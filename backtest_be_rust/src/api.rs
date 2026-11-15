use crate::{
    data::DataSource,
    db as sqlx, engine,
    error::{Error, Result},
    model,
    validation::{self, ApiError},
};
use axum::{
    Json, Router,
    body::Bytes,
    extract::{ConnectInfo, DefaultBodyLimit, RawQuery, State},
    http::HeaderMap,
    response::{Html, Redirect},
    routing::{get, post},
};
use chrono::{NaiveDate, Utc};
use futures::{StreamExt, stream};
use ipnet::IpNet;
use serde_json::{Map, Value, json};
use std::{
    collections::HashMap,
    net::{IpAddr, SocketAddr},
    sync::{
        Arc, Mutex,
        atomic::{AtomicU64, Ordering},
    },
    time::Duration,
};
use tokio::sync::{OwnedSemaphorePermit, Semaphore};
use tokio_util::sync::CancellationToken;

#[derive(Clone)]
pub struct Settings {
    pub min_days: i64,
    pub execution: Duration,
    pub queue: Duration,
    pub supplemental: Duration,
    pub market_timeout: Duration,
    pub market_queue: Duration,
    pub readiness: Duration,
    pub turnstile: bool,
    pub secret: String,
    pub hosts: Vec<String>,
    pub action: String,
    pub turnstile_timeout: Duration,
    pub trusted: Vec<IpNet>,
}
fn setting(name: &str, default: f64) -> Result<f64> {
    let value = std::env::var(name)
        .ok()
        .map(|s| s.parse::<f64>())
        .transpose()
        .map_err(|_| Error::validation(format!("{name} must be numeric")))?
        .unwrap_or(default);
    if !value.is_finite() || value <= 0.0 || value > 3600.0 {
        return Err(Error::validation(format!(
            "{name} is outside its supported range"
        )));
    }
    Ok(value)
}
fn count(name: &str, default: f64) -> Result<usize> {
    let value = setting(name, default)?;
    if value.fract() != 0.0 || value > 128.0 {
        return Err(Error::validation(format!(
            "{name} must be an integer from 1 to 128"
        )));
    }
    Ok(value as usize)
}
impl Settings {
    pub fn from_env() -> Result<Self> {
        let trusted = std::env::var("TRUSTED_PROXY_CIDRS")
            .unwrap_or_else(|_| {
                "127.0.0.0/8,::1/128,10.0.0.0/8,172.16.0.0/12,192.168.0.0/16,fc00::/7".into()
            })
            .split(',')
            .filter(|s| !s.trim().is_empty())
            .map(|s| {
                s.trim()
                    .parse()
                    .map_err(|_| Error::validation("Invalid TRUSTED_PROXY_CIDRS"))
            })
            .collect::<Result<Vec<IpNet>>>()?;
        let seconds = |name, default| setting(name, default).map(Duration::from_secs_f64);
        let enabled = std::env::var("TURNSTILE_ENABLED").unwrap_or_else(|_| "true".into());
        let turnstile = match enabled.to_ascii_lowercase().as_str() {
            "true" | "1" | "yes" => true,
            "false" | "0" | "no" => false,
            _ => return Err(Error::validation("Invalid TURNSTILE_ENABLED")),
        };
        Ok(Self {
            min_days: setting("MIN_BACKTEST_PERIOD_DAYS", 30.0)? as i64,
            execution: seconds("BACKTEST_TIMEOUT_SECONDS", 60.0)?,
            queue: seconds("BACKTEST_QUEUE_TIMEOUT_SECONDS", 30.0)?,
            supplemental: seconds("SUPPLEMENTAL_DATA_TIMEOUT_SECONDS", 15.0)?,
            market_timeout: seconds("MARKET_DATA_TIMEOUT_SECONDS", 20.0)?,
            market_queue: seconds("MARKET_DATA_QUEUE_TIMEOUT_SECONDS", 2.0)?,
            readiness: seconds("READINESS_DB_TIMEOUT_SECONDS", 2.0)?,
            turnstile,
            secret: std::env::var("TURNSTILE_SECRET_KEY").unwrap_or_default(),
            hosts: std::env::var("TURNSTILE_ALLOWED_HOSTNAMES")
                .unwrap_or_default()
                .split(',')
                .map(|s| s.trim().to_owned())
                .filter(|s| !s.is_empty())
                .collect(),
            action: std::env::var("TURNSTILE_EXPECTED_ACTION")
                .unwrap_or_else(|_| "backtest".into()),
            turnstile_timeout: seconds("TURNSTILE_TIMEOUT_SECONDS", 5.0)?,
            trusted,
        })
    }
}
pub struct Gate {
    slots: Arc<Semaphore>,
    clients: Arc<Mutex<HashMap<String, usize>>>,
    per_client: usize,
    pub total: usize,
    job_name: &'static str,
}
struct Admission {
    key: String,
    clients: Arc<Mutex<HashMap<String, usize>>>,
    permit: Option<OwnedSemaphorePermit>,
}
impl Drop for Admission {
    fn drop(&mut self) {
        let mut clients = self.clients.lock().unwrap_or_else(|p| p.into_inner());
        if let Some(n) = clients.get_mut(&self.key) {
            *n -= 1;
            if *n == 0 {
                clients.remove(&self.key);
            }
        }
    }
}
impl Gate {
    pub fn new(total: usize, per_client: usize) -> Self {
        Self {
            slots: Arc::new(Semaphore::new(total)),
            clients: Arc::default(),
            per_client,
            total,
            job_name: "백테스트",
        }
    }
    async fn acquire(&self, key: String, queue: Duration) -> Result<Admission> {
        {
            let mut clients = self.clients.lock().unwrap_or_else(|p| p.into_inner());
            if clients.values().sum::<usize>() >= self.total + 64 {
                return Err(Error::unavailable("대기열이 가득 찼습니다."));
            }
            let n = clients.entry(key.clone()).or_default();
            if *n >= self.per_client {
                return Err(Error(
                    429,
                    format!(
                        "같은 클라이언트에서 이미 {}건의 {}가 실행 중입니다. 이전 요청이 끝난 뒤 다시 시도해주세요.",
                        self.per_client, self.job_name
                    ),
                ));
            }
            *n += 1;
        }
        let mut guard = Admission {
            key,
            clients: self.clients.clone(),
            permit: None,
        };
        guard.permit = Some(
            tokio::time::timeout(queue, self.slots.clone().acquire_owned())
                .await
                .map_err(|_| Error::unavailable("실행 슬롯 대기 시간이 초과되었습니다."))?
                .map_err(|_| Error::unavailable("서버가 종료 중입니다."))?,
        );
        Ok(guard)
    }
    fn running(&self) -> usize {
        self.total - self.slots.available_permits()
    }
    fn waiting(&self) -> usize {
        self.clients
            .lock()
            .unwrap_or_else(|p| p.into_inner())
            .values()
            .sum::<usize>()
            .saturating_sub(self.running())
    }
}
pub struct AppState {
    pub data: DataSource,
    pub settings: Settings,
    pub calculations: Gate,
    pub reads: Gate,
    completed: AtomicU64,
    failed: AtomicU64,
}
impl AppState {
    pub fn from_env() -> Result<Arc<Self>> {
        Ok(Arc::new(Self {
            data: DataSource::new()?,
            settings: Settings::from_env()?,
            calculations: Gate::new(
                count("MAX_CONCURRENT_BACKTESTS", 8.0)?,
                count("MAX_CONCURRENT_BACKTESTS_PER_CLIENT", 2.0)?,
            ),
            reads: Gate {
                job_name: "참고 데이터 조회",
                ..Gate::new(count("MAX_CONCURRENT_MARKET_DATA", 4.0)?, 4)
            },
            completed: AtomicU64::new(0),
            failed: AtomicU64::new(0),
        }))
    }
}
pub fn router(state: Arc<AppState>) -> Router {
    Router::new().route("/",get(||async{Redirect::temporary("/api/v1/docs")}))
        .route("/health",get(health)).route("/health/ready",get(ready)).route("/metrics",get(metrics))
        .route("/api/v1/backtest",post(backtest))
        .route("/api/v1/prices",get(prices)).route("/api/v1/exchange-rates",get(exchange)).route("/api/v1/benchmarks",get(benchmarks)).route("/api/v1/news",get(news))
        .route("/api/v1/openapi.json",get(||async{Json(serde_json::from_str::<Value>(include_str!("../openapi.json")).unwrap())}))
        .route("/api/v1/docs",get(||async{Html("<!doctype html><html lang=en><title>Backtest API</title><h1>Backtest API</h1><p>Rust backend</p><a href='/api/v1/openapi.json'>OpenAPI 3 schema</a></html>")}))
        .route("/api/v1/redoc",get(||async{Redirect::temporary("/api/v1/docs")}))
        .fallback(||async{Error(404,"Not Found".into())})
        .method_not_allowed_fallback(||async{Error(405,"Method Not Allowed".into())})
        .layer(DefaultBodyLimit::max(64*1024)).layer(tower_http::trace::TraceLayer::new_for_http()).layer(tower_http::catch_panic::CatchPanicLayer::custom(|_|Error(500,"내부 서버 오류가 발생했습니다.".into()).into_response()))
        .with_state(state)
}
use axum::response::IntoResponse;
async fn health() -> Json<Value> {
    Json(json!({"status":"healthy","timestamp":Utc::now(),"version":env!("CARGO_PKG_VERSION")}))
}
async fn ready(State(s): State<Arc<AppState>>) -> (axum::http::StatusCode, Json<Value>) {
    let reason = if let Some(pool) = &s.data.pool {
        match tokio::time::timeout(s.settings.readiness, async {
            use sqlx::Connection;
            let mut connection =
                sqlx::mysql::MySqlConnection::connect_with(&pool.connect_options()).await?;
            sqlx::query("SELECT 1").execute(&mut connection).await
        })
        .await
        {
            Ok(Ok(_)) => "ok",
            Ok(Err(_)) => "unavailable",
            Err(_) => "timeout",
        }
    } else {
        "unavailable"
    };
    (
        if reason == "ok" {
            axum::http::StatusCode::OK
        } else {
            axum::http::StatusCode::SERVICE_UNAVAILABLE
        },
        Json(
            json!({"status":if reason=="ok"{"ready"}else{"not_ready"},"timestamp":Utc::now(),"version":env!("CARGO_PKG_VERSION"),"checks":{"database":reason}}),
        ),
    )
}
async fn metrics(
    State(s): State<Arc<AppState>>,
) -> ([(axum::http::HeaderName, &'static str); 1], String) {
    (
        [(
            axum::http::header::CONTENT_TYPE,
            "text/plain; version=0.0.4",
        )],
        format!(
            "# TYPE backtest_jobs_running gauge\nbacktest_jobs_running {}\n# TYPE backtest_jobs_waiting gauge\nbacktest_jobs_waiting {}\n# TYPE market_data_jobs_running gauge\nmarket_data_jobs_running {}\n# TYPE market_data_jobs_waiting gauge\nmarket_data_jobs_waiting {}\n# TYPE backtest_execution_total counter\nbacktest_execution_total{{status=\"success\"}} {}\nbacktest_execution_total{{status=\"error\"}} {}\n",
            s.calculations.running(),
            s.calculations.waiting(),
            s.reads.running(),
            s.reads.waiting(),
            s.completed.load(Ordering::Relaxed),
            s.failed.load(Ordering::Relaxed)
        ),
    )
}
pub fn client_key(peer: IpAddr, headers: &HeaderMap, trusted: &[IpNet]) -> String {
    let mut client = peer;
    if trusted.iter().any(|net| net.contains(&peer)) {
        let mut hops = vec![];
        let mut valid = true;
        for header in headers.get_all("x-forwarded-for") {
            if let Ok(text) = header.to_str() {
                for item in text.split(',') {
                    if let Ok(ip) = item.trim().parse::<IpAddr>() {
                        hops.push(ip);
                    } else {
                        valid = false;
                    }
                }
            } else {
                valid = false;
            }
        }
        if valid {
            for ip in hops.into_iter().rev() {
                if !trusted.iter().any(|net| net.contains(&client)) {
                    break;
                }
                client = ip;
            }
        }
    }
    match client {
        IpAddr::V4(v) => v.to_string(),
        IpAddr::V6(v) => ipnet::Ipv6Net::new(v, 64).unwrap().trunc().to_string(),
    }
}
async fn verify(s: &AppState, headers: &HeaderMap) -> Result<()> {
    if !s.settings.turnstile {
        return Ok(());
    }
    if s.settings.secret.trim().is_empty()
        || s.settings.hosts.is_empty()
        || s.settings.action.is_empty()
    {
        return Err(Error::unavailable("사람 인증을 확인할 수 없습니다."));
    }
    let values: Vec<_> = headers.get_all("x-turnstile-token").iter().collect();
    let token = values.first().and_then(|v| v.to_str().ok()).unwrap_or("");
    if values.len() != 1 || token.trim().is_empty() || token.len() > 2048 {
        return Err(Error(403, "사람 인증이 필요하거나 만료되었습니다.".into()));
    }
    let request = s
        .data
        .client
        .post("https://challenges.cloudflare.com/turnstile/v0/siteverify")
        .timeout(s.settings.turnstile_timeout)
        .form(&[("secret", s.settings.secret.as_str()), ("response", token)])
        .send()
        .await
        .map_err(|_| Error::unavailable("사람 인증을 확인할 수 없습니다."))?
        .error_for_status()
        .map_err(|_| Error::unavailable("사람 인증을 확인할 수 없습니다."))?;
    let body = request
        .bytes()
        .await
        .map_err(|_| Error::unavailable("사람 인증을 확인할 수 없습니다."))?;
    if body.len() > 16384 {
        return Err(Error::unavailable("사람 인증을 확인할 수 없습니다."));
    }
    let value: Value = serde_json::from_slice(&body)
        .map_err(|_| Error::unavailable("사람 인증을 확인할 수 없습니다."))?;
    if value["success"] != true
        || value["action"] != s.settings.action
        || !value["hostname"]
            .as_str()
            .is_some_and(|h| s.settings.hosts.iter().any(|host| host == h))
    {
        return Err(Error(403, "사람 인증이 필요하거나 만료되었습니다.".into()));
    }
    Ok(())
}
async fn backtest(
    State(s): State<Arc<AppState>>,
    ConnectInfo(peer): ConnectInfo<SocketAddr>,
    headers: HeaderMap,
    body: Bytes,
) -> std::result::Result<Json<Value>, ApiError> {
    verify(&s, &headers).await?;
    let raw: Value = serde_json::from_slice(&body).map_err(validation::invalid_json)?;
    let req = validation::backtest(raw, s.settings.min_days)?;
    let admission = s
        .calculations
        .acquire(
            client_key(peer.ip(), &headers, &s.settings.trusted),
            s.settings.queue,
        )
        .await?;
    let token = CancellationToken::new();
    let _cancel = token.clone().drop_guard();
    let compute = async {
        // Funds wait in cash until an asset's first available trading bar.
        // Listing metadata must not change acceptance when the cache warms.
        let data = s.data.load(&req).await?;
        let input = req.clone();
        tokio::task::spawn_blocking(move || {
            let result = engine::run(&input, &data, &token).map(|mut value| {
                let info: Map<String, Value> = input.portfolio.iter()
                    .filter(|a| !a.cash())
                    .map(|a| (a.symbol.clone(), json!({"symbol":a.symbol,"currency":"USD","company_name":a.symbol,"exchange":"Unknown"})))
                    .collect();
                value["data"]["ticker_info"] = json!(info);
                value
            });
            (admission, result)
        })
        .await
        .map_err(|_| Error(500, "계산 작업이 실패했습니다.".into()))
    };
    let (_admission, mut result) = match tokio::time::timeout(s.settings.execution, compute).await {
        Ok(Ok((guard, Ok(v)))) => (guard, v),
        Ok(Ok((_, Err(e)))) | Ok(Err(e)) => {
            s.failed.fetch_add(1, Ordering::Relaxed);
            return Err(e.into());
        }
        Err(_) => {
            s.failed.fetch_add(1, Ordering::Relaxed);
            return Err(Error(504, "백테스트 실행 시간이 초과되었습니다.".into()).into());
        }
    };
    s.completed.fetch_add(1, Ordering::Relaxed);
    let symbols = req
        .portfolio
        .iter()
        .filter(|a| !a.cash())
        .map(|a| a.symbol.clone())
        .collect::<Vec<_>>();
    let mut extra = empty_data("skipped");
    extra["ticker_info"] = result["data"]["ticker_info"].clone();
    let sections = [
        (
            "prices",
            req.include_stock_data || req.include_volatility_events,
        ),
        ("exchange-rates", req.include_exchange_rates),
        ("benchmarks", req.include_benchmarks),
        ("news", req.include_news),
    ];
    let query = ReadQuery {
        symbols,
        start: Some(req.start_date),
        end: Some(req.end_date),
        limit: 15,
    };
    let responses = futures::future::join_all(
        sections
            .iter()
            .filter(|(_, enabled)| *enabled)
            .map(|(name, _)| reference(&s, name, &query)),
    )
    .await;
    for response in responses {
        merge(&mut extra, response);
    }
    if !req.include_stock_data {
        extra["stock_data"] = json!({});
        extra["supplemental_status"]["stock_data"] = json!("skipped");
    }
    if !req.include_volatility_events {
        extra["volatility_events"] = json!({});
        extra["supplemental_status"]["volatility_events"] = json!("skipped");
    }
    if let Some(benchmark) = extra["sp500_total_return_pct"].as_f64() {
        let total = result["data"]["portfolio_statistics"]["Time_Weighted_Return"]
            .as_f64()
            .unwrap();
        result["data"]["portfolio_statistics"]["sp500_total_return_pct"] = json!(benchmark);
        result["data"]["portfolio_statistics"]["alpha_vs_sp500_pct"] = json!(total - benchmark);
    }
    extra
        .as_object_mut()
        .unwrap()
        .remove("sp500_total_return_pct");
    merge(&mut result["data"], extra);
    Ok(Json(result))
}
fn merge(to: &mut Value, from: Value) {
    if let (Some(dst), Value::Object(src)) = (to.as_object_mut(), from) {
        for (key, value) in src {
            if key == "supplemental_status" {
                let status = dst.entry(key).or_insert(json!({}));
                status
                    .as_object_mut()
                    .unwrap()
                    .extend(value.as_object().unwrap().clone());
            } else {
                dst.insert(key, value);
            }
        }
    }
}
pub fn empty_data(outcome: &str) -> Value {
    json!({"ticker_info":{},"stock_data":{},"volatility_events":{},"exchange_rates":[],"exchange_stats":{},"latest_news":{},"sp500_benchmark":[],"nasdaq_benchmark":[],"supplemental_status":{"ticker_info":outcome,"stock_data":outcome,"volatility_events":outcome,"exchange_rates":outcome,"benchmarks":outcome,"news":outcome}})
}
struct ReadQuery {
    symbols: Vec<String>,
    start: Option<NaiveDate>,
    end: Option<NaiveDate>,
    limit: usize,
}
impl ReadQuery {
    fn parse(section: &str, raw: Option<String>) -> Result<Self> {
        let mut q = Self {
            symbols: vec![],
            start: None,
            end: None,
            limit: 15,
        };
        let pairs: Vec<_> = url::form_urlencoded::parse(raw.as_deref().unwrap_or("").as_bytes())
            .into_owned()
            .collect();
        for (index, (key, value)) in pairs.iter().enumerate() {
            // Starlette uses the last scalar value; symbols remains a list.
            if key != "symbols" && pairs[index + 1..].iter().any(|(later, _)| later == key) {
                continue;
            }
            match key.as_ref() {
                "symbols" if section == "prices" || section == "news" => {
                    model::validate_symbol(value, false)?;
                    q.symbols.push(value.to_ascii_uppercase());
                }
                "start_date" if section != "news" => {
                    q.start = Some(
                        value
                            .parse()
                            .map_err(|_| Error::validation("날짜 형식이 잘못되었습니다."))?,
                    )
                }
                "end_date" if section != "news" => {
                    q.end = Some(
                        value
                            .parse()
                            .map_err(|_| Error::validation("날짜 형식이 잘못되었습니다."))?,
                    )
                }
                "limit" if section == "news" => {
                    q.limit = value
                        .parse()
                        .map_err(|_| Error::validation("유효하지 않은 뉴스 개수입니다."))?
                }
                _ => return Err(Error::validation("지원하지 않는 조회 인자입니다.")),
            }
        }
        if (section == "prices" || section == "news")
            && (q.symbols.is_empty() || q.symbols.len() > 20)
        {
            return Err(Error::validation("1~20개의 종목을 지정해 주세요."));
        }
        if section != "news" {
            model::validate_period(
                q.start
                    .ok_or_else(|| Error::validation("시작 날짜가 필요합니다."))?,
                q.end
                    .ok_or_else(|| Error::validation("종료 날짜가 필요합니다."))?,
                0,
            )?;
        }
        if !(1..=20).contains(&q.limit) {
            return Err(Error::validation("뉴스 개수는 1~20이어야 합니다."));
        }
        q.symbols.sort();
        q.symbols.dedup();
        Ok(q)
    }
}
macro_rules! read_handler {
    ($fn:ident,$section:literal) => {
        async fn $fn(
            State(s): State<Arc<AppState>>,
            ConnectInfo(peer): ConnectInfo<SocketAddr>,
            headers: HeaderMap,
            RawQuery(raw): RawQuery,
        ) -> std::result::Result<Json<Value>, ApiError> {
            read(s, peer, headers, raw, $section).await
        }
    };
}
read_handler!(prices, "prices");
read_handler!(exchange, "exchange-rates");
read_handler!(benchmarks, "benchmarks");
read_handler!(news, "news");
async fn read(
    s: Arc<AppState>,
    peer: SocketAddr,
    headers: HeaderMap,
    raw: Option<String>,
    section: &str,
) -> std::result::Result<Json<Value>, ApiError> {
    validation::query(section, raw.as_deref())?;
    let query = ReadQuery::parse(section, raw)?;
    let _admission = s
        .reads
        .acquire(
            client_key(peer.ip(), &headers, &s.settings.trusted),
            s.settings.market_queue,
        )
        .await?;
    let data = tokio::time::timeout(s.settings.market_timeout, reference(&s, section, &query))
        .await
        .map_err(|_| Error(504, "참고 데이터 조회 시간이 초과되었습니다.".into()))?;
    Ok(Json(json!({"status":"success","data":data})))
}
async fn reference(s: &AppState, section: &str, q: &ReadQuery) -> Value {
    let fields: &[&str] = match section {
        "prices" => &["ticker_info", "stock_data", "volatility_events"],
        "exchange-rates" => &["exchange_rates", "exchange_stats"],
        "benchmarks" => &["sp500_benchmark", "nasdaq_benchmark"],
        _ => &["latest_news"],
    };
    let statuses: &[&str] = match section {
        "prices" => &["ticker_info", "stock_data", "volatility_events"],
        "exchange-rates" => &["exchange_rates"],
        "benchmarks" => &["benchmarks"],
        _ => &["news"],
    };
    let result = tokio::time::timeout(s.settings.supplemental, collect(s, section, q)).await;
    let mut value = match result {
        Ok(Ok(v)) => v,
        other => {
            let outcome = if other.is_err() { "timeout" } else { "error" };
            let all = empty_data(outcome);
            let mut out = Map::new();
            for key in fields {
                out.insert((*key).into(), all[key].clone());
            }
            out.insert("supplemental_status".into(), json!({}));
            for name in statuses {
                out["supplemental_status"][name] = json!(outcome);
            }
            Value::Object(out)
        }
    };
    if section == "benchmarks"
        && !value
            .as_object()
            .unwrap()
            .contains_key("sp500_total_return_pct")
    {
        value["sp500_total_return_pct"] = Value::Null;
    }
    value
}
async fn collect(s: &AppState, section: &str, q: &ReadQuery) -> Result<Value> {
    let start = q.start.unwrap_or_else(|| Utc::now().date_naive());
    let end = q.end.unwrap_or(start);
    match section {
        "prices" => {
            let mut info = Map::new();
            let mut prices = Map::new();
            let mut volatility = Map::new();
            let tasks: Vec<_> = q
                .symbols
                .clone()
                .into_iter()
                .map(|symbol| {
                    let source = s.data.clone();
                    async move { source.history(&symbol, start, end).await }
                })
                .collect();
            let results = stream::iter(tasks)
                .buffer_unordered(4)
                .collect::<Vec<_>>()
                .await;
            for result in results {
                let h = result?;
                info.insert(h.symbol.clone(),json!({"symbol":h.symbol,"currency":h.currency,"company_name":h.company_name,"exchange":h.exchange,"first_trade_date":h.first_trade_date}));
                prices.insert(
                    h.symbol.clone(),
                    json!(
                        h.bars
                            .iter()
                            .map(|b| json!({"date":b.date,"price":b.close,"volume":b.volume}))
                            .collect::<Vec<_>>()
                    ),
                );
                let threshold = setting("VOLATILITY_THRESHOLD_PCT", 5.0)?;
                let events:Vec<_>=h.bars.windows(2).rev().filter_map(|bars|{let r=(bars[1].close/bars[0].close-1.0)*100.0;if r.abs()<threshold{None}else{Some(json!({"date":bars[1].date,"daily_return":r,"close_price":bars[1].close,"volume":bars[1].volume,"event_type":if r>0.0{"급등"}else{"급락"}}))}}).take(10).collect();
                volatility.insert(h.symbol.clone(), json!(events));
            }
            let has_prices = prices
                .values()
                .any(|v| v.as_array().is_some_and(|a| !a.is_empty()));
            let has_events = volatility
                .values()
                .any(|v| v.as_array().is_some_and(|a| !a.is_empty()));
            Ok(
                json!({"ticker_info":info,"stock_data":prices,"volatility_events":volatility,"supplemental_status":{"ticker_info":if info.is_empty(){"empty"}else{"ok"},"stock_data":if has_prices{"ok"}else{"empty"},"volatility_events":if has_events{"ok"}else{"empty"}}}),
            )
        }
        "exchange-rates" => {
            let h = s.data.history("KRW=X", start, end).await?;
            let points: Vec<_> = h
                .bars
                .iter()
                .map(|b| json!({"date":b.date,"rate":b.close}))
                .collect();
            let stats = if points.is_empty() {
                json!({})
            } else {
                json!({"start_point":points.first(),"end_point":points.last(),"high_point":points.iter().max_by(|a,b|a["rate"].as_f64().unwrap().total_cmp(&b["rate"].as_f64().unwrap())),"low_point":points.iter().min_by(|a,b|a["rate"].as_f64().unwrap().total_cmp(&b["rate"].as_f64().unwrap()))})
            };
            Ok(
                json!({"exchange_rates":points,"exchange_stats":stats,"supplemental_status":{"exchange_rates":if points.is_empty(){"empty"}else{"ok"}}}),
            )
        }
        "benchmarks" => {
            let (sp, nasdaq) = tokio::try_join!(
                s.data.history("^GSPC", start, end),
                s.data.history("^IXIC", start, end)
            )?;
            let points = |h: &crate::model::History| {
                let mut points = Vec::new();
                if h.bars.is_empty() {
                    return points;
                }
                let mut index = 0;
                let mut previous = h.bars[0].close;
                for offset in 0..=(end - start).num_days() {
                    let date = start + chrono::Duration::days(offset);
                    while index + 1 < h.bars.len() && h.bars[index + 1].date <= date {
                        index += 1;
                    }
                    let close = h.bars[index].close;
                    points.push(
                        json!({"date":date,"close":close,"return_pct":(close/previous-1.0)*100.0}),
                    );
                    previous = close;
                }
                points
            };
            let ret = if sp.bars.len() >= 2 {
                Some((sp.bars.last().unwrap().close / sp.bars[0].close - 1.0) * 100.0)
            } else {
                None
            };
            Ok(
                json!({"sp500_benchmark":points(&sp),"nasdaq_benchmark":points(&nasdaq),"sp500_total_return_pct":ret,"supplemental_status":{"benchmarks":if sp.bars.is_empty()&&nasdaq.bars.is_empty(){"empty"}else{"ok"}}}),
            )
        }
        _ => {
            let mut news = Map::new();
            let limit = q.limit;
            let tasks: Vec<_> = q
                .symbols
                .clone()
                .into_iter()
                .map(|symbol| {
                    let source = s.data.clone();
                    async move {
                        let items = source.news(&symbol, limit).await;
                        (symbol, items)
                    }
                })
                .collect();
            let results = stream::iter(tasks)
                .buffer_unordered(4)
                .collect::<Vec<_>>()
                .await;
            let mut any = false;
            for (symbol, result) in results {
                let items = result?;
                any |= !items.is_empty();
                news.insert(symbol, json!(items));
            }
            Ok(json!({"latest_news":news,"supplemental_status":{"news":if any{"ok"}else{"empty"}}}))
        }
    }
}

#[cfg(test)]
#[path = "api_tests.rs"]
mod tests;
