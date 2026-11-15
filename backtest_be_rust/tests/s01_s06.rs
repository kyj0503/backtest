//! Independent accounting oracles: no Python output is used.
use backtest_server::{
    engine,
    model::{BacktestRequest, Bar, Histories, History},
};
use chrono::{Duration, NaiveDate};
use serde_json::{Value, json};
use tokio_util::sync::CancellationToken;

fn start() -> NaiveDate {
    NaiveDate::from_ymd_opt(2023, 1, 2).unwrap()
}
fn history(symbol: &str, prices: &[f64]) -> History {
    History {
        symbol: symbol.into(),
        currency: "USD".into(),
        company_name: symbol.into(),
        exchange: "synthetic".into(),
        first_trade_date: None,
        bars: prices
            .iter()
            .enumerate()
            .map(|(i, p)| Bar {
                date: start() + Duration::days(i as i64),
                open: *p,
                high: *p,
                low: *p,
                close: *p,
                volume: 1000.0,
            })
            .collect(),
    }
}
fn run(histories: Vec<History>, extra: Value) -> Value {
    let mut request = json!({"portfolio":[{"symbol":"TEST","amount":10000}],"start_date":start(),"end_date":start()+Duration::days(39),"commission":0,"rebalance_frequency":"none"});
    for (k, v) in extra.as_object().unwrap() {
        request[k] = v.clone();
    }
    let req: BacktestRequest = serde_json::from_value(request).unwrap();
    let data: Histories = histories
        .into_iter()
        .map(|h| (h.symbol.clone(), h))
        .collect();
    engine::run(&req, &data, &CancellationToken::new()).unwrap()["data"].clone()
}
fn near(a: f64, b: f64) {
    assert!((a - b).abs() < 1e-7, "{a} != {b}");
}
fn num(v: &Value) -> f64 {
    v.as_f64().unwrap()
}

#[test]
fn s01_fractional_units_are_invariant_and_next_open_ledger_reconciles() {
    for fee in [0.0, 0.01] {
        // Signal close=980, next open=970, following sale open=1500.
        let q = 9500.0 / (980.0 * (1.0 + fee));
        let expected = 10000.0 - q * 970.0 * (1.0 + fee) + q * 1500.0 * (1.0 - fee);
        for scale in [0.01, 0.5, 1.0, 2.0, 100.0] {
            let mut prices = vec![1500.0 * scale; 40];
            prices[..4].copy_from_slice(&[
                1000.0 * scale,
                990.0 * scale,
                980.0 * scale,
                970.0 * scale,
            ]);
            let d = run(
                vec![history("TEST", &prices)],
                json!({"strategy":"rsi_strategy","strategy_params":{"rsi_period":2},"commission":fee}),
            );
            near(num(&d["portfolio_statistics"]["Final_Value"]), expected);
            let t = &d["strategy_details"]["TEST"]["trade_log"][0];
            near(num(&t["Size"]), q / scale);
            near(num(&t["Commission"]), q * (970.0 + 1500.0) * fee);
            assert_eq!(t["EntryTime"], "2023-01-05T00:00:00");
            assert_eq!(t["QuantityUnit"], "fractional_adjusted_unit");
        }
    }
}

#[test]
fn s01_all_technical_strategies_preserve_wealth_under_adjusted_unit_change() {
    let prices: Vec<_> = (0..120)
        .map(|i| 100.0 + 20.0 * ((i as f64) / 7.0).sin() + i as f64 / 10.0)
        .collect();
    for strategy in [
        "sma_strategy",
        "ema_strategy",
        "macd_strategy",
        "rsi_strategy",
        "bollinger_strategy",
    ] {
        let extra =
            json!({"strategy":strategy,"commission":0.01,"end_date":start()+Duration::days(119)});
        let a = run(vec![history("TEST", &prices)], extra.clone());
        let b = run(
            vec![history(
                "TEST",
                &prices.iter().map(|p| p / 2.0).collect::<Vec<_>>(),
            )],
            extra,
        );
        for (day, v) in a["equity_curve"].as_object().unwrap() {
            near(num(v), num(&b["equity_curve"][day]));
        }
        assert_eq!(
            a["strategy_details"]["TEST"]["total_trades"],
            b["strategy_details"]["TEST"]["total_trades"]
        );
    }
}

#[test]
fn s02_first_fee_is_in_public_returns_and_risk_exactly_once() {
    let d = run(
        vec![history("TEST", &[100.0; 40])],
        json!({"commission":0.01}),
    );
    let loss = 1.0 / 1.01 - 1.0;
    near(num(&d["daily_returns"]["2023-01-02"]), loss * 100.0);
    let growth: f64 = d["daily_returns"]
        .as_object()
        .unwrap()
        .values()
        .map(|v| 1.0 + num(v) / 100.0)
        .product();
    near(growth, 1.0 / 1.01);
    let stats = &d["portfolio_statistics"];
    near(num(&stats["Time_Weighted_Return"]), loss * 100.0);
    near(num(&stats["Max_Drawdown"]), loss * 100.0);
    // Sample standard deviation of [loss, 0, ..., 0] is |loss|/sqrt(n).
    near(
        num(&stats["Annual_Volatility"]),
        loss.abs() * (365.0_f64 / 40.0).sqrt() * 100.0,
    );
    assert_eq!(stats["Negative_Days"], 1);
}

#[test]
fn s02_weekend_inflow_then_fee_does_not_double_count_deposit() {
    let d = run(
        vec![history("TEST", &[100.0; 40])],
        json!({"commission":0.01,"start_date":"2023-01-01"}),
    );
    near(num(&d["daily_returns"]["2023-01-01"]), 0.0);
    near(
        num(&d["daily_returns"]["2023-01-02"]),
        (1.0 / 1.01 - 1.0) * 100.0,
    );
    near(
        num(&d["portfolio_statistics"]["Final_Value"]),
        10000.0 / 1.01,
    );
}

#[test]
fn s04_execution_prices_preserve_native_currency_and_execution_day_fx() {
    let mut prices = vec![110000.0; 40];
    prices[..3].copy_from_slice(&[100000.0, 99000.0, 98000.0]);
    let mut stock = history("TEST", &prices);
    stock.currency = "KRW".into();
    stock.bars[3].open = 97000.0;
    stock.bars[3].low = 97000.0;
    let rates: Vec<_> = (0..40).map(|i| 1000.0 + i as f64).collect();
    let d = run(
        vec![stock, history("KRW=X", &rates)],
        json!({"strategy":"rsi_strategy","strategy_params":{"rsi_period":2}}),
    );
    let t = &d["strategy_details"]["TEST"]["trade_log"][0];
    near(num(&t["EntryPriceNative"]), 97000.0);
    near(num(&t["EntryPrice"]), 97000.0 / 1003.0);
    near(num(&t["ExitPriceNative"]), 110000.0);
    assert_eq!(t["NativeCurrency"], "KRW");
    assert_eq!(t["PriceCurrency"], "USD");
}

#[test]
fn s05_waiting_cash_and_late_asset_keep_full_account_weights() {
    let mut late = history("LATE", &[100.0; 40]);
    late.bars.drain(..10);
    let d = run(
        vec![history("TEST", &[100.0; 40]), late],
        json!({"start_date":"2023-01-01","portfolio":[{"symbol":"TEST","amount":5000},{"symbol":"LATE","amount":5000}]}),
    );
    for row in d["weight_history"].as_array().unwrap() {
        near(num(&row["TEST"]), 0.5);
        near(num(&row["LATE"]), 0.5);
        near(
            row.as_object()
                .unwrap()
                .values()
                .filter_map(Value::as_f64)
                .sum(),
            1.0,
        );
    }
    assert_eq!(
        d["calculation_assumptions"]["weight_basis"],
        "asset_account_including_uninvested_cash"
    );
}
