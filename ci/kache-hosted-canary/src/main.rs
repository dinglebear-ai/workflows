fn main() {
    let values = (1_u64..=10_000).map(|value| value * value);
    let checksum: u64 = values.sum();
    println!("kache-hosted-canary:{checksum}");
}
