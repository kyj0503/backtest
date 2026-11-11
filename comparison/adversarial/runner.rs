//! Independent audit adapter. No Python output or parity fixture is consumed.
use backtest_server::{engine, model::{BacktestRequest, Histories}};
use serde_json::{json, Value};
use tokio_util::sync::CancellationToken;

fn main() {
    let directory = std::env::args().nth(1).expect("report directory");
    let cases: Vec<Value> = serde_json::from_slice(&std::fs::read(format!("{directory}/cases.json")).unwrap()).unwrap();
    let mut outputs = Vec::new();
    for case in cases {
        let output = std::panic::catch_unwind(|| {
            let mut request: BacktestRequest = serde_json::from_value(case["request"].clone()).unwrap();
            let histories: Histories = serde_json::from_value(case["histories"].clone()).unwrap();
            match request.validate(30).and_then(|_| engine::run(&request, &histories, &CancellationToken::new())) {
                Ok(value) => value,
                Err(error) => json!({"error_code":error.0,"error":error.1}),
            }
        }).unwrap_or_else(|_| json!({"panic":true}));
        outputs.push(json!({"name":case["name"],"output":output}));
    }
    std::fs::write(format!("{directory}/engine-results.json"), serde_json::to_vec(&outputs).unwrap()).unwrap();
    println!("Independent audit engine cases: {}", outputs.len());
}
