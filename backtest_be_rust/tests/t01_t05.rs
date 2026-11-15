//! T01/T02 provider regressions live in yahoo_regression_tests; T04 uses real MySQL.
use backtest_server::{
    engine,
    model::{BacktestRequest, Bar, Histories, History},
};
use chrono::{Duration, NaiveDate};
use serde_json::{Value, json};
use tokio_util::sync::CancellationToken;

fn first() -> NaiveDate {
    NaiveDate::from_ymd_opt(2023, 1, 2).unwrap()
}
fn input() -> BacktestRequest {
    serde_json::from_value(json!({"portfolio":[{"symbol":"TEST","amount":10000}],"start_date":first(),"end_date":first()+Duration::days(39),"commission":0,"rebalance_frequency":"none"})).unwrap()
}
fn history() -> History {
    History {
        symbol: "TEST".into(),
        currency: "USD".into(),
        company_name: "test".into(),
        exchange: "synthetic".into(),
        first_trade_date: None,
        bars: (0..40)
            .map(|i| Bar {
                date: first() + Duration::days(i),
                open: 100.,
                high: 100.,
                low: 100.,
                close: 100.,
                volume: 1000.,
            })
            .collect(),
    }
}
fn calculate(req: &BacktestRequest, h: History) -> Value {
    engine::run(
        req,
        &Histories::from([("TEST".into(), h)]),
        &CancellationToken::new(),
    )
    .unwrap()["data"]
        .clone()
}
#[test]
fn t03_first_complete_bollinger_window_signals_and_fills_on_next_open() {
    for period in [5, 20] {
        for fee in [0., 0.01] {
            for delay in [0, 1] {
                let signal = period - 1 + delay;
                let mut h = history();
                h.bars[signal].open = 80.;
                h.bars[signal].close = 80.;
                h.bars[signal].low = 80.;
                h.bars[signal + 1].open = 80.;
                h.bars[signal + 1].low = 80.;
                let mut req = input();
                req.strategy = "bollinger_strategy".into();
                req.commission = fee;
                req.strategy_params =
                    serde_json::from_value(json!({"period":period,"std_dev":1})).unwrap();
                let d = calculate(&req, h);
                let q = 9500. / (80. * (1. + fee));
                let expected = 10000. - q * 80. * (1. + fee) + q * 100. * (1. - fee);
                assert!(
                    (d["portfolio_statistics"]["Final_Value"].as_f64().unwrap() - expected).abs()
                        < 1e-7
                );
                let t = &d["strategy_details"]["TEST"]["trade_log"][0];
                assert_eq!(
                    t["EntryTime"],
                    format!("{}T00:00:00", first() + Duration::days((signal + 1) as i64))
                );
                assert_eq!(
                    t["ExitTime"],
                    format!("{}T00:00:00", first() + Duration::days((signal + 2) as i64))
                );
                assert_eq!(t["EntryPrice"], 80.);
                assert_eq!(t["ExitPrice"], 100.);
            }
        }
    }
}
#[test]
fn t03_incomplete_bollinger_window_cannot_trade() {
    let mut req = input();
    req.strategy = "bollinger_strategy".into();
    req.strategy_params = serde_json::from_value(json!({"period":100,"std_dev":1})).unwrap();
    let d = calculate(&req, history());
    assert_eq!(d["portfolio_statistics"]["Final_Value"], 10000.);
    assert!(
        d["strategy_details"]["TEST"]["trade_log"]
            .as_array()
            .unwrap()
            .is_empty()
    );
}
#[test]
fn t02_engine_rejects_impossible_fills_even_without_provider_adapter() {
    for (open, high, low, close) in [
        (1., 100., 80., 100.),
        (100., 100., 100., 0.),
        (100., 90., 80., 100.),
        (100., 120., 110., 100.),
    ] {
        let mut h = history();
        h.bars[20].open = open;
        h.bars[20].high = high;
        h.bars[20].low = low;
        h.bars[20].close = close;
        let err = engine::run(
            &input(),
            &Histories::from([("TEST".into(), h)]),
            &CancellationToken::new(),
        )
        .unwrap_err();
        assert_eq!(err.0, 422);
    }
}

#[test]
fn t02_daily_fx_point_rate_is_not_an_executable_ohlc_bar() {
    let mut stock = history();
    stock.currency = "KRW".into();
    let mut fx = history();
    fx.symbol = "KRW=X".into();
    // Captured Yahoo FX data can report the daily point outside the intraday
    // range. Only close is used in conversion; no fill may use this bad OHLC.
    for b in &mut fx.bars {
        b.open = 1000.;
        b.close = 1000.;
        b.high = 1010.;
        b.low = 1005.;
    }
    let mut data = Histories::from([("TEST".into(), stock), ("KRW=X".into(), fx)]);
    let d = engine::run(&input(), &data, &CancellationToken::new()).unwrap();
    assert_eq!(d["data"]["portfolio_statistics"]["Final_Value"], 10000.);
    let mut traded = input();
    traded.portfolio[0].symbol = "KRW=X".into();
    assert_eq!(
        engine::run(&traded, &data, &CancellationToken::new())
            .unwrap_err()
            .0,
        422
    );
    data.get_mut("KRW=X").unwrap().bars[0].close = 0.;
    assert_eq!(
        engine::run(&input(), &data, &CancellationToken::new())
            .unwrap_err()
            .0,
        422
    );
}
