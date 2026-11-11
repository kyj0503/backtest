use crate::{
    error::{Error, Result},
    metrics,
    model::Bar,
};

use chrono::NaiveDate;
use serde_json::{Map, Value, json};
use std::collections::BTreeMap;
use tokio_util::sync::CancellationToken;

pub fn parameters(name: &str, input: Option<&Map<String, Value>>) -> Result<BTreeMap<String, f64>> {
    let specs: &[(&str, f64, f64, f64)] = match name {
        "sma_strategy" => &[
            ("short_window", 10.0, 2.0, 50.0),
            ("long_window", 20.0, 10.0, 200.0),
        ],
        "ema_strategy" => &[
            ("fast_window", 12.0, 5.0, 50.0),
            ("slow_window", 26.0, 10.0, 200.0),
        ],
        "macd_strategy" => &[
            ("fast_period", 12.0, 5.0, 50.0),
            ("slow_period", 26.0, 10.0, 100.0),
            ("signal_period", 9.0, 2.0, 20.0),
        ],
        "rsi_strategy" => &[
            ("rsi_period", 14.0, 2.0, 50.0),
            ("rsi_oversold", 30.0, 10.0, 40.0),
            ("rsi_overbought", 70.0, 60.0, 90.0),
        ],
        "bollinger_strategy" => &[("period", 20.0, 5.0, 100.0), ("std_dev", 2.0, 0.5, 4.0)],
        "buy_hold_strategy" => &[],
        _ => return Err(Error::validation("지원하지 않는 전략입니다.")),
    };
    let mut result = BTreeMap::new();
    for &(key, default, min, max) in specs {
        let mut value = match input.and_then(|p| p.get(key)) {
            Some(v) => v
                .as_f64()
                .or_else(|| v.as_str().and_then(|s| s.parse().ok()))
                .ok_or_else(|| Error::validation(format!("{key}: 숫자를 입력해 주세요.")))?,
            None => default,
        };
        if key != "std_dev" {
            value = value.trunc();
        }
        if !value.is_finite() || value < min || value > max {
            return Err(Error::validation(format!(
                "{key}: 허용 범위는 {min}~{max}입니다."
            )));
        }
        result.insert(key.into(), value);
    }
    for (a, b) in [
        ("short_window", "long_window"),
        ("fast_window", "slow_window"),
        ("fast_period", "slow_period"),
        ("rsi_oversold", "rsi_overbought"),
    ] {
        if let (Some(x), Some(y)) = (result.get(a), result.get(b))
            && x >= y
        {
            return Err(Error::validation(format!("{a}은 {b}보다 작아야 합니다.")));
        }
    }
    Ok(result)
}
fn ema(values: &[f64], alpha: f64, adjust: bool) -> Vec<f64> {
    let mut numerator = values[0];
    let mut denominator = 1.0;
    values
        .iter()
        .enumerate()
        .map(|(i, x)| {
            if i > 0 {
                if adjust {
                    numerator = x + (1.0 - alpha) * numerator;
                    denominator = 1.0 + (1.0 - alpha) * denominator;
                } else {
                    numerator = alpha * x + (1.0 - alpha) * numerator;
                }
            }
            numerator / denominator
        })
        .collect()
}
fn rolling(values: &[f64], n: usize, std: bool) -> Vec<f64> {
    (0..values.len())
        .map(|i| {
            if i + 1 < n {
                f64::NAN
            } else if std {
                metrics::stddev(&values[i + 1 - n..=i])
            } else {
                metrics::mean(&values[i + 1 - n..=i])
            }
        })
        .collect()
}
pub struct StrategyOutput {
    pub equity: Vec<f64>,
    pub stats: Value,
    pub wins: usize,
    pub trades: usize,
}
pub struct StrategyMarket<'a> {
    /// USD trading bars: only these observations may create signals or fills.
    pub bars: &'a [Bar],
    /// Calendar dates and USD marks (local close revalued at each date's FX).
    pub valuations: &'a [(NaiveDate, f64)],
}
pub fn run(
    name: &str,
    params: Option<&Map<String, Value>>,
    market: &StrategyMarket<'_>,
    initial: f64,
    commission: f64,
    cancel: &CancellationToken,
) -> Result<StrategyOutput> {
    let bars = market.bars;
    if bars.len() < 2 || market.valuations.len() < 2 {
        return Err(Error::validation("전략 실행에 필요한 시세가 부족합니다."));
    }
    let p = parameters(name, params)?;
    let close: Vec<f64> = bars.iter().map(|b| b.close).collect();
    let (a, b, warmup) = match name {
        "sma_strategy" => (
            rolling(&close, p["short_window"] as usize, false),
            rolling(&close, p["long_window"] as usize, false),
            p["long_window"] as usize - 1,
        ),
        "ema_strategy" => (
            ema(&close, 2.0 / (p["fast_window"] + 1.0), false),
            ema(&close, 2.0 / (p["slow_window"] + 1.0), false),
            0,
        ),
        "macd_strategy" => {
            let f = ema(&close, 2.0 / (p["fast_period"] + 1.0), true);
            let s = ema(&close, 2.0 / (p["slow_period"] + 1.0), true);
            let m: Vec<f64> = f.iter().zip(s).map(|(x, y)| x - y).collect();
            let signal = ema(&m, 2.0 / (p["signal_period"] + 1.0), true);
            (m, signal, 0)
        }
        "rsi_strategy" => {
            let delta: Vec<f64> = close
                .iter()
                .enumerate()
                .map(|(i, x)| if i == 0 { 0.0 } else { x - close[i - 1] })
                .collect();
            let n = p["rsi_period"] as usize;
            let mut rsi = vec![f64::NAN; close.len()];
            if close.len() > n {
                let mut gain = delta[1..=n].iter().map(|x| x.max(0.0)).sum::<f64>() / n as f64;
                let mut loss = delta[1..=n].iter().map(|x| (-x).max(0.0)).sum::<f64>() / n as f64;
                for i in n..close.len() {
                    if i > n {
                        gain = (gain * (n - 1) as f64 + delta[i].max(0.0)) / n as f64;
                        loss = (loss * (n - 1) as f64 + (-delta[i]).max(0.0)) / n as f64;
                    }
                    rsi[i] = if gain + loss == 0.0 {
                        50.0
                    } else {
                        100.0 * gain / (gain + loss)
                    };
                }
            }
            (rsi, vec![], 0)
        }
        "bollinger_strategy" => (
            rolling(&close, p["period"] as usize, false),
            rolling(&close, p["period"] as usize, true),
            p["period"] as usize - 1,
        ),
        _ => return Err(Error::validation("지원하지 않는 전략입니다.")),
    };
    let mut equity = vec![initial; bars.len()];
    let mut cash_balances = vec![initial; bars.len()];
    let mut quantities = vec![0.0; bars.len()];
    let mut cash = initial;
    let mut position: Option<(usize, f64, f64, f64)> = None;
    let mut order = 0.0_f64;
    let mut trades = Vec::new();
    let mut pnl = Vec::new();
    let mut trade_returns = Vec::new();
    // Signals from a close execute on the next bar's open, never on the signal bar.
    // Bollinger needs only the current complete window; crossover strategies
    // also need the preceding indicator value. Every order still fills later.
    let first_signal = if name == "bollinger_strategy" {
        warmup
    } else {
        warmup + 1
    };
    for i in first_signal..bars.len() {
        if cancel.is_cancelled() {
            return Err(Error(499, "계산이 취소되었습니다.".into()));
        }
        if order < 0.0 {
            if let Some((entry, price, size, entry_fee)) = position.take() {
                let exit = bars[i].open;
                let exit_fee = size * exit * commission;
                cash += size * exit - exit_fee;
                let profit = size * (exit - price) - entry_fee - exit_fee;
                let ret = profit / (size * price + entry_fee);
                pnl.push(profit);
                trade_returns.push(ret);
                trades.push(json!({"Size":size,"EntryBar":entry,"ExitBar":i,"EntryPrice":price,"ExitPrice":exit,"SL":0.0,"TP":0.0,"PnL":profit,"Commission":entry_fee+exit_fee,"ReturnPct":ret,"EntryTime":format!("{}T00:00:00",bars[entry].date),"ExitTime":format!("{}T00:00:00",bars[i].date),"Duration":format!("P{}DT0H0M0S",(bars[i].date-bars[entry].date).num_days()),"Tag":0.0}));
            }
        } else if order > 0.0 && position.is_none() {
            let price = bars[i].open;
            let fee = order * price * commission;
            if order * price + fee <= cash {
                cash -= order * price + fee;
                position = Some((i, price, order, fee));
            }
        }
        order = 0.0;
        equity[i] = cash + position.map_or(0.0, |(_, _, s, _)| s * bars[i].close);
        cash_balances[i] = cash;
        quantities[i] = position.map_or(0.0, |(_, _, size, _)| size);
        if !equity[i].is_finite() || !cash.is_finite() || !quantities[i].is_finite() {
            return Err(Error::validation(
                "계산 결과가 표현 가능한 범위를 벗어났습니다.",
            ));
        }
        let (buy, sell) = match name {
            "sma_strategy" | "ema_strategy" | "macd_strategy" => (
                a[i - 1] < b[i - 1] && a[i] > b[i],
                b[i - 1] < a[i - 1] && b[i] > a[i],
            ),
            "rsi_strategy" => (
                i >= p["rsi_period"] as usize && a[i] < p["rsi_oversold"],
                i >= p["rsi_period"] as usize
                    && (a[i] > p["rsi_overbought"] || (a[i] >= 50.0 && a[i - 1] < 50.0)),
            ),
            _ => (
                close[i] < a[i] - p["std_dev"] * b[i],
                close[i] > a[i] + p["std_dev"] * b[i] || close[i] >= a[i],
            ),
        };
        if position.is_some() && sell {
            order = -1.0;
        } else if position.is_none() && buy {
            // Adjusted OHLC is a total-return price unit, not a historical share
            // lot. Fractional units preserve wealth when that unit is rescaled.
            order = equity[i] * 0.95 / (close[i] * (1.0 + commission));
        }
    }
    // No executable next bar exists for the final signal. Open positions remain
    // marked at the final close; liquidation is never backdated to that day's open.
    let mut calendar_equity = Vec::with_capacity(market.valuations.len());
    for (day, price) in market.valuations {
        let n = bars.partition_point(|b| b.date <= *day);
        let value = if n == 0 {
            initial
        } else {
            cash_balances[n - 1] + quantities[n - 1] * price
        };
        if !value.is_finite() {
            return Err(Error::validation(
                "계산 결과가 표현 가능한 범위를 벗어났습니다.",
            ));
        }
        calendar_equity.push(value);
    }
    let equity = calendar_equity;
    let i = equity.len() - 1;
    let final_price = market.valuations[i].1;
    let open_positions: Vec<Value> = position
        .into_iter()
        .map(|(entry, price, size, fee)| {
            json!({"EntryTime":bars[entry].date,"EntryPrice":price,"Size":size,
            "Commission":fee,"MarketPrice":final_price,"MarketValue":size*final_price})
        })
        .collect();
    // Preserve backtesting.py's public indicator snapshots at the fill bars.
    let names = match name {
        "sma_strategy" => vec![
            (format!("_sma_help…(C,{})", p["short_window"]), a.clone()),
            (format!("_sma_help…(C,{})", p["long_window"]), b.clone()),
        ],
        "ema_strategy" => vec![
            (format!("_ema(C,{})", p["fast_window"]), a.clone()),
            (format!("_ema(C,{})", p["slow_window"]), b.clone()),
        ],
        "macd_strategy" => vec![
            (
                format!("_macd_line(C,{},{})", p["fast_period"], p["slow_period"]),
                a.clone(),
            ),
            (
                format!(
                    "_signal_l…(C,{},{},{})",
                    p["fast_period"], p["slow_period"], p["signal_period"]
                ),
                b.clone(),
            ),
        ],
        "rsi_strategy" => vec![(format!("_rsi(C,{})", p["rsi_period"]), a.clone())],
        _ => vec![
            (format!("SMA(C,{})", p["period"]), a.clone()),
            (format!("_std(C,{})", p["period"]), b.clone()),
            (
                "λ".into(),
                a.iter()
                    .zip(&b)
                    .map(|(m, s)| m - p["std_dev"] * s)
                    .collect(),
            ),
        ],
    };
    for trade in &mut trades {
        for (prefix, key) in [("Entry", "EntryBar"), ("Exit", "ExitBar")] {
            let index = trade[key].as_u64().unwrap() as usize;
            for (name, values) in &names {
                trade[format!("{prefix}_{name}")] = json!(values[index]);
            }
        }
    }
    let dates: Vec<_> = market.valuations.iter().map(|(day, _)| *day).collect();
    let calendar_returns = metrics::daily(&equity);
    let headline = metrics::statistics(
        &dates,
        &equity,
        &calendar_returns,
        initial,
        1.0,
        trades.len(),
    );
    let finite_metric = |key: &str| {
        headline[key]
            .as_f64()
            .filter(|n| n.is_finite())
            .ok_or_else(|| {
                Error::validation(format!(
                    "{key}: 계산 결과가 표현 가능한 범위를 벗어났습니다."
                ))
            })
    };
    let annual = finite_metric("Annual_Return")? / 100.0;
    let volatility = finite_metric("Annual_Volatility")?;
    let downside = (calendar_returns
        .iter()
        .map(|r| r.min(0.0).powi(2))
        .sum::<f64>()
        / calendar_returns.len() as f64)
        .sqrt()
        * 365.0_f64.sqrt();
    let wins = pnl.iter().filter(|p| **p > 0.0).count();
    let n = trades.len();
    let mut peak = equity[0];
    let mut drawdowns = Vec::new();
    let mut recoveries = Vec::new();
    for (idx, value) in equity.iter().enumerate() {
        peak = peak.max(*value);
        let dd = 1.0 - value / peak;
        drawdowns.push(dd);
        if dd == 0.0 || idx == i {
            recoveries.push(idx);
        }
    }
    let mut drawdown_peaks: Vec<f64> = recoveries
        .windows(2)
        .filter(|pair| pair[1] > pair[0] + 1)
        .map(|pair| {
            drawdowns[pair[0]..=pair[1]]
                .iter()
                .copied()
                .fold(0.0_f64, f64::max)
        })
        .collect();
    if drawdown_peaks.is_empty() {
        drawdown_peaks = drawdowns.iter().copied().filter(|d| *d > 0.0).collect();
    }
    let stats = json!({"initial_cash":initial,"final_equity":equity[i],"total_return_pct":(equity[i]/initial-1.0)*100.0,
        "annualized_return_pct":annual*100.0,"cagr_pct":annual*100.0,"buy_and_hold_return_pct":(final_price/close[warmup.min(close.len()-1)]-1.0)*100.0,"volatility_pct":volatility,
        "sharpe_ratio":headline["Sharpe_Ratio"],"sortino_ratio":if downside>0.0{annual/downside}else{0.0},
        "calmar_ratio":if headline["Max_Drawdown"].as_f64().unwrap()<0.0{annual/(-headline["Max_Drawdown"].as_f64().unwrap()/100.0)}else{0.0},
        "max_drawdown_pct":headline["Max_Drawdown"],"avg_drawdown_pct":-metrics::mean(&drawdown_peaks)*100.0,"total_trades":n,"win_rate_pct":if n>0{wins as f64/n as f64*100.0}else{0.0},
        "profit_factor":metrics::profit_factor(&pnl),
        "avg_trade_pct":if n>0{(trade_returns.iter().map(|r|1.0+r).product::<f64>().powf(1.0/n as f64)-1.0)*100.0}else{0.0},
        "best_trade_pct":trade_returns.iter().copied().reduce(f64::max).unwrap_or(0.0)*100.0,"worst_trade_pct":trade_returns.iter().copied().reduce(f64::min).unwrap_or(0.0)*100.0,
        "sqn":if metrics::stddev(&pnl)>0.0{(n as f64).sqrt()*metrics::mean(&pnl)/metrics::stddev(&pnl)}else{0.0},
        "alpha_pct":null,"beta":null,"kelly_criterion":null,"trade_log":trades,"open_positions":open_positions,"cash":cash,
        "equity_curve":dates.iter().zip(&equity).map(|(d,e)|(d.to_string(),json!(e))).collect::<Map<_,_>>()});
    Ok(StrategyOutput {
        equity,
        stats,
        wins,
        trades: n,
    })
}
