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

pub fn query(section: &str, raw: Option<&str>) -> Result<(), ApiError> {
    let mut input = json!({});
    for (key, value) in url::form_urlencoded::parse(raw.unwrap_or("").as_bytes()) {
        if key == "symbols" {
            if input["symbols"].is_null() {
                input["symbols"] = json!([]);
            }
            input["symbols"].as_array_mut().unwrap().push(json!(value));
        } else {
            input[key.as_ref()] = json!(value);
        }
    }
    let mut errors = vec![];
    for key in if section == "news" {
        vec!["symbols"]
    } else if section == "prices" {
        vec!["symbols", "start_date", "end_date"]
    } else {
        vec!["start_date", "end_date"]
    } {
        if input.get(key).is_none() {
            errors.push(field(
                "missing",
                json!(["query", key]),
                "Field required",
                &input,
                None,
            ));
        }
    }
    if section == "news"
        && let Some(v) = input.get("limit")
        && let Some(n) = v.as_str().and_then(|s| s.parse::<i64>().ok())
        && !(1..=20).contains(&n)
    {
        errors.push(field(
            if n > 20 {
                "less_than_equal"
            } else {
                "greater_than_equal"
            },
            json!(["query", "limit"]),
            if n > 20 {
                "Input should be less than or equal to 20"
            } else {
                "Input should be greater than or equal to 1"
            },
            v,
            Some(if n > 20 {
                json!({"le":20})
            } else {
                json!({"ge":1})
            }),
        ));
    }
    for (key, v) in input.as_object().unwrap() {
        let allowed = match section {
            "news" => ["symbols", "limit"].contains(&key.as_str()),
            "prices" => ["symbols", "start_date", "end_date"].contains(&key.as_str()),
            _ => ["start_date", "end_date"].contains(&key.as_str()),
        };
        if !allowed {
            errors.push(field(
                "extra_forbidden",
                json!(["query", key]),
                "Extra inputs are not permitted",
                v,
                None,
            ));
        }
    }
    if errors.is_empty() {
        Ok(())
    } else {
        Err(ApiError::Validation(errors))
    }
}

pub fn invalid_json(error: serde_json::Error) -> ApiError {
    ApiError::Validation(vec![field(
        "json_invalid",
        json!(["body", error.column().saturating_sub(1)]),
        "JSON decode error",
        &json!({}),
        Some(
            json!({"error":if error.to_string().contains("key must be a string"){"Expecting property name enclosed in double quotes".to_string()}else{error.to_string()}}),
        ),
    )])
}
