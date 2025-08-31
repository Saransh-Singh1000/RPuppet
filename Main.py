





import time
from RPuppet import RPuppet







RP = RPuppet()

# Rust code
rust_code = """
fn main() {
    println!("Hello from Rust via RPuppet!");
}
"""


# Ruby code
ruby_code = """
puts "Hello from Ruby via RPuppet!"
"""
for i in range(10):
    RP.Rust(rust_code)   # <-- call the method directly
    RP.Ruby(ruby_code)   # <-- call the method directly








