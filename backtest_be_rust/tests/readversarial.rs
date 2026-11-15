//! Independent regressions from the second adversarial review. The fixture
//! contains synthetic inputs only; expectations come from cash/share ledgers.
use backtest_server::{
    engine,
    model::{BacktestRequest, Histories},
};
use chrono::NaiveDate;
use serde_json::{Value, json};
use tokio_util::sync::CancellationToken;

fn case(name: &str) -> (BacktestRequest, Histories) {
    let cases: Vec<Value> =
        serde_json::from_str(include_str!("fixtures/readversarial.json")).unwrap();
    let c = cases.iter().find(|c| c["name"] == name).unwrap();
    (
        serde_json::from_value(c["request"].clone()).unwrap(),
        serde_json::from_value(c["histories"].clone()).unwrap(),
    )
}
fn calculate(r: &BacktestRequest, h: &Histories) -> Value {
    engine::run(r, h, &CancellationToken::new()).unwrap()["data"].clone()
}
fn run(name: &str) -> Value {
    let (r, h) = case(name);
    calculate(&r, &h)
}
fn near(v: &Value, expected: f64) {
    let actual = v.as_f64().unwrap();
    assert!(
        (actual - expected).abs() <= 1e-7_f64.max(expected.abs() * 1e-12),
        "{actual} != {expected}"
    );
}

#[test]
fn r01_sunday_schedule_executes_on_next_common_trading_day() {
    let d = run("sunday_rebalance_weekly_1");
    let dates: Vec<_> = d["rebalance_history"]
        .as_array()
        .unwrap()
        .iter()
        .map(|r| r["date"].as_str().unwrap())
        .collect();
    assert_eq!(
        dates,
        vec![
            "2023-01-09",
            "2023-01-16",
            "2023-01-23",
            "2023-01-30",
            "2023-02-06"
        ]
    );
    // Fee-free 50:50 ledger, independently calculated at those five closes.
    near(&d["portfolio_statistics"]["Final_Value"], 17356.30580357143);
    assert_ne!(
        d["portfolio_statistics"]["Final_Value"],
        run("sunday_rebalance_none")["portfolio_statistics"]["Final_Value"]
    );
}
#[test]
fn r01_different_market_holidays_do_not_rebalance_only_a_subset() {
    let (r, mut h) = case("one_market_holiday_True");
    h.get_mut("B")
        .unwrap()
        .bars
        .retain(|b| b.date != NaiveDate::from_ymd_opt(2023, 1, 10).unwrap());
    let d = calculate(&r, &h);
    assert_eq!(d["rebalance_history"][0]["date"], "2023-01-11");
    near(&d["rebalance_history"][0]["weights_after"]["A"], 0.5);
    near(&d["rebalance_history"][0]["weights_after"]["B"], 0.5);
}
#[test]
fn r02_closed_market_foreign_holdings_revalue_at_calendar_fx() {
    let d = run("fx_open_position_2000");
    // Fractional adjusted units: 95% budget / signal USD price (98/1000).
    let units = 9500.0 / (98.0 / 1000.0);
    let cash = 10000.0 - units * 97.0 / 1000.0;
    near(
        &d["portfolio_statistics"]["Final_Value"],
        cash + units * 97.0 / 2000.0,
    );
    near(
        &d["daily_returns"]["2023-02-10"],
        (cash + units * 97.0 / 2000.0 - 10000.0) / 100.0,
    );
    let detail = &d["strategy_details"]["TEST"];
    near(
        &detail["open_positions"][0]["MarketValue"],
        units * 97.0 / 2000.0,
    );
    near(&detail["cash"], cash);
    assert_eq!(
        detail["final_equity"],
        d["individual_returns"]["TEST"]["final_value"]
    );
    assert_eq!(
        detail["final_equity"],
        d["portfolio_statistics"]["Final_Value"]
    );
    near(
        &detail["annualized_return_pct"],
        d["portfolio_statistics"]["Annual_Return"].as_f64().unwrap(),
    );
    near(
        &run("fx_open_position_1000")["portfolio_statistics"]["Final_Value"],
        10000.0,
    );
    near(
        &run("fx_buyhold_control_2000")["portfolio_statistics"]["Final_Value"],
        4850.0,
    );
}
#[test]
fn r05_profit_factor_uses_net_realized_dollars_at_every_level() {
    let d = run("profit_factor");
    let t = &d["strategy_details"]["TEST"]["trade_log"];
    let gain = (9500.0 / 80.0) * (110.0 - 80.0);
    let loss = ((10000.0 + gain) * 0.95 / 70.0) * (70.0 - 50.0);
    near(&t[0]["PnL"], gain);
    near(&t[1]["PnL"], -loss);
    near(
        &d["portfolio_statistics"]["Final_Value"],
        10000.0 + gain - loss,
    );
    near(&d["portfolio_statistics"]["Profit_Factor"], gain / loss);
    near(&d["strategy_details"]["TEST"]["profit_factor"], gain / loss);
    assert!(run("sunday_rebalance_weekly_1")["portfolio_statistics"]["Profit_Factor"].is_null());
    let (mut r, mut h) = case("profit_factor");
    r.portfolio.push(r.portfolio[0].clone());
    r.portfolio[1].symbol = "OTHER".into();
    r.portfolio[1].amount = Some(20000.0);
    let mut other = h["TEST"].clone();
    other.symbol = "OTHER".into();
    h.insert("OTHER".into(), other);
    r.commission = 0.01;
    let d = calculate(&r, &h);
    let pnl: Vec<f64> = d["strategy_details"]
        .as_object()
        .unwrap()
        .values()
        .flat_map(|s| s["trade_log"].as_array().unwrap())
        .map(|t| t["PnL"].as_f64().unwrap())
        .collect();
    let gains: f64 = pnl.iter().filter(|p| **p > 0.0).sum();
    let losses: f64 = -pnl.iter().filter(|p| **p < 0.0).sum::<f64>();
    near(&d["portfolio_statistics"]["Profit_Factor"], gains / losses);
}
#[test]
fn r06_r11_asset_ids_join_all_outputs_without_reserved_key_collisions() {
    for strategy in ["buy_hold_strategy", "rsi_strategy"] {
        let (mut r, h) = case("cash_date_key");
        r.strategy = strategy.into();
        r.portfolio.push(r.portfolio[0].clone()); // two independently allocated cash buckets named date
        r.portfolio.push(
            serde_json::from_value(json!({"symbol":"CASH","asset_type":"cash","amount":1000}))
                .unwrap(),
        );
        let d = calculate(&r, &h);
        let composition = d["portfolio_composition"].as_array().unwrap();
        assert_eq!(composition.len(), 4);
        assert_eq!(d["individual_returns"].as_object().unwrap().len(), 4);
        for point in d["weight_history"].as_array().unwrap() {
            assert!(point["date"].as_str().is_some());
            let sum: f64 = composition
                .iter()
                .map(|a| point[a["asset_id"].as_str().unwrap()].as_f64().unwrap())
                .sum();
            near(&json!(sum), 1.0);
        }
        for a in composition {
            let id = a["asset_id"].as_str().unwrap();
            assert_eq!(d["individual_returns"][id]["asset_id"], a["asset_id"]);
            assert_eq!(d["individual_returns"][id]["symbol"], a["symbol"]);
            assert!(
                d["individual_results"]
                    .as_array()
                    .unwrap()
                    .iter()
                    .any(|v| v["asset_id"] == id)
            );
        }
    }
    let d = run("cash_weight_chart");
    near(&d["weight_history"][0]["CASH__cash_1"], 0.5);
    assert_eq!(d["portfolio_composition"][0]["asset_id"], "CASH__cash_1");
}
#[test]
fn r07_open_position_preserves_actual_entry_and_does_not_invent_exit() {
    let d = run("open_position");
    let s = &d["strategy_details"]["TEST"];
    assert_eq!(s["trade_log"], json!([]));
    assert_eq!(s["open_positions"].as_array().unwrap().len(), 1);
    assert_eq!(s["open_positions"][0]["EntryTime"], "2023-01-05");
    near(&s["open_positions"][0]["Size"], 9500.0 / 98.0);
    near(&s["cash"], 10000.0 - 9500.0 / 98.0 * 97.0);
    near(&s["open_positions"][0]["MarketValue"], 9500.0 / 98.0 * 97.0);
}
#[test]
fn r09_dca_validation_uses_real_schedule_instead_of_thirty_day_months() {
    let (mut r, h) = case("monthly_2_calendar");
    r.validate(30).unwrap();
    let d = calculate(&r, &h);
    near(&d["portfolio_statistics"]["Initial_Value"], 20000.0);
    let dates: Vec<_> = d["strategy_details"]["TEST"]["trade_log"]
        .as_array()
        .unwrap()
        .iter()
        .map(|t| t["EntryTime"].as_str().unwrap())
        .collect();
    assert_eq!(dates, vec!["2023-01-30T00:00:00", "2023-03-27T00:00:00"]);
    r.end_date = NaiveDate::from_ymd_opt(2023, 3, 26).unwrap();
    assert_eq!(r.validate(30).unwrap_err().0, 422);
}
#[test]
fn r10_finite_overflow_returns_validation_error_instead_of_panicking() {
    let (r, h) = case("finite_annual_overflow");
    assert_eq!(
        engine::run(&r, &h, &CancellationToken::new())
            .unwrap_err()
            .0,
        422
    );
    // Full requested valuation period (39 days) has a representable CAGR, even
    // though annualizing only the final three trading days would overflow.
    let d = run("finite_short_listing_overflow");
    near(
        &d["portfolio_statistics"]["Final_Value"],
        10000.0 + (9500.0 / 98.0) * (1000000.0 - 97.0),
    );
    assert!(
        d["portfolio_statistics"]["Annual_Return"]
            .as_f64()
            .unwrap()
            .is_finite()
    );
}
