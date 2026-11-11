// Mounted as a Cargo example solely for the benchmark. The running app is unchanged.
use backtest_server::{engine,model::{BacktestRequest,Histories}};
use serde_json::Value;
use tokio_util::sync::CancellationToken;
fn main() {
    let output = std::env::args().nth(1).unwrap_or_else(|| "/reports/scenarios".into());
    let data: Histories=serde_json::from_str(&std::fs::read_to_string(format!("{output}/prices-python.json")).unwrap()).unwrap();
    let mut cases:Vec<Value>=serde_json::from_str(&std::fs::read_to_string(format!("{output}/replay-python.json")).unwrap()).unwrap();
    for case in &mut cases {
        let mut request:BacktestRequest=serde_json::from_value(case["request"].clone()).unwrap();
        request.validate(30).unwrap();
        let mut filtered=data.clone();
        for history in filtered.values_mut() {
            history.bars.retain(|bar| bar.date<=request.end_date && (history.symbol.ends_with("=X") || bar.date>=request.start_date));
        }
        case["rust"]=engine::run(&request,&filtered,&CancellationToken::new()).unwrap();
    }
    std::fs::write(format!("{output}/replay-both.json"),serde_json::to_string(&cases).unwrap()).unwrap();
    println!("Same-input Rust engine cases: {}", cases.len());
}
