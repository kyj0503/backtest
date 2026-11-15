use super::*;
use crate::model::BacktestRequest;
use axum::{
    Extension,
    body::Body,
    http::{Request, StatusCode},
};
use http_body_util::BodyExt;
use tower::ServiceExt;

#[tokio::test]
#[ignore = "requires a disposable MySQL with schema.sql; RUST_TEST_DATABASE=1"]
async fn t04_listing_waiting_cash_is_identical_without_cache_cold_warm_and_after_restart() {
    assert_eq!(std::env::var("RUST_TEST_DATABASE").as_deref(), Ok("1"));
    let first = chrono::NaiveDate::from_ymd_opt(2023, 1, 2).unwrap();
    let h = crate::model::History {
        symbol: "ZZT04IPO".into(),
        currency: "USD".into(),
        company_name: "test".into(),
        exchange: "synthetic".into(),
        first_trade_date: Some(first + chrono::Duration::days(10)),
        bars: (10..40)
            .map(|i| crate::model::Bar {
                date: first + chrono::Duration::days(i),
                open: 100.,
                high: 100.,
                low: 100.,
                close: 100.,
                volume: 1000.,
            })
            .collect(),
    };
    let fixtures = Arc::new(crate::model::Histories::from([(h.symbol.clone(), h)]));
    let make_state = |database: bool, with_fixture: bool| {
        let mut s = Arc::try_unwrap(state()).ok().unwrap();
        s.data = DataSource::new().unwrap();
        if !database {
            s.data.pool = None;
        }
        s.data.fixtures = Some(if with_fixture {
            fixtures.clone()
        } else {
            Arc::default()
        });
        Arc::new(s)
    };
    let cold = make_state(true, true);
    let pool = cold.data.pool.as_ref().unwrap();
    crate::db::query(
        "DELETE FROM daily_prices WHERE stock_id=(SELECT id FROM stocks WHERE ticker='ZZT04IPO')",
    )
    .execute(pool)
    .await
    .unwrap();
    crate::db::query("DELETE FROM stocks WHERE ticker='ZZT04IPO'")
        .execute(pool)
        .await
        .unwrap();
    let request = json!({"portfolio":[{"symbol":"ZZT04IPO","amount":10000}],"start_date":first,"end_date":first+chrono::Duration::days(39),"commission":0,"rebalance_frequency":"none","include_stock_data":false,"include_volatility_events":false,"include_exchange_rates":false,"include_benchmarks":false,"include_news":false});
    for s in [
        make_state(false, true),
        cold.clone(),
        cold,
        make_state(true, false),
    ] {
        let (status, v) = call(s, "POST", "/api/v1/backtest", request.clone()).await;
        assert_eq!(status, StatusCode::OK, "{v}");
        assert_eq!(v["data"]["portfolio_statistics"]["Final_Value"], 10000.);
        assert_eq!(
            v["data"]["portfolio_statistics"]["Time_Weighted_Return"],
            0.
        );
        for row in v["data"]["weight_history"].as_array().unwrap() {
            assert_eq!(row["ZZT04IPO"], 1.);
        }
        for value in v["data"]["equity_curve"].as_object().unwrap().values() {
            assert_eq!(value, 10000.);
        }
    }
}

#[test]
fn validation_payloads_match_captured_python_responses() {
    let cases: Vec<Value> =
        serde_json::from_str(include_str!("../tests/fixtures/http-boundary.json")).unwrap();
    for case in cases {
        let req = &case["request"];
        let error = if req["method"] == "GET" {
            let path = req["path"].as_str().unwrap();
            let (route, query) = path.split_once('?').unwrap();
            validation::query(route.rsplit('/').next().unwrap(), Some(query)).unwrap_err()
        } else if let Some(raw) = req["raw"].as_str() {
            validation::invalid_json(serde_json::from_str::<Value>(raw).unwrap_err())
        } else {
            validation::backtest(req["body"].clone(), 30).unwrap_err()
        };
        let actual = match error {
            ApiError::Application(e) => json!({"detail":e.1}),
            ApiError::Validation(errors) => json!({"detail":errors}),
        };
        assert_eq!(actual, case["expected"], "{}", case["name"]);
    }
}

#[tokio::test]
async fn legacy_coercion_duplicate_queries_and_ipo_remain_supported() {
    let (status, error) = call(state(), "GET", "/api/v1/backtest", Value::Null).await;
    assert_eq!(status, StatusCode::METHOD_NOT_ALLOWED);
    assert_eq!(error, json!({"detail":"Method Not Allowed"}));
    // CASH is also a real stock ticker unless asset_type explicitly says cash.
    let mut stock_state = Arc::try_unwrap(state()).ok().unwrap();
    let mut stock_data = stock_state.data.fixtures.as_ref().unwrap().as_ref().clone();
    let mut cash_stock = stock_data["AAPL"].clone();
    cash_stock.symbol = "CASH".into();
    stock_data.insert("CASH".into(), cash_stock);
    stock_state.data.fixtures = Some(Arc::new(stock_data));
    let mut stock_request = input();
    stock_request["portfolio"] = json!([{"symbol":"CASH","amount":1000}]);
    let (status, result) = call(
        Arc::new(stock_state),
        "POST",
        "/api/v1/backtest",
        stock_request,
    )
    .await;
    assert_eq!(status, StatusCode::OK);
    assert_eq!(
        result["data"]["individual_results"]
            .as_array()
            .unwrap()
            .len(),
        1
    );
    for amount in [json!("10000"), json!(true)] {
        let mut req = input();
        req["portfolio"][0]["amount"] = amount;
        assert_eq!(
            call(state(), "POST", "/api/v1/backtest", req).await.0,
            StatusCode::OK
        );
    }
    let s = state();
    let (_, duplicate) = call(
        s.clone(),
        "GET",
        "/api/v1/prices?symbols=AAPL&start_date=invalid&start_date=2023-01-03&end_date=2023-10-31",
        Value::Null,
    )
    .await;
    let (_, single) = call(
        s,
        "GET",
        "/api/v1/prices?symbols=AAPL&start_date=2023-01-03&end_date=2023-10-31",
        Value::Null,
    )
    .await;
    assert_eq!(duplicate, single);
    let mut s = Arc::try_unwrap(state()).ok().unwrap();
    let mut histories = s.data.fixtures.as_ref().unwrap().as_ref().clone();
    histories.get_mut("AAPL").unwrap().first_trade_date = Some("2023-01-02".parse().unwrap());
    s.data.fixtures = Some(Arc::new(histories));
    let mut req = input();
    req["start_date"] = json!("2022-01-01");
    let (status, value) = call(Arc::new(s), "POST", "/api/v1/backtest", req).await;
    assert_eq!(status, StatusCode::OK);
    assert_eq!(value["data"]["portfolio_statistics"]["Start"], "2022-01-01");
    assert!(
        value["data"]["equity_curve"]["2022-01-01"]
            .as_f64()
            .unwrap()
            > 0.0
    );
    assert_eq!(value["data"]["ticker_info"]["AAPL"]["exchange"], "Unknown");
}

#[test]
fn yahoo_historical_dates_use_iana_rules_in_both_dst_seasons() {
    for (zone, offset, instants, dates) in [
        (
            "Europe/London",
            0,
            vec![
                "2023-03-24T00:00:00Z",
                "2023-03-26T23:00:00Z",
                "2023-10-26T23:00:00Z",
                "2023-10-30T00:00:00Z",
            ],
            vec!["2023-03-24", "2023-03-27", "2023-10-27", "2023-10-30"],
        ),
        (
            "Europe/London",
            3600,
            vec!["2023-01-03T00:00:00Z", "2023-06-04T23:00:00Z"],
            vec!["2023-01-03", "2023-06-05"],
        ),
        (
            "Asia/Seoul",
            32400,
            vec!["2023-10-31T00:00:00Z", "2023-11-01T00:00:00Z"],
            vec!["2023-10-31", "2023-11-01"],
        ),
    ] {
        let timestamps: Vec<_> = instants
            .iter()
            .map(|s| chrono::DateTime::parse_from_rfc3339(s).unwrap().timestamp())
            .collect();
        let n = timestamps.len();
        let chart = json!({"chart":{"result":[{"meta":{"currency":"KRW","exchangeTimezoneName":zone,"gmtoffset":offset},"timestamp":timestamps,"indicators":{"quote":[{"open":vec![1300;n],"high":vec![1300;n],"low":vec![1300;n],"close":vec![1300;n],"volume":vec![0;n]}]}}]}});
        let h = crate::data::parse_chart("KRW=X", chart).unwrap();
        assert_eq!(
            h.bars
                .iter()
                .map(|b| b.date.to_string())
                .collect::<Vec<_>>(),
            dates
        );
    }
}

fn compare_reference(actual: &Value, expected: &Value) {
    match expected {
        Value::Number(n) => assert!((actual.as_f64().unwrap() - n.as_f64().unwrap()).abs() < 1e-6),
        Value::Object(map) => {
            for (key, value) in map {
                compare_reference(&actual[key], value);
            }
        }
        Value::Array(array) => {
            assert_eq!(actual.as_array().unwrap().len(), array.len());
            for (a, e) in actual.as_array().unwrap().iter().zip(array) {
                compare_reference(a, e);
            }
        }
        _ => assert_eq!(actual, expected),
    }
}

#[tokio::test]
async fn supplemental_transforms_match_python() {
    let expected: Value =
        serde_json::from_str(include_str!("../tests/fixtures/supplemental.json")).unwrap();
    let s = state();
    for (path, fields) in [
        (
            "/api/v1/prices?symbols=AAPL&symbols=MSFT&start_date=2023-01-02&end_date=2023-10-31",
            vec!["stock_data", "volatility_events"],
        ),
        (
            "/api/v1/exchange-rates?start_date=2023-01-02&end_date=2023-10-31",
            vec!["exchange_rates", "exchange_stats"],
        ),
        (
            "/api/v1/benchmarks?start_date=2023-01-02&end_date=2023-10-31",
            vec!["sp500_benchmark", "nasdaq_benchmark"],
        ),
    ] {
        let (status, body) = call(s.clone(), "GET", path, Value::Null).await;
        assert_eq!(status, StatusCode::OK);
        for field in fields {
            compare_reference(&body["data"][field], &expected[field]);
        }
    }
}

fn state() -> Arc<AppState> {
    let mut data = DataSource::new().unwrap();
    data.pool = None;
    data.fixtures = Some(Arc::new(
        serde_json::from_str(include_str!("../tests/fixtures/histories.json")).unwrap(),
    ));
    let mut settings = Settings::from_env().unwrap();
    settings.turnstile = false;
    Arc::new(AppState {
        data,
        settings,
        calculations: Gate::new(2, 1),
        reads: Gate::new(4, 4),
        completed: AtomicU64::new(0),
        failed: AtomicU64::new(0),
    })
}
fn input() -> Value {
    serde_json::from_str::<Vec<Value>>(include_str!("../tests/fixtures/parity.json")).unwrap()[0]["request"].clone()
}
async fn call(state: Arc<AppState>, method: &str, path: &str, body: Value) -> (StatusCode, Value) {
    let request = Request::builder()
        .method(method)
        .uri(path)
        .header("content-type", "application/json")
        .body(if body.is_null() {
            Body::empty()
        } else {
            Body::from(body.to_string())
        })
        .unwrap();
    let response = router(state)
        .layer(Extension(ConnectInfo(
            "203.0.113.9:1234".parse::<SocketAddr>().unwrap(),
        )))
        .oneshot(request)
        .await
        .unwrap();
    let status = response.status();
    let bytes = response.into_body().collect().await.unwrap().to_bytes();
    (status, serde_json::from_slice(&bytes).unwrap())
}
#[tokio::test]
async fn calculation_and_independent_reads_keep_contract() {
    let s = state();
    let (status, body) = call(s.clone(), "POST", "/api/v1/backtest", input()).await;
    assert_eq!(status, StatusCode::OK);
    assert_eq!(body["status"], "success");
    assert!(
        body["data"]["portfolio_statistics"]["Final_Value"]
            .as_f64()
            .unwrap()
            > 0.0
    );
    assert_eq!(body["data"]["supplemental_status"]["stock_data"], "skipped");
    for (path, field) in [
        (
            "/api/v1/prices?symbols=AAPL&symbols=MSFT&start_date=2023-01-02&end_date=2023-10-31",
            "stock_data",
        ),
        (
            "/api/v1/exchange-rates?start_date=2023-01-02&end_date=2023-10-31",
            "exchange_rates",
        ),
        (
            "/api/v1/benchmarks?start_date=2023-01-02&end_date=2023-10-31",
            "sp500_benchmark",
        ),
        ("/api/v1/news?symbols=AAPL&limit=15", "latest_news"),
    ] {
        let (status, body) = call(s.clone(), "GET", path, Value::Null).await;
        assert_eq!(status, StatusCode::OK, "{path}");
        assert!(!body["data"][field].is_null(), "{path}");
        assert!(body["data"]["portfolio_statistics"].is_null());
    }
    assert_eq!(s.completed.load(Ordering::Relaxed), 1);
}
#[tokio::test]
async fn legacy_supplemental_defaults_and_health() {
    let s = state();
    let mut request = input();
    for key in [
        "include_stock_data",
        "include_volatility_events",
        "include_exchange_rates",
        "include_benchmarks",
        "include_news",
    ] {
        request.as_object_mut().unwrap().remove(key);
    }
    let (status, body) = call(s.clone(), "POST", "/api/v1/backtest", request).await;
    assert_eq!(status, StatusCode::OK);
    assert_eq!(body["data"]["supplemental_status"]["stock_data"], "ok");
    assert!(body["data"]["portfolio_statistics"]["alpha_vs_sp500_pct"].is_number());
    assert_eq!(
        call(s.clone(), "GET", "/health", Value::Null).await.0,
        StatusCode::OK
    );
    let (status, body) = call(s, "GET", "/health/ready", Value::Null).await;
    assert_eq!(status, StatusCode::SERVICE_UNAVAILABLE);
    assert_eq!(body["checks"]["database"], "unavailable");
}
#[tokio::test]
async fn validation_rejects_invalid_inputs_before_execution() {
    for (key, value) in [
        ("strategy", json!("unknown")),
        ("commission", json!(0.1)),
        ("end_date", json!("2023-01-05")),
        ("end_date", json!("9999-01-01")),
        ("rebalance_frequency", json!("weekly_4")),
        ("portfolio", json!([])),
    ] {
        let mut req = input();
        req[key] = value.clone();
        let s = state();
        let (status, body) = call(s.clone(), "POST", "/api/v1/backtest", req).await;
        assert_eq!(status, StatusCode::UNPROCESSABLE_ENTITY, "{key}");
        if key == "end_date" && value == "2023-01-05" {
            assert!(body["detail"].is_string());
        } else {
            assert!(body["detail"].is_array());
        }
        assert_eq!(s.completed.load(Ordering::Relaxed), 0);
    }
    for path in [
        "/api/v1/news?symbols=AAPL&start_date=2023-01-01",
        "/api/v1/news?symbols=AAPL&limit=21",
        "/api/v1/prices?symbols=AAPL",
        "/api/v1/benchmarks?start_date=2023-01-01&end_date=2023-02-01&extra=x",
    ] {
        assert_eq!(
            call(state(), "GET", path, Value::Null).await.0,
            StatusCode::UNPROCESSABLE_ENTITY
        );
    }
}
#[tokio::test]
async fn turnstile_fails_closed_before_calculation() {
    let mut s = Arc::try_unwrap(state()).ok().unwrap();
    s.settings.turnstile = true;
    s.settings.secret.clear();
    s.settings.hosts.clear();
    assert_eq!(
        call(Arc::new(s), "POST", "/api/v1/backtest", input())
            .await
            .0,
        StatusCode::SERVICE_UNAVAILABLE
    );
    let mut s = Arc::try_unwrap(state()).ok().unwrap();
    s.settings.turnstile = true;
    s.settings.secret = "test-secret".into();
    s.settings.hosts = vec!["test.example".into()];
    let s = Arc::new(s);
    assert_eq!(
        call(s.clone(), "POST", "/api/v1/backtest", input()).await.0,
        StatusCode::FORBIDDEN
    );
    assert_eq!(s.calculations.running(), 0);
}
#[tokio::test]
async fn admission_holds_slots_and_releases_client_counts_on_cancellation() {
    let gate = Gate::new(1, 1);
    let first = gate
        .acquire("a".into(), Duration::from_millis(20))
        .await
        .unwrap();
    assert_eq!(
        gate.acquire("a".into(), Duration::from_millis(20))
            .await
            .err()
            .unwrap()
            .0,
        429
    );
    assert_eq!(
        gate.acquire("b".into(), Duration::from_millis(20))
            .await
            .err()
            .unwrap()
            .0,
        503
    );
    assert_eq!(gate.running(), 1);
    assert_eq!(gate.waiting(), 0);
    assert_eq!(gate.clients.lock().unwrap().len(), 1);
    assert!(
        tokio::time::timeout(
            Duration::from_millis(1),
            gate.acquire("c".into(), Duration::from_secs(1))
        )
        .await
        .is_err()
    );
    assert_eq!(gate.waiting(), 0);
    drop(first);
    assert_eq!(gate.running(), 0);
    assert!(gate.clients.lock().unwrap().is_empty());
    let _again = gate
        .acquire("a".into(), Duration::from_millis(20))
        .await
        .unwrap();
}
#[test]
fn forwarded_headers_only_trusted_and_ipv6_bucketed() {
    let mut headers = HeaderMap::new();
    headers.insert("x-forwarded-for", "198.51.100.5, 10.0.0.1".parse().unwrap());
    let trusted = vec!["10.0.0.0/8".parse().unwrap()];
    assert_eq!(
        client_key("203.0.113.2".parse().unwrap(), &headers, &trusted),
        "203.0.113.2"
    );
    assert_eq!(
        client_key("10.0.0.2".parse().unwrap(), &headers, &trusted),
        "198.51.100.5"
    );
    assert_eq!(
        client_key("2001:db8::1234".parse().unwrap(), &headers, &trusted),
        "2001:db8::/64"
    );
}
#[tokio::test]
async fn no_future_fx_and_cooperative_engine_cancel() {
    let s = state();
    let data = s.data.fixtures.as_ref().unwrap();
    assert!(engine::fx("KRW", "2022-12-31".parse().unwrap(), data).is_err());
    assert!(engine::fx("UNKNOWN", "2023-01-01".parse().unwrap(), data).is_err());
    let req: BacktestRequest = serde_json::from_value(input()).unwrap();
    let cancel = CancellationToken::new();
    cancel.cancel();
    assert_eq!(engine::run(&req, data, &cancel).unwrap_err().0, 499);
}
#[test]
fn yahoo_prices_apply_adjustment_and_skip_missing_bars() {
    let chart = json!({"chart":{"result":[{"meta":{"currency":"USD","gmtoffset":-18000},"timestamp":[1672675200,1672761600],"indicators":{"quote":[{"open":[100,null],"high":[110,null],"low":[90,null],"close":[105,null],"volume":[500,0]}],"adjclose":[{"adjclose":[52.5,null]}]}}]}});
    let h = crate::data::parse_chart("AAPL", chart).unwrap();
    assert_eq!(h.bars.len(), 1);
    assert_eq!(h.bars[0].open, 50.0);
    assert_eq!(h.bars[0].close, 52.5);
}
#[test]
fn fifth_weekday_and_leap_year_schedule_remain_anchored() {
    let dates = crate::schedule::schedule(
        "2024-01-29".parse().unwrap(),
        "2024-04-30".parse().unwrap(),
        "monthly_1",
    );
    assert_eq!(
        dates.iter().map(ToString::to_string).collect::<Vec<_>>(),
        vec!["2024-02-26", "2024-03-25", "2024-04-29"]
    );
}
