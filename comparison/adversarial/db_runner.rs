use backtest_server::{data::DataSource, engine, model::{BacktestRequest, Histories}};
use serde_json::{json, Value};
use tokio_util::sync::CancellationToken;

#[tokio::main]
async fn main() {
    assert_eq!(std::env::var("AUDIT_DISPOSABLE_DATABASE").as_deref(), Ok("true"));
    let source=DataSource::new().unwrap();
    let mut results=Vec::new();
    for symbol in ["ZZTINY", "ZZSPLIT"] {
        let mut request: BacktestRequest=serde_json::from_value(json!({
            "portfolio":[{"symbol":symbol,"amount":10000}],"start_date":"2023-01-02",
            "end_date":"2023-02-10","commission":0,"rebalance_frequency":"none"
        })).unwrap();
        request.validate(30).unwrap();
        let history=source.history(symbol,request.start_date,request.end_date).await.unwrap();
        let mut data=Histories::new();
        data.insert(symbol.into(),history.clone());
        let result=match engine::run(&request,&data,&CancellationToken::new()) {
            Ok(value)=>value,
            Err(error)=>json!({"error_code":error.0,"error":error.1}),
        };
        results.push(json!({"symbol":symbol,"cached_history":history,"output":result}));
    }
    let output=std::env::args().nth(1).unwrap();
    std::fs::write(output,serde_json::to_string_pretty(&Value::Array(results)).unwrap()).unwrap();
    println!("Disposable MySQL precision/cache probes completed: 2");
}
