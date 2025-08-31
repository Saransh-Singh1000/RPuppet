








import subprocess
import tempfile
import os
import hashlib
import sqlite3
import platform
import time

class RPuppet:
    def __init__(self,
                 mingw_path=r"C:\mingw64\mingw64\bin",
                 ruby_path=r"C:\Ruby34-x64\bin\ruby.exe"):
        self.mingw_path = mingw_path
        self.ruby_path = ruby_path
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

        # Assign language methods
        self.Rust = self._run_rust
        self.Ruby = self._run_ruby

        # Rust target config
        self.rust_target = "x86_64-pc-windows-gnu"
        self._create_cargo_config()

    # Create a temporary cargo config to set MinGW linker
    def _create_cargo_config(self):
        cargo_dir = os.path.join(tempfile.gettempdir(), "rpup_config")
        os.makedirs(cargo_dir, exist_ok=True)
        config_path = os.path.join(cargo_dir, "config.toml")
        linker_path = os.path.join(self.mingw_path, "gcc.exe").replace("\\", "/")
        with open(config_path, "w") as f:
            f.write(f"[target.{self.rust_target}]\nlinker = \"{linker_path}\"\n")
        os.environ["CARGO_HOME"] = cargo_dir  # Temporary CARGO_HOME

    # Hashing function
    def _hash_code(self, code: str):
        return hashlib.sha256(code.encode()).hexdigest()

    # Cache checking
    def _check_cache(self, code_hash: str):
        self.cursor.execute("SELECT output FROM cache WHERE hash=?", (code_hash,))
        row = self.cursor.fetchone()
        return row[0] if row else None

    # Cache saving
    def _cache_output(self, code_hash: str, output: str):
        self.cursor.execute(
            "INSERT OR REPLACE INTO cache(hash, output) VALUES (?, ?)",
            (code_hash, output)
        )
        self.conn.commit()

    # Run Rust code
    def _run_rust(self, code: str):
        start_time = time.time()
        code_hash = self._hash_code(code)

        cached = self._check_cache(code_hash)
        if cached:
            print(f"[Rust JIT] Returning cached output in {time.time() - start_time:.6f}s")
            print(cached, end="")
            return

        # Write temp Rust file
        with tempfile.NamedTemporaryFile(delete=False, suffix=".rs") as tmp_rs:
            tmp_rs.write(code.encode())
            tmp_rs_path = tmp_rs.name
        tmp_bin_path = tmp_rs_path.replace(".rs", self.exe_ext)

        compile_cmd = [
            "rustc",
            f"--target={self.rust_target}",
            tmp_rs_path,
            "-o", tmp_bin_path,
            "-C", "opt-level=0",
            "-C", "debuginfo=0",
            "-C", "codegen-units=16"
        ]

        try:
            # Compile Rust
            result = subprocess.run(compile_cmd, capture_output=True, text=True)
            if result.returncode != 0:
                print("[Rust Compilation Error]:\n", result.stderr)
                return

            # Execute
            run_result = subprocess.run([tmp_bin_path], capture_output=True, text=True)
            if run_result.returncode != 0:
                print("[Rust Runtime Error]:\n", run_result.stderr)
                return

            output = run_result.stdout
            print(output, end="")

            # Cache output
            self._cache_output(code_hash, output)

            print(f"[First Rust Run] {time.time() - start_time:.6f}s")

        finally:
            if os.path.exists(tmp_rs_path):
                os.remove(tmp_rs_path)
            if os.path.exists(tmp_bin_path):
                os.remove(tmp_bin_path)

    # Run Ruby code
    def _run_ruby(self, code: str):
        start_time = time.time()
        code_hash = self._hash_code(code)

        cached = self._check_cache(code_hash)
        if cached:
            print(f"[Ruby JIT] Returning cached output in {time.time() - start_time:.6f}s")
            print(cached, end="")
            return

        with tempfile.NamedTemporaryFile(delete=False, suffix=".rb") as tmp_rb:
            tmp_rb.write(code.encode())
            tmp_rb_path = tmp_rb.name

        try:
            result = subprocess.run(
                [self.ruby_path, tmp_rb_path],
                capture_output=True,
                text=True
            )
            if result.returncode != 0:
                print("[Ruby Runtime Error]:\n", result.stderr)
                return

            output = result.stdout
            print(output, end="")

            self._cache_output(code_hash, output)
            print(f"[First Ruby Run] {time.time() - start_time:.6f}s")

        finally:
            if os.path.exists(tmp_rb_path):
                os.remove(tmp_rb_path)

    # Close cache
    def Close(self):
        self.conn.close()
        if os.path.exists(self.db_path):
            os.remove(self.db_path)


# === Example usage ===
if __name__ == "__main__":
    RP = RPuppet()

    rust_code = """
fn main() {
    println!("Hello from Rust via RPuppet!");
}
"""
    ruby_code = """
puts 'Hello from Ruby via RPuppet!'
"""

    print("=== Rust Test ===")
    RP.Rust(rust_code)
    print("\n=== Ruby Test ===")
    RP.Ruby(ruby_code)

    # Test JIT caching
    print("\n=== Rust Cached ===")
    RP.Rust(rust_code)
    print("\n=== Ruby Cached ===")
    RP.Ruby(ruby_code)

    RP.Close()
