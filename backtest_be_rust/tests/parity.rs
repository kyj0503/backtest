//! Historical input corpus retained; Python numeric outputs are archival only.
//! Financial assertions now check a single reconciled ledger and causal fills.
use backtest_server::{
    engine,
    model::{BacktestRequest, Histories},
};
use serde_json::Value;
use tokio_util::sync::CancellationToken;

fn reconcile(req: &BacktestRequest, result: &Value) {
    let d = &result["data"];
    let total = d["portfolio_statistics"]["Final_Value"].as_f64().unwrap();
    let initial = d["portfolio_statistics"]["Initial_Value"].as_f64().unwrap();
    assert!(total.is_finite() && total >= 0.0 && initial > 0.0);
    let sum: f64 = d["individual_results"]
        .as_array()
        .unwrap()
        .iter()
        .map(|v| v["final_equity"].as_f64().unwrap())
        .sum();
    assert!((total - sum).abs() <= 1e-7 * total.max(1.0));
    assert!(
        (d["portfolio_statistics"]["Total_Return"].as_f64().unwrap()
            - (total / initial - 1.0) * 100.0)
            .abs()
            < 1e-7
    );
    for stats in d["strategy_details"].as_object().unwrap().values() {
        for t in stats["trade_log"].as_array().into_iter().flatten() {
            let size = t["Size"].as_f64().unwrap();
            let entry = t["EntryPrice"].as_f64().unwrap();
            let fee = t["Commission"].as_f64().unwrap();
            let notional = size * (entry + t["ExitPrice"].as_f64().unwrap_or(0.0));
            assert!((fee - notional * req.commission).abs() < 1e-7 * notional.max(1.0));
            if let Some(exit) = t["ExitPrice"].as_f64() {
                assert!(
                    (t["PnL"].as_f64().unwrap() - (size * (exit - entry) - fee)).abs()
                        < 1e-7 * notional.max(1.0)
                );
                assert!(t["ExitBar"].as_u64().unwrap() > t["EntryBar"].as_u64().unwrap());
            }
        }
    }
}

#[test]
fn captured_scenarios_obey_corrected_financial_invariants() {
    let histories: Histories =
        serde_json::from_str(include_str!("fixtures/histories.json")).unwrap();
    let cases: Vec<Value> = serde_json::from_str(include_str!("fixtures/parity.json")).unwrap();
    for case in cases {
        let mut req: BacktestRequest = serde_json::from_value(case["request"].clone()).unwrap();
        req.validate(30).unwrap();
        let result = engine::run(&req, &histories, &CancellationToken::new()).unwrap();
        reconcile(&req, &result);
    }
}
#[test]
fn captured_market_inputs_obey_corrected_financial_invariants() {
    let fixture: Value =
        serde_json::from_str(include_str!("fixtures/real-market-python.json")).unwrap();
    let histories: Histories = serde_json::from_value(fixture["histories"].clone()).unwrap();
    for case in fixture["cases"].as_array().unwrap() {
        let mut req: BacktestRequest = serde_json::from_value(case["request"].clone()).unwrap();
        req.validate(30).unwrap();
        let mut data = histories.clone();
        for h in data.values_mut() {
            h.bars.retain(|b| {
                b.date <= req.end_date && (h.symbol.ends_with("=X") || b.date >= req.start_date)
            });
        }
        let result = engine::run(&req, &data, &CancellationToken::new()).unwrap();
        reconcile(&req, &result);
    }
}
