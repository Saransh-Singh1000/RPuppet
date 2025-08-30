

# Main.py
from RPuppet import RPuppet
import time

# Initialize RPuppet (adjust evcxr path if needed)
# rp = RPuppet(evcxr_path=r"C:\Users\sharm\.cargo\bin\evcxr.exe")
rp = RPuppet()  # default assumes evcxr is in PATH

# Corrected Rust snippets (wrapped in fn main)
rust_snippets = [
    ( "First snippet",
    """
fn main() {
    println!("Hello from RPuppet!");
    let a = 10;
    let b = 32;
    println!("10 + 32 = {}", a + b);
}
"""
    ),
    ( "Second snippet",
    """
fn factorial(n: u64) -> u64 {
    if n <= 1 { 1 } else { n * factorial(n - 1) }
}
fn main() {
    println!("5! = {}", factorial(5));
}
"""
    ),
    ( "Third snippet",
    """
fn main() {
    let mut sum = 0;
    for i in 1..=1000 { sum += i; }
    println!("Sum 1..1000 = {}", sum);
}
"""
    )
]

# Run each snippet twice to demonstrate JIT caching
for title, code in rust_snippets:
    print(f"\n=== {title} ===")
    rp.Run(code)  # First run (JIT compilation)
    rp.Run(code)  # Second run (hotspot cache)

# Close RPuppet
rp.Close()
