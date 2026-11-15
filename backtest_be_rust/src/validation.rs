//! HTTP validation compatibility with the retained FastAPI/Pydantic contract.
use crate::{error::Error, model::BacktestRequest, schedule};
use axum::{
    Json,
    http::StatusCode,
    response::{IntoResponse, Response},
};
use chrono::{NaiveDate, Utc};
use serde_json::{Value, json};
use std::collections::BTreeSet;

#[derive(Debug)]
pub enum ApiError {
    Application(Error),
    Validation(Vec<Value>),
}
impl From<Error> for ApiError {
    fn from(e: Error) -> Self {
        Self::Application(e)
    }
}
impl IntoResponse for ApiError {
    fn into_response(self) -> Response {
        match self {
            Self::Application(e) => e.into_response(),
            Self::Validation(errors) => (
                StatusCode::UNPROCESSABLE_ENTITY,
                Json(json!({"detail":errors})),
            )
                .into_response(),
        }
    }
}
fn field(
    kind: &str,
    loc: Value,
    msg: impl Into<String>,
    input: &Value,
    ctx: Option<Value>,
) -> Value {
    let mut e = json!({"type":kind,"loc":loc,"msg":msg.into(),"input":input});
    if let Some(ctx) = ctx {
        e["ctx"] = ctx;
    }
    e
}
fn value_error(loc: Value, msg: impl Into<String>, input: &Value) -> Value {
    field(
        "value_error",
        loc,
        format!("Value error, {}", msg.into()),
        input,
        Some(json!({"error":{}})),
    )
}
fn number(v: &Value) -> Option<f64> {
    match v {
        Value::Bool(b) => Some(if *b { 1.0 } else { 0.0 }),
        Value::String(s) => s.trim().parse().ok(),
        _ => v.as_f64(),
    }
}
const STRATEGIES: &str = "bollinger_strategy, buy_hold_strategy, ema_strategy, macd_strategy, rsi_strategy, sma_strategy";
const FREQUENCIES: &str =
    "weekly_1, weekly_2, monthly_1, monthly_2, monthly_3, monthly_6, monthly_12";

pub fn backtest(raw: Value, min_days: i64) -> Result<BacktestRequest, ApiError> {
    if !raw.is_object() {
        return Err(ApiError::Validation(vec![field(
            "model_attributes_type",
            json!(["body"]),
            "Input should be a valid dictionary or object to extract fields from",
            &raw,
            None,
        )]));
    }
    let mut errors = vec![];
    let mut normalized = raw.clone();
    if let Some(items) = raw["portfolio"].as_array() {
        let mut assets_ok = true;
        for (i, item) in items.iter().enumerate() {
            let before = errors.len();
            match item["symbol"].as_str() {
                Some(s) if s.is_empty() || s.chars().count() > 10 => {
                    let (kind, msg, key, n) = if s.is_empty() {
                        (
                            "string_too_short",
                            "String should have at least 1 character",
                            "min_length",
                            1,
                        )
                    } else {
                        (
                            "string_too_long",
                            "String should have at most 10 characters",
                            "max_length",
                            10,
                        )
                    };
                    errors.push(field(
                        kind,
                        json!(["body", "portfolio", i, "symbol"]),
                        msg,
                        &item["symbol"],
                        Some(json!({key:n})),
                    ));
                }
                Some(s)
                    if item["asset_type"] != "cash"
                        && !s
                            .bytes()
                            .all(|b| b.is_ascii_alphanumeric() || b == b'.' || b == b'-') =>
                {
                    errors.push(value_error(
                        json!(["body", "portfolio", i]),
                        "주식 심볼은 영문자, 숫자, 점(.), 하이픈(-)만 포함해야 합니다.",
                        item,
                    ))
                }
                None => errors.push(field(
                    if item.get("symbol").is_none() {
                        "missing"
                    } else {
                        "string_type"
                    },
                    json!(["body", "portfolio", i, "symbol"]),
                    if item.get("symbol").is_none() {
                        "Field required"
                    } else {
                        "Input should be a valid string"
                    },
                    item.get("symbol").unwrap_or(item),
                    None,
                )),
                _ => {}
            }
            for key in ["amount", "weight"] {
                if let Some(v) = item.get(key).filter(|v| !v.is_null()) {
                    match number(v) {
                        Some(n) if n.is_finite() => {
                            normalized["portfolio"][i][key] = json!(n);
                            let rule = if key == "amount" && n <= 0.0 {
                                Some((
                                    "greater_than",
                                    "Input should be greater than 0",
                                    json!({"gt":0.0}),
                                ))
                            } else if key == "weight" && n < 0.0 {
                                Some((
                                    "greater_than_equal",
                                    "Input should be greater than or equal to 0",
                                    json!({"ge":0.0}),
                                ))
                            } else if key == "weight" && n > 100.0 {
                                Some((
                                    "less_than_equal",
                                    "Input should be less than or equal to 100",
                                    json!({"le":100.0}),
                                ))
                            } else {
                                None
                            };
                            if let Some((kind, msg, ctx)) = rule {
                                errors.push(field(
                                    kind,
                                    json!(["body", "portfolio", i, key]),
                                    msg,
                                    v,
                                    Some(ctx),
                                ));
                            }
                        }
                        _ => errors.push(field(
                            "float_parsing",
                            json!(["body", "portfolio", i, key]),
                            "Input should be a valid number, unable to parse string as a number",
                            v,
                            None,
                        )),
                    }
                }
            }
            for (key, allowed, msg) in [
                (
                    "investment_type",
                    vec!["lump_sum", "dca"],
                    "투자 방식은 lump_sum 또는 dca만 가능합니다.".to_string(),
                ),
                (
                    "asset_type",
                    vec!["stock", "cash"],
                    "자산 타입은 stock 또는 cash만 가능합니다.".to_string(),
                ),
                (
                    "dca_frequency",
                    FREQUENCIES.split(", ").collect(),
                    format!("DCA 주기는 {FREQUENCIES} 중 하나여야 합니다."),
                ),
            ] {
                if let Some(v) = item.get(key)
                    && !v.as_str().is_some_and(|s| allowed.contains(&s))
                {
                    errors.push(value_error(json!(["body", "portfolio", i, key]), msg, v));
                }
            }
            assets_ok &= errors.len() == before;
        }
        if assets_ok {
            if items.is_empty() || items.len() > 20 {
                let (kind, msg, ctx) = if items.is_empty() {
                    (
                        "too_short",
                        "List should have at least 1 item after validation, not 0".into(),
                        json!({"field_type":"List","min_length":1,"actual_length":0}),
                    )
                } else {
                    (
                        "too_long",
                        format!(
                            "List should have at most 20 items after validation, not {}",
                            items.len()
                        ),
                        json!({"field_type":"List","max_length":20,"actual_length":items.len()}),
                    )
                };
                errors.push(field(
                    kind,
                    json!(["body", "portfolio"]),
                    msg,
                    &raw["portfolio"],
                    Some(ctx),
                ));
            } else {
                let mut seen = BTreeSet::new();
                let mut duplicates = BTreeSet::new();
                for item in items {
                    if item["asset_type"] != "cash" {
                        let s = item["symbol"].as_str().unwrap().to_uppercase();
                        if !seen.insert(s.clone()) {
                            duplicates.insert(s);
                        }
                    }
                }
                let has_amount = items.iter().any(|i| !i["amount"].is_null());
                let has_weight = items.iter().any(|i| !i["weight"].is_null());
                let total: f64 = items
                    .iter()
                    .map(|i| {
                        number(&i[if has_weight { "weight" } else { "amount" }]).unwrap_or(0.0)
                    })
                    .sum();
                let message = if !duplicates.is_empty() {
                    Some(format!(
                        "중복된 종목이 있습니다: {}. 같은 종목은 한 번만 추가할 수 있습니다.",
                        duplicates.into_iter().collect::<Vec<_>>().join(", ")
                    ))
                } else if has_amount && has_weight {
                    Some("포트폴리오 내 모든 종목은 amount 또는 weight 중 하나만 입력해야 합니다. 혼합 입력 불가.".into())
                } else if has_weight && !(95.0..=105.0).contains(&total) {
                    Some(format!(
                        "종목 비중 합계가 95-105% 범위를 벗어났습니다. 현재: {total:.1}%"
                    ))
                } else if !has_weight && total <= 0.0 {
                    Some("총 투자 금액은 0보다 커야 합니다.".into())
                } else {
                    None
                };
                if let Some(msg) = message {
                    errors.push(value_error(
                        json!(["body", "portfolio"]),
                        msg,
                        &raw["portfolio"],
                    ));
                }
            }
        }
    } else {
        errors.push(field(
            if raw.get("portfolio").is_none() {
                "missing"
            } else {
                "list_type"
            },
            json!(["body", "portfolio"]),
            if raw.get("portfolio").is_none() {
                "Field required"
            } else {
                "Input should be a valid list"
            },
            raw.get("portfolio").unwrap_or(&raw),
            None,
        ));
    }
    let mut dates = [None, None];
    for (i, key) in ["start_date", "end_date"].into_iter().enumerate() {
        if raw.get(key).is_none() {
            errors.push(field(
                "missing",
                json!(["body", key]),
                "Field required",
                &raw,
                None,
            ));
            continue;
        }
        dates[i] = raw[key]
            .as_str()
            .and_then(|s| NaiveDate::parse_from_str(s, "%Y-%m-%d").ok());
        if dates[i].is_none() {
            errors.push(value_error(
                json!(["body", key]),
                "날짜는 YYYY-MM-DD 형식이어야 합니다.",
                &raw[key],
            ));
        }
    }
    if let Some(end) = dates[1] {
        let today = Utc::now().date_naive();
        let msg = if end > today {
            Some(format!(
                "종료 날짜는 미래일 수 없습니다: {end} (오늘: {today})"
            ))
        } else if let Some(start) = dates[0] {
            if end <= start {
                Some("종료 날짜는 시작 날짜보다 이후여야 합니다.".into())
            } else if (end - start).num_days() > 3650 {
                Some("백테스트 기간은 최대 10년으로 제한됩니다.".into())
            } else {
                None
            }
        } else {
            None
        };
        if let Some(msg) = msg {
            errors.push(value_error(
                json!(["body", "end_date"]),
                msg,
                &raw["end_date"],
            ));
        }
    }
    if let Some(v) = raw.get("commission") {
        if let Some(n) = number(v).filter(|v| v.is_finite()) {
            normalized["commission"] = json!(n);
            if !(0.0..0.1).contains(&n) {
                errors.push(field(
                    if n < 0.0 {
                        "greater_than_equal"
                    } else {
                        "less_than"
                    },
                    json!(["body", "commission"]),
                    if n < 0.0 {
                        "Input should be greater than or equal to 0"
                    } else {
                        "Input should be less than 0.1"
                    },
                    v,
                    Some(if n < 0.0 {
                        json!({"ge":0.0})
                    } else {
                        json!({"lt":0.1})
                    }),
                ));
            }
        } else {
            errors.push(field(
                "float_type",
                json!(["body", "commission"]),
                "Input should be a valid number",
                v,
                None,
            ));
        }
    }
    if let Some(v) = raw.get("rebalance_frequency") {
        if let Some(s) = v.as_str() {
            if s != "none" && schedule::frequency(s).is_none() {
                errors.push(value_error(json!(["body","rebalance_frequency"]),format!("유효하지 않은 리밸런싱 주기입니다: {s}. 허용된 값: monthly_1, monthly_12, monthly_2, monthly_3, monthly_6, none, weekly_1, weekly_2"),v));
            }
        } else {
            errors.push(field(
                "string_type",
                json!(["body", "rebalance_frequency"]),
                "Input should be a valid string",
                v,
                None,
            ));
        }
    }
    if let Some(v) = raw.get("strategy")
        && !v
            .as_str()
            .is_some_and(|s| STRATEGIES.split(", ").any(|a| a == s))
    {
        errors.push(value_error(
            json!(["body", "strategy"]),
            format!(
                "유효하지 않은 전략입니다: {}. 허용된 값: {STRATEGIES}",
                v.as_str().unwrap_or("")
            ),
            v,
        ));
    }
    if !errors.is_empty() {
        return Err(ApiError::Validation(errors));
    }
    let mut request: BacktestRequest = serde_json::from_value(normalized).map_err(|e| {
        ApiError::Validation(vec![field(
            "value_error",
            json!(["body"]),
            e.to_string(),
            &raw,
            None,
        )])
    })?;
    if !request.buy_hold() {
        let dca: Vec<_> = request
            .portfolio
            .iter()
            .filter(|a| !a.cash() && a.dca())
            .map(|a| a.symbol.to_uppercase())
            .collect();
        let msg = if !dca.is_empty() {
            Some(format!(
                "{}는 분할 매수(DCA)를 지원하지 않습니다 (DCA 종목: {}). DCA는 buy_hold_strategy에서만 사용할 수 있습니다.",
                request.strategy,
                dca.join(", ")
            ))
        } else if let Some(r) = &request.rebalance_frequency
            && r != "none"
        {
            Some(format!(
                "{}는 리밸런싱을 지원하지 않습니다 (rebalance_frequency={r}). rebalance_frequency를 none으로 보내거나 buy_hold_strategy를 사용하세요.",
                request.strategy
            ))
        } else {
            None
        };
        if let Some(msg) = msg {
            return Err(ApiError::Validation(vec![value_error(
                json!(["body"]),
                msg,
                &raw,
            )]));
        }
    }
    let days = (request.end_date - request.start_date).num_days();
    if days < min_days {
        return Err(Error::validation(format!(
            "백테스트 기간이 너무 짧습니다: {days}일 (최소 {min_days}일 필요)"
        ))
        .into());
    }
    request.validate(min_days).map_err(|e| {
        if !request.buy_hold()
            && crate::strategy::parameters(&request.strategy, request.strategy_params.as_ref())
                .is_err()
        {
            ApiError::from(Error::validation(
                "[ValidationError] 모든 종목의 백테스트가 실패했습니다.",
            ))
        } else {
            e.into()
        }
    })?;
    Ok(request)
}

/// Parsed GET query arguments after the Pydantic-compatible checks.
#[derive(Debug, Default)]
pub struct QueryValues {
    pub symbols: Vec<String>,
    pub start: Option<NaiveDate>,
    pub end: Option<NaiveDate>,
    pub limit: usize,
}

fn query_fields(section: &str) -> &'static [&'static str] {
    // PricesQuery(PeriodQuery, SymbolsQuery) collects SymbolsQuery's field first.
    match section {
        "prices" => &["symbols", "start_date", "end_date"],
        "news" => &["symbols", "limit"],
        _ => &["start_date", "end_date"],
    }
}

/// GET query models (`extra='forbid'`): field errors in field order, then extra keys in
/// query order; the period model validator runs only when every field is valid. Repeated
/// scalar keys keep the last value (Starlette); symbols stay a list.
pub fn query(section: &str, raw: Option<&str>) -> Result<QueryValues, ApiError> {
    let pairs: Vec<(String, String)> = url::form_urlencoded::parse(raw.unwrap_or("").as_bytes())
        .into_owned()
        .collect();
    let mut order: Vec<String> = vec![];
    for (k, _) in &pairs {
        if !order.contains(k) {
            order.push(k.clone());
        }
    }
    let value = |k: &str| -> Value {
        if k == "symbols" {
            json!(
                pairs
                    .iter()
                    .filter(|(key, _)| key == k)
                    .map(|(_, v)| v.clone())
                    .collect::<Vec<_>>()
            )
        } else {
            json!(
                pairs
                    .iter()
                    .rev()
                    .find(|(key, _)| key == k)
                    .map(|(_, v)| v.clone())
            )
        }
    };
    let allowed = query_fields(section);
    let mut input = serde_json::Map::new();
    for k in allowed {
        if order.iter().any(|o| o == k) {
            input.insert((*k).into(), value(k));
        }
    }
    for k in &order {
        if !allowed.contains(&k.as_str()) {
            input.insert(k.clone(), value(k));
        }
    }
    let input = Value::Object(input);
    let mut q = QueryValues {
        limit: 15,
        ..Default::default()
    };
    let mut errors = vec![];
    for key in allowed {
        let Some(v) = input.get(*key) else {
            if *key != "limit" {
                errors.push(field(
                    "missing",
                    json!(["query", key]),
                    "Field required",
                    &input,
                    None,
                ));
            }
            continue;
        };
        match *key {
            "symbols" => match query_symbols(v.as_array().unwrap()) {
                Ok(symbols) => q.symbols = symbols,
                Err(e) => errors.push(e),
            },
            "start_date" | "end_date" => match query_date(key, v.as_str().unwrap()) {
                Ok(d) if *key == "start_date" => q.start = Some(d),
                Ok(d) => q.end = Some(d),
                Err(e) => errors.push(e),
            },
            _ => match query_limit(v.as_str().unwrap()) {
                Ok(n) => q.limit = n,
                Err(e) => errors.push(e),
            },
        }
    }
    for k in &order {
        if !allowed.contains(&k.as_str()) {
            errors.push(field(
                "extra_forbidden",
                json!(["query", k]),
                "Extra inputs are not permitted",
                &input[k.as_str()],
                None,
            ));
        }
    }
    if !errors.is_empty() {
        return Err(ApiError::Validation(errors));
    }
    if let (Some(start), Some(end)) = (q.start, q.end) {
        let msg = if end < start {
            Some("종료일은 시작일 이후여야 합니다.")
        } else if end > Utc::now().date_naive() {
            Some("미래 날짜는 조회할 수 없습니다.")
        } else if (end - start).num_days() > 3650 {
            Some("조회 기간이 최대 허용 기간을 초과했습니다.")
        } else {
            None
        };
        if let Some(msg) = msg {
            return Err(ApiError::Validation(vec![value_error(
                json!(["query"]),
                msg,
                &input,
            )]));
        }
    }
    Ok(q)
}

/// `list[str]` with 1..=20 items, each validated as `PortfolioStock(symbol=...)`; the
/// field validator stops at the first bad symbol. Uppercased, deduplicated in input order.
fn query_symbols(raw: &[Value]) -> Result<Vec<String>, Value> {
    if raw.len() > 20 {
        return Err(field(
            "too_long",
            json!(["query", "symbols"]),
            format!(
                "List should have at most 20 items after validation, not {}",
                raw.len()
            ),
            &json!(raw),
            Some(json!({"field_type":"List","max_length":20,"actual_length":raw.len()})),
        ));
    }
    let mut out: Vec<String> = vec![];
    for v in raw {
        let s = v.as_str().unwrap();
        let n = s.chars().count();
        if n < 1 {
            return Err(field(
                "string_too_short",
                json!(["query", "symbols", "symbol"]),
                "String should have at least 1 character",
                v,
                Some(json!({"min_length":1})),
            ));
        }
        if n > 10 {
            return Err(field(
                "string_too_long",
                json!(["query", "symbols", "symbol"]),
                "String should have at most 10 characters",
                v,
                Some(json!({"max_length":10})),
            ));
        }
        if !s.eq_ignore_ascii_case("CASH")
            && !s
                .bytes()
                .all(|b| b.is_ascii_alphanumeric() || b == b'.' || b == b'-')
        {
            return Err(value_error(
                json!(["query", "symbols"]),
                "주식 심볼은 영문자, 숫자, 점(.), 하이픈(-)만 포함해야 합니다.",
                &json!({"symbol":s}),
            ));
        }
        let upper = s.to_ascii_uppercase();
        if !out.contains(&upper) {
            out.push(upper);
        }
    }
    Ok(out)
}

fn query_limit(s: &str) -> Result<usize, Value> {
    let input = json!(s);
    let Ok(n) = s.trim().parse::<i64>() else {
        return Err(field(
            "int_parsing",
            json!(["query", "limit"]),
            "Input should be a valid integer, unable to parse string as an integer",
            &input,
            None,
        ));
    };
    if n > 20 {
        return Err(field(
            "less_than_equal",
            json!(["query", "limit"]),
            "Input should be less than or equal to 20",
            &input,
            Some(json!({"le":20})),
        ));
    }
    if n < 1 {
        return Err(field(
            "greater_than_equal",
            json!(["query", "limit"]),
            "Input should be greater than or equal to 1",
            &input,
            Some(json!({"ge":1})),
        ));
    }
    Ok(n as usize)
}

/// Pydantic (speedate) `date` parsing for the common inputs: YYYY-MM-DD with an optional
/// all-zero time part.
fn query_date(key: &str, s: &str) -> Result<NaiveDate, Value> {
    let input = json!(s);
    let fail = |reason: &str| {
        field(
            "date_from_datetime_parsing",
            json!(["query", key]),
            format!("Input should be a valid date or datetime, {reason}"),
            &input,
            Some(json!({"error":reason})),
        )
    };
    let b = s.as_bytes();
    let digits = |r: std::ops::Range<usize>| b[r].iter().all(u8::is_ascii_digit);
    if b.len() < 10 {
        return Err(fail("input is too short"));
    }
    if !digits(0..4) {
        return Err(fail("invalid character in year"));
    }
    if b[4] != b'-' {
        return Err(fail("invalid date separator, expected `-`"));
    }
    if !digits(5..7) {
        return Err(fail("invalid character in month"));
    }
    if b[7] != b'-' {
        return Err(fail("invalid date separator, expected `-`"));
    }
    if !digits(8..10) {
        return Err(fail("invalid character in day"));
    }
    let (y, m, d): (i32, u32, u32) = (
        s[0..4].parse().unwrap(),
        s[5..7].parse().unwrap(),
        s[8..10].parse().unwrap(),
    );
    if !(1..=12).contains(&m) {
        return Err(fail("month value is outside expected range of 1-12"));
    }
    let Some(date) = NaiveDate::from_ymd_opt(y, m, d) else {
        return Err(fail("day value is outside expected range"));
    };
    if b.len() > 10 {
        if !matches!(b[10], b'T' | b't' | b'_' | b' ') {
            return Err(fail(
                "invalid datetime separator, expected `T`, `t`, `_` or space",
            ));
        }
        if !matches!(&s[11..], "00:00" | "00:00:00" | "00:00:00Z") {
            return Err(field(
                "date_from_datetime_inexact",
                json!(["query", key]),
                "Datetimes provided to dates should have zero time - e.g. be exact dates",
                &input,
                None,
            ));
        }
    }
    Ok(date)
}

/// FastAPI reads an empty body as a missing body, not as malformed JSON.
pub fn missing_body() -> ApiError {
    ApiError::Validation(vec![field(
        "missing",
        json!(["body"]),
        "Field required",
        &Value::Null,
        None,
    )])
}

pub fn invalid_json(error: serde_json::Error) -> ApiError {
    ApiError::Validation(vec![field(
        "json_invalid",
        json!(["body", error.column().saturating_sub(1)]),
        "JSON decode error",
        &json!({}),
        Some(json!({"error": python_json_message(&error.to_string())})),
    )])
}

/// Python `json` module wording for the serde_json syntax error.
fn python_json_message(serde: &str) -> &'static str {
    if serde.contains("key must be a string") {
        "Expecting property name enclosed in double quotes"
    } else if serde.contains("expected `:`") {
        "Expecting ':' delimiter"
    } else if serde.contains("expected `,` or") {
        "Expecting ',' delimiter"
    } else if serde.contains("trailing characters") {
        "Extra data"
    } else {
        "Expecting value"
    }
}
