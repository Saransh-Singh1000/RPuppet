

import subprocess
import tempfile
import os
import hashlib
import sqlite3
import platform
import time

class RPuppet:
    def __init__(self, mingw_path=r"C:\mingw64\mingw64\bin"):
        self.mingw_path = mingw_path
        self.exe_ext = ".exe" if platform.system() == "Windows" else ""

        # Ensure MinGW is in PATH
        os.environ["PATH"] = self.mingw_path + os.pathsep + os.environ.get("PATH", "")

        # Create a temporary SQLite cache file
        self.db_file = tempfile.NamedTemporaryFile(delete=False, suffix=".db")
        self.db_path = self.db_file.name
        self.db_file.close()  # Close handle to avoid Windows lock

        # Setup SQLite cache
        self.conn = sqlite3.connect(self.db_path)
        self.cursor = self.conn.cursor()
        self.cursor.execute(
            "CREATE TABLE IF NOT EXISTS cache(hash TEXT PRIMARY KEY, output TEXT)"
        )
        self.conn.commit()

    def Run(self, code: str):
        start_time = time.time()
        code_hash = hashlib.sha256(code.encode()).hexdigest()

        # Check cache
        self.cursor.execute("SELECT output FROM cache WHERE hash=?", (code_hash,))
        row = self.cursor.fetchone()
        if row:
            elapsed = time.time() - start_time
            print(f"[JIT] Returning cached output in {elapsed:.6f} seconds")
            print(row[0], end="")
            return

        # Compile and execute
        with tempfile.NamedTemporaryFile(delete=False, suffix=".rs") as tmp_rs:
            tmp_rs.write(code.encode())
            tmp_rs_path = tmp_rs.name

        tmp_bin_path = tmp_rs_path.replace(".rs", self.exe_ext)

        compile_cmd = [
            "rustc",
            "--target=x86_64-pc-windows-gnu",
            tmp_rs_path,
            "-o",
            tmp_bin_path,
            "-C","opt-level=0",       # Disable optimizations for ultra-fast compilation
            "-C", "debuginfo=0",   # No debug info
            "-C", "codegen-units=1" # Minimal codegen units
        ]

        try:
            result = subprocess.run(compile_cmd, capture_output=True, text=True)
            if result.returncode != 0:
                print("[Compilation Error]:\n", result.stderr)
                return

            run_result = subprocess.run([tmp_bin_path], capture_output=True, text=True)
            if run_result.returncode != 0:
                print("[Runtime Error]:\n", run_result.stderr)
                return

            output = run_result.stdout
            print(output, end="")

            # Cache the output
            self.cursor.execute(
                "INSERT OR REPLACE INTO cache(hash, output) VALUES (?, ?)",
                (code_hash, output)
            )
            self.conn.commit()

            elapsed = time.time() - start_time
            print(f"[First Run] Compiled and executed in {elapsed:.6f} seconds")

        finally:
            if os.path.exists(tmp_rs_path):
                os.remove(tmp_rs_path)
            if os.path.exists(tmp_bin_path):
                os.remove(tmp_bin_path)

    def Close(self):
        self.conn.close()
        if os.path.exists(self.db_path):
            os.remove(self.db_path)


