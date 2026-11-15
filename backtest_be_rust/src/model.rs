use crate::{
    error::{Error, Result},
    schedule,
};
use chrono::{NaiveDate, Utc};
use serde::{Deserialize, Serialize};
use serde_json::{Map, Value};
use std::collections::{BTreeMap, HashSet};

fn lump_sum() -> String {
    "lump_sum".into()
}
fn monthly() -> String {
    "monthly_1".into()
}
fn stock() -> String {
    "stock".into()
}
fn buy_hold() -> String {
    "buy_hold_strategy".into()
}
fn commission() -> f64 {
    0.002
}
fn yes() -> bool {
    true
}

#[derive(Debug, Clone, Deserialize, Serialize)]
pub struct Asset {
    pub symbol: String,
    #[serde(default, deserialize_with = "optional_number")]
    pub amount: Option<f64>,
    /// Exact allocation budget; DCA divides this over scheduled deposits and
    /// settles the rounding remainder on the final installment.
    #[serde(default, deserialize_with = "optional_number")]
    pub total_amount: Option<f64>,
    #[serde(default, deserialize_with = "optional_number")]
    pub weight: Option<f64>,
    #[serde(default = "lump_sum")]
    pub investment_type: String,
    #[serde(default = "monthly")]
    pub dca_frequency: String,
    #[serde(default = "stock")]
    pub asset_type: String,
}
impl Asset {
    /// Stable response key, separate from the display symbol and reserved metadata.
    pub fn id(&self, index: usize) -> String {
        if self.cash() {
            format!("{}__cash_{}", self.symbol, index + 1)
        } else {
            self.symbol.clone()
        }
    }
    pub fn cash(&self) -> bool {
        self.asset_type == "cash"
    }
    pub fn dca(&self) -> bool {
        self.investment_type == "dca"
    }
    pub fn amount(&self) -> f64 {
        self.total_amount
            .filter(|_| !self.dca())
            .or(self.amount)
            .or(self.weight)
            .unwrap_or(0.0)
    }
}

#[derive(Debug, Clone, Deserialize, Serialize)]
pub struct BacktestRequest {
    pub portfolio: Vec<Asset>,
    pub start_date: NaiveDate,
    pub end_date: NaiveDate,
    #[serde(default = "buy_hold")]
    pub strategy: String,
    #[serde(default)]
    pub strategy_params: Option<Map<String, Value>>,
    #[serde(default = "commission")]
    pub commission: f64,
    // None preserves the legacy distinction between an omitted and explicit value.
    #[serde(default, deserialize_with = "explicit_string")]
    pub rebalance_frequency: Option<String>,
    #[serde(default = "yes")]
    pub include_stock_data: bool,
    #[serde(default = "yes")]
    pub include_volatility_events: bool,
    #[serde(default = "yes")]
    pub include_exchange_rates: bool,
    #[serde(default = "yes")]
    pub include_benchmarks: bool,
    #[serde(default = "yes")]
    pub include_news: bool,
}
impl BacktestRequest {
    pub fn buy_hold(&self) -> bool {
        self.strategy == "buy_hold_strategy"
    }
    pub fn rebalance(&self) -> &str {
        self.rebalance_frequency
            .as_deref()
            .unwrap_or(if self.buy_hold() { "monthly_1" } else { "none" })
    }
    pub fn validate(&mut self, min_days: i64) -> Result<()> {
        validate_period(self.start_date, self.end_date, min_days)?;
        if self.portfolio.is_empty() || self.portfolio.len() > 20 {
            return Err(Error::validation("포트폴리오는 1~20개 항목이어야 합니다."));
        }
        if !(0.0..0.1).contains(&self.commission) {
            return Err(Error::validation("수수료는 0 이상 0.1 미만이어야 합니다."));
        }
        if ![
            "buy_hold_strategy",
            "sma_strategy",
            "ema_strategy",
            "rsi_strategy",
            "bollinger_strategy",
            "macd_strategy",
        ]
        .contains(&self.strategy.as_str())
        {
            return Err(Error::validation("지원하지 않는 전략입니다."));
        }
        if self.rebalance() != "none" && schedule::frequency(self.rebalance()).is_none() {
            return Err(Error::validation("유효하지 않은 리밸런싱 주기입니다."));
        }
        let mut seen = HashSet::new();
        for a in &mut self.portfolio {
            if !["cash", "stock"].contains(&a.asset_type.as_str())
                || !["lump_sum", "dca"].contains(&a.investment_type.as_str())
            {
                return Err(Error::validation(
                    "유효하지 않은 자산 또는 투자 방식입니다.",
                ));
            }
            validate_symbol(&a.symbol, a.cash())?;
            if !a.cash() {
                a.symbol.make_ascii_uppercase();
                if !seen.insert(a.symbol.clone()) {
                    return Err(Error::validation("중복된 종목입니다."));
                }
            }
            if a.amount
                .is_some_and(|v| !v.is_finite() || v <= 0.0 || v > 1e12)
                || a.total_amount
                    .is_some_and(|v| !v.is_finite() || v <= 0.0 || v > 1e12)
                || a.weight
                    .is_some_and(|v| !v.is_finite() || !(0.0..=100.0).contains(&v))
            {
                return Err(Error::validation("금액 또는 비중이 유효하지 않습니다."));
            }
            if a.amount.is_some() && a.weight.is_some() {
                return Err(Error::validation(
                    "각 항목에 amount 또는 weight 중 하나를 입력해 주세요.",
                ));
            }
            if a.total_amount.is_some() && (a.amount.is_none() || a.weight.is_some()) {
                return Err(Error::validation(
                    "total_amount는 amount와 함께만 사용할 수 있습니다.",
                ));
            }
            schedule::frequency(&a.dca_frequency)
                .ok_or_else(|| Error::validation("유효하지 않은 DCA 주기입니다."))?;
            if a.dca()
                && schedule::schedule(self.start_date, self.end_date, &a.dca_frequency).is_empty()
            {
                return Err(Error::validation("DCA 주기가 백테스트 기간보다 깁니다."));
            }
        }
        let planned: f64 = self
            .portfolio
            .iter()
            .map(|a| {
                a.total_amount.unwrap_or_else(|| {
                    a.amount()
                        * if a.dca() && a.weight.is_none() {
                            (1 + schedule::schedule(
                                self.start_date,
                                self.end_date,
                                &a.dca_frequency,
                            )
                            .len()) as f64
                        } else {
                            1.0
                        }
                })
            })
            .sum();
        if !planned.is_finite() || planned <= 0.0 || planned > 1e12 {
            return Err(Error::validation(
                "총 예정 납입액은 0 초과 1조 USD 이하여야 합니다.",
            ));
        }
        let weights = self.portfolio.iter().any(|a| a.weight.is_some());
        if weights && self.portfolio.iter().any(|a| a.amount.is_some()) {
            return Err(Error::validation("금액과 비중을 혼합할 수 없습니다."));
        }
        if weights
            && !(95.0..=105.0).contains(&self.portfolio.iter().map(Asset::amount).sum::<f64>())
        {
            return Err(Error::validation("비중 합계는 95~105%여야 합니다."));
        }
        if !self.buy_hold()
            && (self.rebalance() != "none" || self.portfolio.iter().any(|a| a.dca()))
        {
            return Err(Error::validation(
                "DCA와 리밸런싱은 buy_hold_strategy에서만 지원합니다.",
            ));
        }
        crate::strategy::parameters(&self.strategy, self.strategy_params.as_ref())?;
        Ok(())
    }
}
pub fn validate_symbol(symbol: &str, cash: bool) -> Result<()> {
    if symbol.is_empty()
        || symbol.chars().count() > 10
        || (!cash
            && !symbol
                .bytes()
                .all(|b| b.is_ascii_alphanumeric() || b == b'.' || b == b'-'))
    {
        return Err(Error::validation("유효하지 않은 종목 심볼입니다."));
    }
    Ok(())
}
pub fn validate_period(start: NaiveDate, end: NaiveDate, min_days: i64) -> Result<()> {
    let days = (end - start).num_days();
    if days < min_days || days > 3650 || end > Utc::now().date_naive() {
        return Err(Error::validation(format!(
            "조회 기간은 {min_days}~3650일이며 종료일은 미래일 수 없습니다."
        )));
    }
    Ok(())
}
#[derive(Debug, Clone, Deserialize, Serialize)]
pub struct Bar {
    pub date: NaiveDate,
    pub open: f64,
    pub high: f64,
    pub low: f64,
    pub close: f64,
    #[serde(default)]
    pub volume: f64,
}
impl Bar {
    pub fn valid_rate(&self) -> bool {
        self.close.is_finite() && self.close > 0.0
    }
    pub fn valid_prices(&self) -> bool {
        let values = [self.open, self.high, self.low, self.close];
        if values.iter().any(|v| !v.is_finite() || *v <= 0.0) {
            return false;
        }
        // Multiplying raw OHLC by an adjustment factor can differ by a few
        // ulps from the provider's adjusted close at an exact high/low boundary.
        let tolerance = self.high.max(self.close).max(self.open) * f64::EPSILON * 8.0;
        self.high >= self.low
            && self.open.min(self.close) >= self.low - tolerance
            && self.open.max(self.close) <= self.high + tolerance
    }
}
#[derive(Debug, Clone, Deserialize, Serialize)]
pub struct History {
    pub symbol: String,
    pub currency: String,
    #[serde(default)]
    pub company_name: String,
    #[serde(default)]
    pub exchange: String,
    pub first_trade_date: Option<NaiveDate>,
    pub bars: Vec<Bar>,
}
pub type Histories = BTreeMap<String, History>;

fn optional_number<'de, D: serde::Deserializer<'de>>(
    d: D,
) -> std::result::Result<Option<f64>, D::Error> {
    let value = Value::deserialize(d)?;
    let number = match &value {
        Value::Null => return Ok(None),
        Value::Bool(b) => Some(if *b { 1.0 } else { 0.0 }),
        Value::String(s) => s.trim().parse().ok(),
        _ => value.as_f64(),
    };
    number
        .map(Some)
        .ok_or_else(|| serde::de::Error::custom("Input should be a valid number"))
}
fn explicit_string<'de, D: serde::Deserializer<'de>>(
    d: D,
) -> std::result::Result<Option<String>, D::Error> {
    String::deserialize(d).map(Some)
}
