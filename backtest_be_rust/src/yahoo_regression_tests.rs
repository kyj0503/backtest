use super::*;

fn t_chart() -> Value {
    let dates: Vec<String> = (0..40)
        .map(|i| format!("{}T00:00:00Z", date("2023-01-02") + Duration::days(i)))
        .collect();
    let instants: Vec<&str> = dates.iter().map(String::as_str).collect();
    let mut v = chart("TEST", "UTC", "USD", &instants);
    v["chart"]["result"][0]["indicators"]["adjclose"][0]["adjclose"] = json!(vec![50.; 40]);
    v
}

#[test]
fn t01_missing_stock_adjustments_cannot_manufacture_gain_or_drawdown() {
    let base = t_chart();
    let h = parse("TEST", base.clone()).unwrap();
    assert!(h.bars.iter().all(|b| b.close == 50.));
    let req: BacktestRequest=serde_json::from_value(json!({"portfolio":[{"symbol":"TEST","amount":10000}],"start_date":"2023-01-02","end_date":"2023-02-10","commission":0,"rebalance_frequency":"none"})).unwrap();
    let d = engine::run(
        &req,
        &Histories::from([("TEST".into(), h)]),
        &tokio_util::sync::CancellationToken::new(),
    )
    .unwrap();
    assert_eq!(d["data"]["portfolio_statistics"]["Final_Value"], 10000.);
    assert_eq!(d["data"]["portfolio_statistics"]["Max_Drawdown"], 0.);
    for missing in [0, 20, 39] {
        let mut v = base.clone();
        v["chart"]["result"][0]["indicators"]["adjclose"][0]["adjclose"][missing] = Value::Null;
        assert_eq!(parse("TEST", v).unwrap_err().0, 503);
    }
    let mut v = base;
    v["chart"]["result"][0]["indicators"]["adjclose"] = Value::Null;
    assert_eq!(parse("TEST", v).unwrap_err().0, 503);
}

#[test]
fn t02_invalid_provider_bars_fail_but_wholly_absent_bars_are_skipped() {
    let base = t_chart();
    for (field, bad) in [
        ("open", json!(1.)),
        ("open", json!(1000.)),
        ("close", json!(0.)),
        ("low", json!(-1.)),
        ("high", json!(79.)),
        ("open", Value::Null),
    ] {
        let mut v = base.clone();
        v["chart"]["result"][0]["indicators"]["quote"][0][field][20] = bad;
        assert_eq!(parse("TEST", v).unwrap_err().0, 503, "{field}");
    }
    let mut v = base;
    for field in ["open", "high", "low", "close"] {
        v["chart"]["result"][0]["indicators"]["quote"][0][field][20] = Value::Null;
    }
    v["chart"]["result"][0]["indicators"]["adjclose"][0]["adjclose"][20] = Value::Null;
    let h = parse("TEST", v).unwrap();
    assert_eq!(h.bars.len(), 39);
    assert!(h.bars.iter().all(|b| b.close == 50.));
}

#[test]
fn t02_provider_cannot_fill_below_its_own_low() {
    let mut v = t_chart();
    for field in ["open", "low", "close"] {
        v["chart"]["result"][0]["indicators"]["quote"][0][field][5] = json!(80.);
    }
    v["chart"]["result"][0]["indicators"]["adjclose"][0]["adjclose"][5] = json!(40.);
    v["chart"]["result"][0]["indicators"]["quote"][0]["open"][6] = json!(80.);
    let h = parse("TEST", v.clone()).unwrap();
    let req:BacktestRequest=serde_json::from_value(json!({"portfolio":[{"symbol":"TEST","amount":10000}],"start_date":"2023-01-02","end_date":"2023-02-10","commission":0,"rebalance_frequency":"none","strategy":"bollinger_strategy","strategy_params":{"period":5,"std_dev":1}})).unwrap();
    let d = engine::run(
        &req,
        &Histories::from([("TEST".into(), h)]),
        &tokio_util::sync::CancellationToken::new(),
    )
    .unwrap();
    assert_eq!(d["data"]["portfolio_statistics"]["Final_Value"], 12375.);
    v["chart"]["result"][0]["indicators"]["quote"][0]["open"][6] = json!(1.);
    assert_eq!(parse("TEST", v).unwrap_err().0, 503);
}

fn date(value: &str) -> NaiveDate {
    value.parse().unwrap()
}

fn timestamp(value: &str) -> i64 {
    DateTime::parse_from_rfc3339(value).unwrap().timestamp()
}

fn chart(symbol: &str, zone: &str, currency: &str, instants: &[&str]) -> Value {
    // Serialize the library's actual metadata type: tests exercise its public
    // deserializer, including the fields absent from the older hand-made tests.
    let meta = yahoo_finance_api::YMetaData {
        symbol: symbol.into(),
        currency: Some(currency.into()),
        exchange_timezone_name: zone.into(),
        gmtoffset: 3600, // Deliberately wrong for winter: IANA history must win.
        ..Default::default()
    };
    let mut meta = serde_json::to_value(meta).unwrap();
    // Daily chart responses omit this intraday-only field. The library's
    // default serializer emits null subfields its own deserializer rejects.
    meta.as_object_mut().unwrap().remove("tradingPeriods");
    let n = instants.len();
    json!({"chart":{"error":null,"result":[{
        "meta":meta,"timestamp":instants.iter().map(|s|timestamp(s)).collect::<Vec<_>>(),
        "indicators":{"quote":[{"open":vec![100.0;n],"high":vec![120.0;n],
            "low":vec![80.0;n],"close":vec![100.0;n],"volume":vec![1000;n]}],
            "adjclose":[{"adjclose":vec![100.0;n]}]}
    }]}})
}

fn parse(symbol: &str, value: Value) -> Result<History> {
    let response = YResponse::from_json(value).map_err(|e| {
        eprintln!("Yahoo fixture decode failed: {e:?}");
        yahoo_error(symbol, e)
    })?;
    parse_yahoo_response(symbol, response)
}

#[test]
fn yahoo_library_preserves_historical_dst_and_local_midnight() {
    for (zone, instants, dates) in [
        (
            "Europe/London",
            vec![
                "2023-03-24T00:00:00Z",
                "2023-03-26T23:00:00Z",
                "2023-10-26T23:00:00Z",
                "2023-10-30T00:00:00Z",
            ],
            vec!["2023-03-24", "2023-03-27", "2023-10-27", "2023-10-30"],
        ),
        (
            "America/New_York",
            vec![
                "2023-03-10T14:30:00Z",
                "2023-03-13T13:30:00Z",
                "2023-11-06T14:30:00Z",
            ],
            vec!["2023-03-10", "2023-03-13", "2023-11-06"],
        ),
        (
            "Asia/Seoul",
            vec!["2023-01-01T15:00:00Z"],
            vec!["2023-01-02"],
        ),
        (
            "Asia/Tokyo",
            vec!["2023-01-01T15:00:00Z"],
            vec!["2023-01-02"],
        ),
        (
            "UTC",
            vec![
                "2023-01-01T00:00:00Z",
                "2023-01-07T00:00:00Z",
                "2023-01-08T00:00:00Z",
            ],
            vec!["2023-01-01", "2023-01-07", "2023-01-08"],
        ),
    ] {
        let h = parse("KRW=X", chart("KRW=X", zone, "KRW", &instants)).unwrap();
        assert_eq!(
            h.bars
                .iter()
                .map(|b| b.date.to_string())
                .collect::<Vec<_>>(),
            dates,
            "{zone}"
        );
    }
}

#[test]
fn yahoo_library_adjusts_all_ohlc_once_and_preserves_volume() {
    let mut value = chart(
        "AAPL",
        "America/New_York",
        "USD",
        &["2023-01-03T14:30:00Z", "2023-01-04T14:30:00Z"],
    );
    value["chart"]["result"][0]["indicators"]["adjclose"][0]["adjclose"] = json!([50.0, 99.0]);
    // Split and dividend events must not be applied on top of adjclose again.
    value["chart"]["result"][0]["events"] = json!({"splits":{"1":{"date":1672756200,"numerator":2.0,"denominator":1.0,"splitRatio":"2:1"}},"dividends":{"2":{"date":1672842600,"amount":1.0}}});
    let h = parse("AAPL", value).unwrap();
    for (bar, ratio) in h.bars.iter().zip([0.5, 0.99]) {
        assert_eq!(
            [bar.open, bar.high, bar.low, bar.close],
            [100.0 * ratio, 120.0 * ratio, 80.0 * ratio, 100.0 * ratio]
        );
        assert_eq!(bar.volume, 1000.0);
    }
}

#[test]
fn yahoo_library_missing_adjustment_is_identity_but_zero_is_an_error() {
    let base = chart("KRW=X", "Europe/London", "KRW", &["2023-06-04T23:00:00Z"]);
    for missing in [Value::Null, json!([{"adjclose":[null]}])] {
        let mut value = base.clone();
        value["chart"]["result"][0]["indicators"]["adjclose"] = missing;
        assert_eq!(parse("KRW=X", value).unwrap().bars[0].close, 100.0);
    }
    for invalid in [0.0, -1.0] {
        let mut value = base.clone();
        value["chart"]["result"][0]["indicators"]["adjclose"][0]["adjclose"] = json!([invalid]);
        assert_eq!(parse("KRW=X", value).unwrap_err().0, 503);
    }
}

#[test]
fn yahoo_library_checks_alignment_and_does_not_manufacture_null_bars() {
    let mut value = chart(
        "AAPL",
        "UTC",
        "USD",
        &["2023-01-03T00:00:00Z", "2023-01-04T00:00:00Z"],
    );
    value["chart"]["result"][0]["indicators"]["quote"][0]["open"] = json!([null, 100.0]);
    // A partially absent trading bar is an error, not a holiday.
    assert_eq!(parse("AAPL", value.clone()).unwrap_err().0, 503);
    for field in ["high", "low", "close"] {
        value["chart"]["result"][0]["indicators"]["quote"][0][field][0] = Value::Null;
    }
    let h = parse("AAPL", value.clone()).unwrap();
    assert_eq!(h.bars.len(), 1);
    assert_eq!(h.bars[0].date, date("2023-01-04"));
    value["chart"]["result"][0]["indicators"]["quote"][0]["close"] = json!([100.0]);
    assert_eq!(parse("AAPL", value).unwrap_err().0, 503);
}

#[test]
fn yahoo_library_rejects_invalid_timezone_and_adjustment_overflow() {
    let mut value = chart("AAPL", "invalid/zone", "USD", &["2023-01-03T00:00:00Z"]);
    assert_eq!(parse("AAPL", value.clone()).unwrap_err().0, 503);
    value["chart"]["result"][0]["meta"]["exchangeTimezoneName"] = json!("UTC");
    value["chart"]["result"][0]["indicators"]["quote"][0]["close"] = json!([1.0]);
    value["chart"]["result"][0]["indicators"]["adjclose"][0]["adjclose"] = json!([1e308]);
    assert_eq!(parse("AAPL", value).unwrap_err().0, 503);
}

#[test]
fn yahoo_library_fx_uses_quote_direction_and_never_future_rates() {
    let mut histories = Histories::new();
    for (symbol, currency, rate) in [
        ("KRW=X", "KRW", 1300.0),
        ("JPY=X", "JPY", 150.0),
        ("EURUSD=X", "USD", 1.1),
    ] {
        let mut value = chart(
            symbol,
            "Europe/London",
            currency,
            &["2023-06-01T23:00:00Z", "2023-06-04T23:00:00Z"],
        );
        for key in ["open", "high", "low", "close"] {
            value["chart"]["result"][0]["indicators"]["quote"][0][key] = json!([rate, rate * 2.0]);
        }
        value["chart"]["result"][0]["indicators"]["adjclose"] = Value::Null;
        histories.insert(symbol.into(), parse(symbol, value).unwrap());
    }
    for day in ["2023-06-02", "2023-06-03", "2023-06-04"] {
        assert!((engine::fx("KRW", date(day), &histories).unwrap() * 1300.0 - 1.0).abs() < 1e-12);
        assert!((engine::fx("JPY", date(day), &histories).unwrap() * 150.0 - 1.0).abs() < 1e-12);
        assert_eq!(engine::fx("EUR", date(day), &histories).unwrap(), 1.1);
    }
    assert!(
        (engine::fx("KRW", date("2023-06-05"), &histories).unwrap() * 2600.0 - 1.0).abs() < 1e-12
    );
    assert!(engine::fx("KRW", date("2023-06-01"), &histories).is_err());
    assert!(engine::fx("UNKNOWN", date("2023-06-05"), &histories).is_err());
}

#[test]
fn yahoo_request_padding_includes_end_date_and_handles_leap_days() {
    let (start, end) = yahoo_request_bounds(date("2024-02-29"), date("2024-03-01")).unwrap();
    assert_eq!(start.unix_timestamp(), timestamp("2024-02-28T00:00:00Z"));
    assert_eq!(end.unix_timestamp(), timestamp("2024-03-03T00:00:00Z"));
    assert!(yahoo_request_bounds(NaiveDate::MIN, NaiveDate::MAX).is_err());
}

#[test]
fn yahoo_provider_failure_is_not_reported_as_missing_market_data() {
    for error in [
        YahooError::TooManyRequests("url".into()),
        YahooError::Unauthorized,
        YahooError::InvalidCrumb,
        YahooError::DataInconsistency,
        YahooError::HtmlResponse,
    ] {
        assert_eq!(yahoo_error("AAPL", error).0, 503);
    }
    assert_eq!(
        yahoo_error(
            "MISSING",
            YahooError::FetchFailed("404, request url: test".into())
        )
        .0,
        404
    );
}

#[test]
fn yahoo_library_adjusted_krw_prices_reconcile_to_independent_usd_ledger() {
    let instants = ["2023-06-02T00:00:00Z", "2023-07-03T00:00:00Z"];
    let mut stock = chart("005930.KS", "Asia/Seoul", "KRW", &instants);
    let mut fx = chart("KRW=X", "Europe/London", "KRW", &instants);
    for key in ["open", "high", "low", "close"] {
        stock["chart"]["result"][0]["indicators"]["quote"][0][key] = json!([130000.0, 130000.0]);
        fx["chart"]["result"][0]["indicators"]["quote"][0][key] = json!([1300.0, 2600.0]);
    }
    stock["chart"]["result"][0]["indicators"]["adjclose"][0]["adjclose"] =
        json!([65000.0, 65000.0]);
    fx["chart"]["result"][0]["indicators"]["adjclose"] = Value::Null;
    let histories = Histories::from([
        ("005930.KS".into(), parse("005930.KS", stock).unwrap()),
        ("KRW=X".into(), parse("KRW=X", fx).unwrap()),
    ]);
    let mut request: BacktestRequest = serde_json::from_value(json!({
        "portfolio":[{"symbol":"005930.KS","amount":1000}],
        "start_date":"2023-06-02","end_date":"2023-07-03",
        "strategy":"buy_hold_strategy","commission":0,
        "include_stock_data":false,"include_exchange_rates":false,
        "include_benchmarks":false,"include_news":false
    }))
    .unwrap();
    request.validate(30).unwrap();
    let result = engine::run(
        &request,
        &histories,
        &tokio_util::sync::CancellationToken::new(),
    )
    .unwrap();
    // Entry: 65,000 KRW / 1,300 = $50, so $1,000 buys 20 adjusted units.
    // Exit valuation: 20 * 65,000 / 2,600 = $500; no sale/dividend is invented.
    assert!(
        (result["data"]["portfolio_statistics"]["Final_Value"]
            .as_f64()
            .unwrap()
            - 500.0)
            .abs()
            < 1e-9
    );
    assert!(
        (result["data"]["portfolio_statistics"]["Total_Return"]
            .as_f64()
            .unwrap()
            + 50.0)
            .abs()
            < 1e-9
    );
}

#[test]
fn yahoo_captured_responses_match_independent_dates_and_ohlc() {
    let fixture: Value = serde_json::from_str(include_str!(
        "../tests/fixtures/yahoo-chart-regression.json"
    ))
    .unwrap();
    for case in fixture["cases"].as_array().unwrap() {
        let symbol = case["symbol"].as_str().unwrap();
        let history = parse(symbol, case["raw"].clone()).unwrap();
        assert_eq!(history.currency, case["currency"].as_str().unwrap());
        let expected: Vec<Bar> = serde_json::from_value(case["expected"].clone()).unwrap();
        assert_eq!(history.bars.len(), expected.len(), "{symbol}");
        for (actual, expected) in history.bars.iter().zip(expected) {
            assert_eq!(actual.date, expected.date, "{symbol}");
            for (a, b) in [
                actual.open,
                actual.high,
                actual.low,
                actual.close,
                actual.volume,
            ]
            .into_iter()
            .zip([
                expected.open,
                expected.high,
                expected.low,
                expected.close,
                expected.volume,
            ]) {
                assert!(
                    (a - b).abs() <= 1e-12 * b.abs().max(1.0),
                    "{symbol} {}: {a} != {b}",
                    actual.date
                );
            }
        }
    }
}
