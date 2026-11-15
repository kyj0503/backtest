use backtest_server::{
    engine, metrics,
    model::{BacktestRequest, Bar, Histories, History},
};
use chrono::{Duration, NaiveDate};
use serde_json::{Value, json};
use tokio_util::sync::CancellationToken;

fn history(prices: &[f64], opens: Option<&[f64]>, symbol: &str) -> History {
    let start = NaiveDate::from_ymd_opt(2023, 1, 2).unwrap();
    History {
        symbol: symbol.into(),
        currency: "USD".into(),
        company_name: symbol.into(),
        exchange: "test".into(),
        first_trade_date: None,
        bars: prices
            .iter()
            .enumerate()
            .map(|(i, p)| {
                let open = opens.map_or(*p, |v| v[i]);
                Bar {
                    date: start + Duration::days(i as i64),
                    open,
                    close: *p,
                    high: p.max(open),
                    low: p.min(open),
                    volume: 1e6,
                }
            })
            .collect(),
    }
}
fn request(extra: Value, n: usize) -> BacktestRequest {
    let mut r = json!({"portfolio":[{"symbol":"TEST","amount":10000}],"start_date":"2023-01-02","end_date":(NaiveDate::from_ymd_opt(2023,1,2).unwrap()+Duration::days(n as i64-1)),"commission":0,"rebalance_frequency":"none"});
    for (k, v) in extra.as_object().unwrap() {
        r[k] = v.clone();
    }
    serde_json::from_value(r).unwrap()
}
fn run(r: &BacktestRequest, histories: Vec<History>) -> Value {
    let data: Histories = histories
        .into_iter()
        .map(|h| (h.symbol.clone(), h))
        .collect();
    engine::run(r, &data, &CancellationToken::new()).unwrap()["data"].clone()
}
fn near(a: f64, b: f64) {
    assert!((a - b).abs() < 1e-7, "{a} != {b}");
}

#[test]
fn final_signal_cannot_trade_in_the_past() {
    let mut p: Vec<_> = (0..39).map(|i| 100.0 - i as f64 * 0.2).collect();
    p.push(200.0);
    let mut o = p.clone();
    o[39] = 100.0;
    let r = request(
        json!({"strategy":"ema_strategy","strategy_params":{"fast_window":5,"slow_window":10}}),
        40,
    );
    let d = run(&r, vec![history(&p, Some(&o), "TEST")]);
    near(
        d["portfolio_statistics"]["Final_Value"].as_f64().unwrap(),
        10000.0,
    );
    assert_eq!(d["strategy_details"]["TEST"]["trade_log"], json!([]));
    p.push(200.0);
    o.push(200.0);
    let mut longer = r;
    longer.end_date += Duration::days(1);
    let extended = run(&longer, vec![history(&p, Some(&o), "TEST")]);
    assert_eq!(
        d["equity_curve"]["2023-02-10"],
        extended["equity_curve"]["2023-02-10"]
    );
}
#[test]
fn both_sides_pay_commission_and_open_positions_are_marked() {
    let p: Vec<_> = (0..40)
        .map(|i| {
            if i < 4 {
                100.0
            } else if (14..24).contains(&i) {
                110.0
            } else {
                90.0
            }
        })
        .collect();
    let r = request(
        json!({"strategy":"ema_strategy","strategy_params":{"fast_window":5,"slow_window":10},"commission":0.01}),
        40,
    );
    let d = run(&r, vec![history(&p, Some(&[100.0; 40]), "TEST")]);
    let t = &d["strategy_details"]["TEST"]["trade_log"][0];
    let q = t["Size"].as_f64().unwrap();
    near(t["Commission"].as_f64().unwrap(), q * 2.0);
    near(t["PnL"].as_f64().unwrap(), -q * 2.0);
    near(
        d["portfolio_statistics"]["Final_Value"].as_f64().unwrap(),
        10000.0 - q * 2.0,
    );
    let hold = run(
        &request(json!({"commission":0.01}), 40),
        vec![history(&[100.0; 40], None, "TEST")],
    );
    near(
        hold["portfolio_statistics"]["Final_Value"]
            .as_f64()
            .unwrap(),
        10000.0 / 1.01,
    );
}
#[test]
fn cash_deposits_and_budget_remainder_are_conserved() {
    let r = request(
        json!({"portfolio":[{"symbol":"RESERVE","amount":500,"asset_type":"cash","investment_type":"dca","dca_frequency":"weekly_1"}]}),
        40,
    );
    let d = run(&r, vec![]);
    near(d["equity_curve"]["2023-01-02"].as_f64().unwrap(), 500.0);
    near(
        d["portfolio_statistics"]["Final_Value"].as_f64().unwrap(),
        3000.0,
    );
    let r = request(
        json!({"portfolio":[{"symbol":"TEST","amount":333.33,"total_amount":1000,"investment_type":"dca","dca_frequency":"monthly_1"}]}),
        70,
    );
    let d = run(&r, vec![history(&[100.0; 70], None, "TEST")]);
    near(
        d["portfolio_statistics"]["Initial_Value"].as_f64().unwrap(),
        1000.0,
    );
    near(
        d["portfolio_statistics"]["Final_Value"].as_f64().unwrap(),
        1000.0,
    );
    let last = d["strategy_details"]["TEST"]["trade_log"]
        .as_array()
        .unwrap()
        .last()
        .unwrap();
    near(last["Size"].as_f64().unwrap() * 100.0, 333.34);
}
#[test]
fn rebalance_uses_actual_turnover_and_one_ledger() {
    let r = request(
        json!({"portfolio":[{"symbol":"TEST","amount":1000},{"symbol":"RESERVE","amount":1000,"asset_type":"cash"}],"commission":0.01,"rebalance_frequency":"weekly_1"}),
        40,
    );
    let p: Vec<_> = (0..40).map(|i| if i < 7 { 100.0 } else { 200.0 }).collect();
    let d = run(&r, vec![history(&p, None, "TEST")]);
    let rb = &d["rebalance_history"][0];
    let event = rb["trades"]
        .as_array()
        .unwrap()
        .iter()
        .find(|t| t["symbol"] == "TEST")
        .unwrap();
    let trade = d["strategy_details"]["TEST"]["trade_log"]
        .as_array()
        .unwrap()
        .iter()
        .find(|t| t["Type"] == "SELL")
        .unwrap();
    near(
        event["shares"].as_f64().unwrap(),
        trade["Size"].as_f64().unwrap(),
    );
    near(
        rb["commission_cost"].as_f64().unwrap(),
        trade["Size"].as_f64().unwrap() * 200.0 * 0.01,
    );
    let initial_stock = 1000.0 / 1.01 * 2.0;
    near(
        d["equity_curve"]["2023-01-09"].as_f64().unwrap(),
        2.0 * (initial_stock + 1000.0 - 0.01 * initial_stock) / 1.99,
    );
}
#[test]
fn cash_identifier_cannot_overwrite_a_stock() {
    let mut p = vec![100.0; 40];
    p[39] = 200.0;
    let d = run(
        &request(
            json!({"portfolio":[{"symbol":"RESERVE","amount":1000,"asset_type":"cash"},{"symbol":"CASH","amount":2000}]}),
            40,
        ),
        vec![history(&p, None, "CASH")],
    );
    near(
        d["individual_returns"]["CASH"]["final_value"]
            .as_f64()
            .unwrap(),
        4000.0,
    );
    near(
        d["individual_returns"]["RESERVE__cash_1"]["final_value"]
            .as_f64()
            .unwrap(),
        1000.0,
    );
    assert_eq!(d["individual_results"].as_array().unwrap().len(), 2);
}
#[test]
fn wilder_seed_and_flat_price_returns_are_neutral() {
    let mut p = vec![100.0; 40];
    p[1] = 101.0;
    let d = run(
        &request(
            json!({"strategy":"rsi_strategy","strategy_params":{"rsi_period":2,"rsi_oversold":40,"rsi_overbought":70}}),
            40,
        ),
        vec![history(&p, None, "TEST")],
    );
    assert_eq!(d["strategy_details"]["TEST"]["trade_log"], json!([]));
    assert_eq!(d["strategy_details"]["TEST"]["open_positions"], json!([]));
    let d = run(
        &request(
            json!({"portfolio":[{"symbol":"TEST","amount":999.99,"investment_type":"dca","dca_frequency":"weekly_1"}]}),
            100,
        ),
        vec![history(&[7.0; 100], None, "TEST")],
    );
    assert_eq!(d["portfolio_statistics"]["Positive_Days"], 0);
    assert_eq!(d["portfolio_statistics"]["Negative_Days"], 0);
    assert!(d["portfolio_statistics"]["Profit_Factor"].is_null());
}
#[test]
fn daily_calendar_risk_and_cashflow_neutral_benchmark_basis() {
    near(
        metrics::sharpe(&[0.01, -0.01, 0.02]),
        metrics::mean(&[0.01, -0.01, 0.02]) / metrics::stddev(&[0.01, -0.01, 0.02])
            * 365.0_f64.sqrt(),
    );
    let p: Vec<_> = (0..40)
        .map(|i| if i < 35 { 100.0 } else { 200.0 })
        .collect();
    let d = run(
        &request(
            json!({"portfolio":[{"symbol":"TEST","amount":1000,"investment_type":"dca","dca_frequency":"monthly_1"}]}),
            40,
        ),
        vec![history(&p, None, "TEST")],
    );
    near(
        d["portfolio_statistics"]["Total_Return"].as_f64().unwrap(),
        50.0,
    );
    near(
        d["portfolio_statistics"]["Time_Weighted_Return"]
            .as_f64()
            .unwrap(),
        100.0,
    );
}
#[test]
fn overflow_is_rejected_before_financial_serialization() {
    let mut r = request(
        json!({"portfolio":[{"symbol":"A","amount":1e308},{"symbol":"B","amount":1e308}]}),
        40,
    );
    assert_eq!(r.validate(30).unwrap_err().0, 422);
}
