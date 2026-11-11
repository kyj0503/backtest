use crate::{
    db as sqlx, engine,
    error::{Error, Result},
    model::{BacktestRequest, Bar, Histories, History},
};
use chrono::{DateTime, Duration, NaiveDate, Utc};
use futures::{StreamExt, stream};
use serde_json::{Value, json};
use sqlx::{
    Connection, MySqlPool, Row,
    mysql::{MySqlConnectOptions, MySqlPoolOptions, MySqlSslMode},
};
use std::{
    collections::HashMap,
    sync::Arc,
    time::{Duration as Timeout, Instant},
};
use tokio::sync::Mutex;
use yahoo_finance_api::{YResponse, YahooConnector, YahooConnectorBuilder, YahooError};

type Cache = Arc<Mutex<HashMap<(String, NaiveDate, NaiveDate), (Instant, History)>>>;
// v4 rejects mixed adjustment bases and invalid OHLC; older snapshots cannot
// prove those properties and must be fetched again without clearing user DBs.
const PRICE_SNAPSHOT_VERSION: u64 = 4;
fn validate_prices(history: &History) -> Result<()> {
    if history
        .bars
        .iter()
        .any(|b| !valid_quote(&history.symbol, b))
    {
        return Err(Error::unavailable("시세의 OHLC 값이 유효하지 않습니다."));
    }
    Ok(())
}
fn valid_quote(symbol: &str, bar: &Bar) -> bool {
    // FX conversions consume a daily point rate, not an executable OHLC bar.
    // The engine separately requires full OHLC for every traded portfolio asset.
    if symbol.ends_with("=X") {
        bar.valid_rate()
    } else {
        bar.valid_prices()
    }
}
#[cfg(test)]
#[path = "data_regression_tests.rs"]
mod regression_tests;
#[cfg(test)]
#[path = "yahoo_regression_tests.rs"]
mod yahoo_regression_tests;
#[derive(Clone)]
pub struct DataSource {
    pub pool: Option<MySqlPool>,
    pub client: reqwest::Client,
    yahoo_client: Arc<YahooConnector>,
    pub fixtures: Option<Arc<Histories>>,
    cache: Cache,
}
fn env(name: &str, default: &str) -> String {
    std::env::var(name).unwrap_or_else(|_| default.into())
}
impl DataSource {
    pub fn new() -> Result<Self> {
        let client = reqwest::Client::builder()
            .timeout(Timeout::from_secs(15))
            .connect_timeout(Timeout::from_secs(5))
            .user_agent("Mozilla/5.0 (compatible; Backtest/1.7.10)")
            .redirect(reqwest::redirect::Policy::limited(3))
            .https_only(true)
            .build()
            .map_err(|_| Error::unavailable("HTTP 클라이언트 초기화 실패"))?;
        // A single connector shares the library's 10 requests/second limiter
        // across DataSource clones. Reuse the same bounded Rustls HTTP client.
        let yahoo_client = Arc::new(
            YahooConnectorBuilder::build_with_client(client.clone())
                .map_err(|_| Error::unavailable("Yahoo 클라이언트 초기화 실패"))?,
        );
        let raw_url = env("DATABASE_URL", "");
        let pool = if !raw_url.is_empty() || std::env::var("DATABASE_HOST").is_ok() {
            let mut options = MySqlConnectOptions::new()
                .host(&env("DATABASE_HOST", "localhost"))
                .port(
                    env("DATABASE_PORT", "3306")
                        .parse()
                        .map_err(|_| Error::validation("DATABASE_PORT가 유효하지 않습니다."))?,
                )
                .username(&env("DATABASE_USER", "appuser"))
                .password(&env("DATABASE_PASSWORD", ""))
                .database(&env("DATABASE_NAME", "stock_data_cache"))
                .charset("utf8mb4");
            if !raw_url.is_empty() {
                let url = url::Url::parse(&raw_url.replace("mysql+pymysql://", "mysql://"))
                    .map_err(|_| Error::validation("DATABASE_URL이 유효하지 않습니다."))?;
                // SQLAlchemy's ssl_ca/ssl_check_hostname names are handled explicitly below.
                let mut sqlx_url = url.clone();
                sqlx_url.set_query(None);
                options = sqlx_url
                    .as_str()
                    .parse()
                    .map_err(|_| Error::validation("DATABASE_URL이 유효하지 않습니다."))?;
                let q: HashMap<_, _> = url.query_pairs().into_owned().collect();
                if let Some(ca) = q.get("ssl_ca").or(q.get("ssl-ca")) {
                    options = options.ssl_ca(ca).ssl_mode(
                        if q.get("ssl_check_hostname").is_some_and(|v| v == "false") {
                            MySqlSslMode::VerifyCa
                        } else {
                            MySqlSslMode::VerifyIdentity
                        },
                    );
                }
                if let Some(mode) = q.get("ssl-mode") {
                    options =
                        options.ssl_mode(mode.parse().map_err(|_| {
                            Error::validation("유효하지 않은 MySQL TLS 모드입니다.")
                        })?);
                }
            }
            if let Ok(ca) = std::env::var("DATABASE_SSL_CA") {
                options = options.ssl_ca(ca).ssl_mode(MySqlSslMode::VerifyIdentity);
            }
            Some(
                MySqlPoolOptions::new()
                    .max_connections(6)
                    .acquire_timeout(Timeout::from_secs(3))
                    .connect_lazy_with(options),
            )
        } else {
            None
        };
        let fixtures = if let Ok(path) = std::env::var("BACKTEST_FIXTURE_FILE") {
            if env("DEBUG", "false") != "true" {
                return Err(Error::validation(
                    "합성 시세는 DEBUG=true에서만 사용할 수 있습니다.",
                ));
            }
            let bytes = std::fs::read(path)
                .map_err(|_| Error::validation("합성 시세 파일을 읽을 수 없습니다."))?;
            Some(Arc::new(
                serde_json::from_slice::<Histories>(&bytes)
                    .map_err(|_| Error::validation("합성 시세 파일 형식이 잘못되었습니다."))?,
            ))
        } else {
            None
        };
        Ok(Self {
            pool,
            client,
            yahoo_client,
            fixtures,
            cache: Arc::default(),
        })
    }
    pub async fn history(&self, symbol: &str, start: NaiveDate, end: NaiveDate) -> Result<History> {
        if self.pool.is_none()
            && let Some(fixtures) = &self.fixtures
        {
            let mut h = fixtures
                .get(symbol)
                .cloned()
                .ok_or_else(|| Error(404, format!("가격 데이터가 없습니다: {symbol}")))?;
            h.bars.retain(|b| b.date >= start && b.date <= end);
            validate_prices(&h)?;
            return Ok(h);
        }
        let key = (symbol.to_owned(), start, end);
        if let Some((time, h)) = self.cache.lock().await.get(&key)
            && time.elapsed() < Timeout::from_secs(300)
        {
            return Ok(h.clone());
        }
        let cached = self.cached(symbol, start, end).await.unwrap_or(None);
        // A DB entry is one complete provider snapshot, never a union of
        // independently adjusted date ranges. cached() checks coverage and age.
        let history = if let Some(history) = cached {
            history
        } else {
            let mut h = self.yahoo(symbol, start, end).await?;
            validate_prices(&h)?;
            h.bars.retain(|b| b.date >= start && b.date <= end);
            if h.bars.is_empty() {
                return Err(Error(404, format!("가격 데이터가 없습니다: {symbol}")));
            }
            if let Err(error) = self.save(&h, start, end).await {
                tracing::warn!(%error,"price cache write failed");
            }
            // Provider precision is authoritative even if a cache write fails.
            h
        };
        let mut cache = self.cache.lock().await;
        if cache.len() >= 128 {
            cache.retain(|_, (time, _)| time.elapsed() < Timeout::from_secs(300));
            if cache.len() >= 128
                && let Some(k) = cache.keys().next().cloned()
            {
                cache.remove(&k);
            }
        }
        cache.retain(|(cached_symbol, _, _), _| cached_symbol != symbol);
        cache.insert(key, (Instant::now(), history.clone()));
        Ok(history)
    }
    async fn cached(
        &self,
        symbol: &str,
        start: NaiveDate,
        end: NaiveDate,
    ) -> std::result::Result<Option<History>, sqlx::Error> {
        let Some(pool) = &self.pool else {
            return Ok(None);
        };
        // Both SELECTs must observe the same provider snapshot even when another
        // request atomically replaces this ticker's rows in between them.
        let mut connection = pool.acquire().await?;
        sqlx::query("SET TRANSACTION ISOLATION LEVEL REPEATABLE READ, READ ONLY")
            .execute(&mut *connection)
            .await?;
        let mut transaction = connection.begin().await?;
        let stock = sqlx::query("SELECT id,name,exchange,info_json,TIMESTAMPDIFF(SECOND,data_last_update,UTC_TIMESTAMP()) AS age FROM stocks WHERE ticker=?")
            .bind(symbol)
            .fetch_optional(&mut *transaction)
            .await?;
        let Some(stock) = stock else { return Ok(None) };
        let info: Option<Value> = stock.try_get("info_json")?;
        let info = info.unwrap_or(json!({}));
        if symbol.ends_with("=X") && info["rust_chart_date_version"] != 2 {
            return Ok(None);
        }
        let age: Option<i64> = stock.try_get("age")?;
        let snapshot = &info["rust_price_snapshot"];
        if snapshot["version"] != PRICE_SNAPSHOT_VERSION
            || age.is_none_or(|seconds| !(0..3600).contains(&seconds))
            || snapshot["start"]
                .as_str()
                .is_none_or(|s| s > start.to_string().as_str())
            || snapshot["end"]
                .as_str()
                .is_none_or(|s| s < end.to_string().as_str())
        {
            return Ok(None);
        }
        // Read the complete snapshot to detect removed or suspect cache rows.
        let rows=sqlx::query("SELECT date,CAST(open AS DOUBLE) AS o,CAST(high AS DOUBLE) AS h,CAST(low AS DOUBLE) AS l,CAST(close AS DOUBLE) AS c,CAST(volume AS DOUBLE) AS v,data_quality FROM daily_prices WHERE stock_id=? ORDER BY date").bind(stock.try_get::<i32,_>("id")?).fetch_all(&mut *transaction).await?;
        transaction.commit().await?;
        if Some(rows.len() as u64) != snapshot["rows"].as_u64()
            || rows.iter().any(|r| {
                !r.try_get::<String, _>("data_quality")
                    .is_ok_and(|q| q == "good")
                    || r.try_get::<f64, _>("c")
                        .is_ok_and(|price| !price.is_finite() || price <= 0.0)
            })
        {
            return Ok(None);
        }
        let mut bars: Vec<Bar> = rows
            .iter()
            .map(|r| {
                Ok(Bar {
                    date: r.try_get("date")?,
                    open: r.try_get("o")?,
                    high: r.try_get("h")?,
                    low: r.try_get("l")?,
                    close: r.try_get("c")?,
                    volume: r.try_get("v")?,
                })
            })
            .collect::<std::result::Result<_, sqlx::Error>>()?;
        if bars.iter().any(|b| !valid_quote(symbol, b)) {
            return Ok(None);
        }
        bars.retain(|b| b.date >= start && b.date <= end);
        if bars.is_empty() {
            return Ok(None);
        }
        Ok(Some(History {
            symbol: symbol.into(),
            currency: info["currency"].as_str().unwrap_or("").into(),
            company_name: stock
                .try_get::<Option<String>, _>("name")?
                .unwrap_or_else(|| symbol.into()),
            exchange: stock
                .try_get::<Option<String>, _>("exchange")?
                .unwrap_or_default(),
            first_trade_date: listing_date(&info),
            bars,
        }))
    }
    async fn yahoo(&self, symbol: &str, start: NaiveDate, end: NaiveDate) -> Result<History> {
        if let Some(fixtures) = &self.fixtures {
            return fixtures
                .get(symbol)
                .cloned()
                .ok_or_else(|| Error(404, format!("가격 데이터가 없습니다: {symbol}")));
        }
        let (start, end) = yahoo_request_bounds(start, end)?;
        let fetch = async {
            for attempt in 0..3 {
                match self
                    .yahoo_client
                    .get_quote_history(symbol, start, end)
                    .await
                {
                    Ok(response) => return parse_yahoo_response(symbol, response),
                    // The library retries empty/HTML/5xx responses itself. Only
                    // transport failures need an additional bounded retry here.
                    Err(YahooError::ConnectionFailed(_)) if attempt < 2 => {
                        tokio::time::sleep(Timeout::from_millis(250 * (attempt + 1))).await;
                    }
                    Err(error) => return Err(yahoo_error(symbol, error)),
                }
            }
            unreachable!("the final attempt returns")
        };
        tokio::time::timeout(Timeout::from_secs(45), fetch)
            .await
            .map_err(|_| {
                Error::unavailable(format!("{symbol}: 시세 조회 시간이 초과되었습니다."))
            })?
    }
    async fn save(
        &self,
        h: &History,
        start: NaiveDate,
        end: NaiveDate,
    ) -> std::result::Result<(), sqlx::Error> {
        let Some(pool) = &self.pool else {
            return Ok(());
        };
        let mut tx = pool.begin().await?;
        // Serialize cache repair with concurrent refreshes of this ticker.
        let prior = sqlx::query("SELECT id,info_json FROM stocks WHERE ticker=? FOR UPDATE")
            .bind(&h.symbol)
            .fetch_optional(&mut *tx)
            .await?;
        if let Some(prior) = prior {
            sqlx::query("DELETE FROM daily_prices WHERE stock_id=?")
                .bind(prior.try_get::<i32, _>("id")?)
                .execute(&mut *tx)
                .await?;
        }
        let info = json!({"currency":h.currency,"symbol":h.symbol,"shortName":h.company_name,"exchange":h.exchange,"rust_chart_date_version":2,"rust_price_snapshot":{"version":PRICE_SNAPSHOT_VERSION,"start":start,"end":end,"rows":h.bars.len()},"firstTradeDateEpochUtc":h.first_trade_date.map(|d|d.and_hms_opt(0,0,0).unwrap().and_utc().timestamp())});
        sqlx::query("INSERT INTO stocks(ticker,name,exchange,info_json,last_info_update,data_last_update) VALUES(?,?,?,?,UTC_TIMESTAMP(),UTC_TIMESTAMP()) ON DUPLICATE KEY UPDATE name=VALUES(name),exchange=VALUES(exchange),info_json=JSON_MERGE_PATCH(COALESCE(info_json,JSON_OBJECT()),VALUES(info_json)),last_info_update=UTC_TIMESTAMP(),data_last_update=UTC_TIMESTAMP()")
            .bind(&h.symbol).bind(&h.company_name).bind(&h.exchange).bind(&info).execute(&mut *tx).await?;
        let id: i32 = sqlx::query_scalar("SELECT id FROM stocks WHERE ticker=?")
            .bind(&h.symbol)
            .fetch_one(&mut *tx)
            .await?;
        for b in &h.bars {
            sqlx::query("INSERT INTO daily_prices(stock_id,date,open,high,low,close,adj_close,volume) VALUES(?,?,?,?,?,?,?,?) ON DUPLICATE KEY UPDATE open=VALUES(open),high=VALUES(high),low=VALUES(low),close=VALUES(close),adj_close=VALUES(adj_close),volume=VALUES(volume)")
                .bind(id).bind(b.date).bind(b.open).bind(b.high).bind(b.low).bind(b.close).bind(b.close).bind(b.volume.max(0.0) as u64).execute(&mut *tx).await?;
        }
        tx.commit().await
    }
    pub async fn load(&self, req: &BacktestRequest) -> Result<Histories> {
        let symbols: Vec<String> = req
            .portfolio
            .iter()
            .filter(|a| !a.cash())
            .map(|a| a.symbol.clone())
            .collect();
        let start = req.start_date;
        let end = req.end_date;
        let tasks: Vec<_> = symbols
            .into_iter()
            .map(|symbol| {
                let source = self.clone();
                async move {
                    let result = source.history(&symbol, start, end).await;
                    (symbol, result)
                }
            })
            .collect();
        let results = stream::iter(tasks)
            .buffer_unordered(4)
            .collect::<Vec<_>>()
            .await;
        let mut data = Histories::new();
        for (symbol, result) in results {
            match result {
                Ok(h) => {
                    // Python starts at the first available session, including IPOs
                    // after the requested start date.
                    if !h.bars.is_empty() {
                        data.insert(symbol, h);
                    }
                }
                Err(e) if e.0 == 404 => {}
                Err(e) => return Err(e),
            }
        }
        let currencies: std::collections::BTreeSet<_> = data
            .values()
            .map(|h| h.currency.clone())
            .filter(|c| c != "USD")
            .collect();
        for c in currencies {
            let (ticker, _) = engine::fx_ticker(&c).ok_or_else(|| {
                Error::validation(format!("지원하지 않거나 확인할 수 없는 통화: {c}"))
            })?;
            let history = self
                .history(ticker, req.start_date - Duration::days(60), req.end_date)
                .await?;
            data.insert(ticker.into(), history);
        }
        Ok(data)
    }
    pub async fn news(&self, symbol: &str, limit: usize) -> Result<Vec<Value>> {
        if let Some(pool) = &self.pool
            && let Ok(rows)=sqlx::query("SELECT title,link,description,news_date FROM stock_news WHERE ticker=? AND created_at>UTC_TIMESTAMP()-INTERVAL 3 HOUR ORDER BY news_date DESC LIMIT ?").bind(symbol).bind(limit as u32).fetch_all(pool).await
                && !rows.is_empty(){return rows.iter().map(|r|Ok(json!({"title":r.try_get::<String,_>("title").unwrap_or_default(),"link":r.try_get::<Option<String>,_>("link").unwrap_or_default(),"description":r.try_get::<Option<String>,_>("description").unwrap_or_default(),"pubDate":r.try_get::<NaiveDate,_>("news_date").ok(),"company":symbol}))).collect();}
        if self.fixtures.is_some() {
            return Ok(vec![]);
        }
        let id = env("NAVER_CLIENT_ID", "");
        let secret = env("NAVER_CLIENT_SECRET", "");
        if id.is_empty() || secret.is_empty() {
            return Ok(vec![]);
        }
        let response = self
            .client
            .get("https://openapi.naver.com/v1/search/news.json")
            .header("X-Naver-Client-Id", id)
            .header("X-Naver-Client-Secret", secret)
            .query(&[
                ("query", crate::news::query(symbol).as_str()),
                ("display", &limit.to_string()),
                ("sort", "date"),
            ])
            .send()
            .await
            .map_err(|_| Error::unavailable("뉴스 조회 실패"))?
            .error_for_status()
            .map_err(|_| Error::unavailable("뉴스 조회 실패"))?;
        let value: Value = response
            .json()
            .await
            .map_err(|_| Error::unavailable("뉴스 응답 형식 오류"))?;
        let mut items: Vec<_> = value["items"]
            .as_array()
            .into_iter()
            .flatten()
            .filter_map(crate::news::normalize)
            .collect();
        items.truncate(limit);
        if let Some(pool) = &self.pool {
            for item in &items {
                let date = item["pubDate"]
                    .as_str()
                    .and_then(|s| DateTime::parse_from_rfc2822(s).ok())
                    .map(|d| d.date_naive())
                    .unwrap_or_else(|| Utc::now().date_naive());
                let _=sqlx::query("INSERT INTO stock_news(ticker,news_date,title,link,description,source) VALUES(?,?,?,?,?,'naver') ON DUPLICATE KEY UPDATE title=VALUES(title),description=VALUES(description),created_at=UTC_TIMESTAMP()")
                .bind(symbol).bind(date).bind(item["title"].as_str().unwrap_or("")).bind(item["link"].as_str().unwrap_or("")).bind(item["description"].as_str().unwrap_or("")).execute(pool).await;
            }
        }
        Ok(items)
    }
}
fn listing_date(info: &Value) -> Option<NaiveDate> {
    info["first_trade_date"]
        .as_str()
        .and_then(|s| s.parse().ok())
        .or_else(|| {
            info["firstTradeDateEpochUtc"]
                .as_i64()
                .and_then(|t| DateTime::from_timestamp(t, 0))
                .map(|d| d.date_naive())
        })
}

fn yahoo_request_bounds(
    start: NaiveDate,
    end: NaiveDate,
) -> Result<(
    yahoo_finance_api::time::OffsetDateTime,
    yahoo_finance_api::time::OffsetDateTime,
)> {
    let bound = |date: NaiveDate, padding| {
        let timestamp = date
            .checked_add_signed(Duration::days(padding))
            .and_then(|date| date.and_hms_opt(0, 0, 0))
            .ok_or_else(|| Error::validation("시세 요청 날짜가 범위를 벗어났습니다."))?
            .and_utc()
            .timestamp();
        yahoo_finance_api::time::OffsetDateTime::from_unix_timestamp(timestamp)
            .map_err(|_| Error::validation("시세 요청 날짜가 범위를 벗어났습니다."))
    };
    // Yahoo's end bound is exclusive. Padding covers local exchange dates on
    // either side of UTC; history() then retains the inclusive requested dates.
    Ok((bound(start, -1)?, bound(end, 2)?))
}

fn yahoo_error(symbol: &str, error: YahooError) -> Error {
    let not_found = match &error {
        YahooError::NoResult | YahooError::NoQuotes => true,
        YahooError::FetchFailed(message) => message.starts_with("404,"),
        YahooError::ApiError(message) => message.code.as_deref() == Some("Not Found"),
        _ => false,
    };
    if not_found {
        Error(404, format!("가격 데이터가 없습니다: {symbol}"))
    } else {
        tracing::warn!(%symbol, %error, "Yahoo library request failed");
        Error::unavailable(format!(
            "{symbol}: 시세 제공업체의 응답을 사용할 수 없습니다."
        ))
    }
}

fn parse_yahoo_response(symbol: &str, response: YResponse) -> Result<History> {
    if let Some(error) = &response.chart.error {
        return Err(yahoo_error(symbol, YahooError::ApiError(error.clone())));
    }
    // Validate array alignment through the library before our financial
    // normalization. quotes() alone turns a missing adjclose into zero, so
    // retain the structured response's nulls to distinguish missing from an
    // explicitly invalid zero. Never apply a dividend/split adjustment twice.
    response
        .quotes()
        .map_err(|error| yahoo_error(symbol, error))?;
    let value = serde_json::to_value(response)
        .map_err(|_| Error::unavailable("시세 응답을 변환할 수 없습니다."))?;
    parse_chart(symbol, value)
}

pub fn parse_chart(symbol: &str, value: Value) -> Result<History> {
    let r = &value["chart"]["result"][0];
    let meta = &r["meta"];
    let timestamps = r["timestamp"]
        .as_array()
        .ok_or_else(|| Error(404, format!("가격 데이터가 없습니다: {symbol}")))?;
    let quote = &r["indicators"]["quote"][0];
    let zone = meta["exchangeTimezoneName"]
        .as_str()
        .filter(|name| !name.is_empty())
        .map(jiff::tz::TimeZone::get)
        .transpose()
        .map_err(|_| Error::unavailable("시세의 거래소 시간대를 확인할 수 없습니다."))?;
    let offset = meta["gmtoffset"].as_i64().unwrap_or(0);
    let mut bars = Vec::new();
    for (i, t) in timestamps.iter().enumerate() {
        let Some(date) = t.as_i64().and_then(|t| {
            if let Some(zone) = &zone {
                let d = jiff::Timestamp::from_second(t)
                    .ok()?
                    .to_zoned(zone.clone())
                    .date();
                NaiveDate::from_ymd_opt(i32::from(d.year()), d.month() as u32, d.day() as u32)
            } else {
                // Legacy fixture/provider responses without an IANA zone.
                DateTime::from_timestamp(t.checked_add(offset)?, 0).map(|d| d.date_naive())
            }
        }) else {
            continue;
        };
        let fields = ["open", "high", "low", "close"];
        // A wholly absent non-trading bar is different from a partial or
        // contradictory observation. Never silently shorten an indicator window.
        if fields.iter().all(|k| quote[k][i].is_null()) {
            continue;
        }
        let values: Option<Vec<f64>> = fields
            .iter()
            .map(|k| quote[k][i].as_f64().filter(|v| v.is_finite() && *v > 0.0))
            .collect();
        let v = values
            .ok_or_else(|| Error::unavailable("불완전하거나 유효하지 않은 OHLC 시세입니다."))?;
        let raw = Bar {
            date,
            open: v[0],
            high: v[1],
            low: v[2],
            close: v[3],
            volume: 0.0,
        };
        if !valid_quote(symbol, &raw) {
            return Err(Error::unavailable("시세의 OHLC 범위가 일치하지 않습니다."));
        }
        {
            // A stock's adjusted series must have one consistent price basis.
            // FX has no corporate actions, so missing adjustment is identity.
            let adjusted = r["indicators"]["adjclose"][0]["adjclose"][i]
                .as_f64()
                .or_else(|| symbol.ends_with("=X").then_some(v[3]))
                .ok_or_else(|| {
                    Error::unavailable(
                        "수정 종가가 누락되어 일관된 가격 기준을 확인할 수 없습니다.",
                    )
                })?;
            let ratio = adjusted / v[3];
            if !ratio.is_finite() || ratio <= 0.0 {
                return Err(Error::unavailable("유효하지 않은 수정 주가입니다."));
            }
            if v[..3].iter().any(|price| {
                let adjusted = price * ratio;
                !adjusted.is_finite() || adjusted <= 0.0
            }) {
                return Err(Error::unavailable("수정 주가가 수치 범위를 벗어났습니다."));
            }
            let bar = Bar {
                date,
                open: v[0] * ratio,
                high: v[1] * ratio,
                low: v[2] * ratio,
                close: adjusted,
                volume: quote["volume"][i].as_f64().unwrap_or(0.0),
            };
            if !valid_quote(symbol, &bar) {
                return Err(Error::unavailable("유효하지 않은 수정 OHLC 시세입니다."));
            }
            bars.push(bar);
        }
    }
    bars.sort_by_key(|b| b.date);
    bars.dedup_by_key(|b| b.date);
    Ok(History {
        symbol: symbol.into(),
        currency: meta["currency"].as_str().unwrap_or("").into(),
        company_name: meta["longName"]
            .as_str()
            .or(meta["shortName"].as_str())
            .unwrap_or(symbol)
            .into(),
        exchange: meta["exchangeName"].as_str().unwrap_or("").into(),
        first_trade_date: meta["firstTradeDate"]
            .as_i64()
            .and_then(|t| DateTime::from_timestamp(t, 0))
            .map(|d| d.date_naive()),
        bars,
    })
}

#[cfg(test)]
mod mysql_tests {
    use super::*;

    #[tokio::test]
    #[ignore = "requires a disposable MySQL; RUST_TEST_DATABASE=1"]
    async fn precision_and_snapshot_refresh_preserve_economic_value() {
        assert_eq!(std::env::var("RUST_TEST_DATABASE").as_deref(), Ok("1"));
        let mut source = DataSource::new().unwrap();
        let first: NaiveDate = "2023-01-02".parse().unwrap();
        let last: NaiveDate = "2023-02-10".parse().unwrap();
        let make = |symbol: &str, a: f64, b: f64| History {
            symbol: symbol.into(),
            currency: "USD".into(),
            company_name: symbol.into(),
            exchange: "test".into(),
            first_trade_date: None,
            bars: [(first, a), (last, b)]
                .into_iter()
                .map(|(date, p)| Bar {
                    date,
                    open: p,
                    high: p,
                    low: p,
                    close: p,
                    volume: 1e6,
                })
                .collect(),
        };
        let tiny = make("ZZTINY", 0.00001, 0.00003);
        source.save(&tiny, first, last).await.unwrap();
        let cached = source.cached("ZZTINY", first, last).await.unwrap().unwrap();
        assert!((cached.bars[0].close - 0.00001).abs() < 1e-18);
        assert!((cached.bars[1].close - 0.00003).abs() < 1e-18);
        let req: BacktestRequest = serde_json::from_value(json!({"portfolio":[{"symbol":"ZZTINY","amount":10000}],"start_date":first,"end_date":last,"commission":0,"rebalance_frequency":"none"})).unwrap();
        let data = Histories::from([("ZZTINY".into(), cached)]);
        let result = engine::run(&req, &data, &tokio_util::sync::CancellationToken::new()).unwrap();
        assert!(
            (result["data"]["portfolio_statistics"]["Final_Value"]
                .as_f64()
                .unwrap()
                - 30000.0)
                .abs()
                < 1e-7
        );

        let stale = make("ZZSPLIT", 100.0, 50.0);
        let adjusted = make("ZZSPLIT", 50.0, 50.0);
        source.fixtures = Some(Arc::new(Histories::from([(
            "ZZSPLIT".into(),
            adjusted.clone(),
        )])));
        source.save(&stale, first, last).await.unwrap();
        let pool = source.pool.as_ref().unwrap();
        sqlx::query("UPDATE stocks SET data_last_update='2023-02-11' WHERE ticker='ZZSPLIT'")
            .execute(pool)
            .await
            .unwrap();
        let refreshed = source.history("ZZSPLIT", first, last).await.unwrap();
        assert_eq!(refreshed.bars[0].close, 50.0);
        assert_eq!(refreshed.bars[1].close, 50.0);
        let mut partial = adjusted.clone();
        partial.bars.remove(0);
        source.save(&partial, last, last).await.unwrap();
        assert!(
            source
                .cached("ZZSPLIT", first, last)
                .await
                .unwrap()
                .is_none(),
            "partial refresh cannot be merged with older adjustment cohorts"
        );
        source.cache.lock().await.clear();
        let full = source.history("ZZSPLIT", first, last).await.unwrap();
        assert_eq!(full.bars.len(), 2);
        assert!(full.bars.iter().all(|b| b.close == 50.0));
        sqlx::query("UPDATE daily_prices p JOIN stocks s ON p.stock_id=s.id SET p.data_quality='suspicious' WHERE s.ticker='ZZSPLIT'").execute(pool).await.unwrap();
        assert!(
            source
                .cached("ZZSPLIT", first, last)
                .await
                .unwrap()
                .is_none()
        );
        source.cache.lock().await.clear();
        source.history("ZZSPLIT", first, last).await.unwrap();
        assert!(
            source
                .cached("ZZSPLIT", first, last)
                .await
                .unwrap()
                .is_some()
        );
    }

    #[tokio::test]
    #[ignore = "requires a disposable MySQL with schema.sql; RUST_TEST_DATABASE=1"]
    async fn mysql_cache_roundtrip_and_transaction_rollback() {
        assert_eq!(std::env::var("RUST_TEST_DATABASE").as_deref(), Ok("1"));
        let source = DataSource::new().unwrap();
        let mut history: History =
            serde_json::from_str::<Histories>(include_str!("../tests/fixtures/histories.json"))
                .unwrap()
                .remove("AAPL")
                .unwrap();
        history.symbol = "ZZRUST".into();
        source
            .save(
                &history,
                history.bars[0].date,
                history.bars.last().unwrap().date,
            )
            .await
            .unwrap();
        let first = history.bars[0].date;
        let last = history.bars.last().unwrap().date;
        let cached = source.cached("ZZRUST", first, last).await.unwrap().unwrap();
        assert_eq!(cached.currency, "USD");
        assert_eq!(cached.bars.len(), history.bars.len());
        for (a, b) in cached.bars.iter().zip(&history.bars) {
            assert!((a.close - b.close).abs() <= 0.0001);
        }
        history.first_trade_date = Some(first);
        source
            .save(
                &history,
                history.bars[0].date,
                history.bars.last().unwrap().date,
            )
            .await
            .unwrap();
        assert_eq!(
            source
                .cached("ZZRUST", first, last)
                .await
                .unwrap()
                .unwrap()
                .first_trade_date,
            Some(first)
        );
        // A version-1 FX cache may contain shifted Sunday rows. Repair only
        // that ticker, and do not mark it corrected if any insert rolls back.
        let mut fx = history.clone();
        fx.symbol = "ZZFX=X".into();
        source
            .save(&fx, fx.bars[0].date, fx.bars.last().unwrap().date)
            .await
            .unwrap();
        let pool = source.pool.as_ref().unwrap();
        sqlx::query("UPDATE stocks SET info_json=JSON_REMOVE(info_json,'$.rust_chart_date_version') WHERE ticker='ZZFX=X'").execute(pool).await.unwrap();
        assert!(
            source
                .cached("ZZFX=X", first, last)
                .await
                .unwrap()
                .is_none()
        );
        let mut invalid = fx.clone();
        invalid.bars[0].close = -1.0;
        assert!(
            source
                .save(
                    &invalid,
                    invalid.bars[0].date,
                    invalid.bars.last().unwrap().date
                )
                .await
                .is_err()
        );
        let count:i64=sqlx::query_scalar("SELECT COUNT(*) FROM daily_prices p JOIN stocks s ON s.id=p.stock_id WHERE s.ticker='ZZFX=X'").fetch_one(pool).await.unwrap();
        assert_eq!(
            count,
            fx.bars.len() as i64,
            "failed FX repair must preserve old rows"
        );
        let mut corrected = fx.clone();
        corrected.bars.remove(0);
        source.save(&corrected, first, last).await.unwrap();
        let repaired = source.cached("ZZFX=X", first, last).await.unwrap().unwrap();
        assert_eq!(
            repaired.bars.len(),
            corrected.bars.len(),
            "obsolete dates must be removed"
        );
        // The public path must work from a complete cache without Yahoo.
        assert_eq!(
            source
                .history("ZZRUST", first, last)
                .await
                .unwrap()
                .bars
                .len(),
            history.bars.len()
        );
        history.symbol = "ZZFAIL".into();
        history.bars[0].close = -1.0;
        assert!(
            source
                .save(
                    &history,
                    history.bars[0].date,
                    history.bars.last().unwrap().date
                )
                .await
                .is_err()
        );
        let count: i64 = sqlx::query_scalar("SELECT COUNT(*) FROM stocks WHERE ticker='ZZFAIL'")
            .fetch_one(source.pool.as_ref().unwrap())
            .await
            .unwrap();
        assert_eq!(
            count, 0,
            "failed child insert must roll back the parent row"
        );
    }
}
