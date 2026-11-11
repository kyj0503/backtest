//! Deterministic simulation. No HTTP, database, wall-clock or Python dependency.
use crate::{
    error::{Error, Result},
    metrics,
    model::{Asset, BacktestRequest, Bar, Histories},
    schedule, strategy,
};
use chrono::{Duration, NaiveDate};
use serde_json::{Map, Value, json};
use std::collections::{BTreeMap, BTreeSet};
use tokio_util::sync::CancellationToken;

pub fn fx_ticker(currency: &str) -> Option<(&'static str, bool)> {
    Some(match currency {
        "KRW" => ("KRW=X", false),
        "JPY" => ("JPY=X", false),
        "EUR" => ("EURUSD=X", true),
        "GBP" => ("GBPUSD=X", true),
        "CNY" => ("CNY=X", false),
        "HKD" => ("HKD=X", false),
        "TWD" => ("TWD=X", false),
        "SGD" => ("SGD=X", false),
        "AUD" => ("AUDUSD=X", true),
        "CAD" => ("CADUSD=X", true),
        "CHF" => ("CHFUSD=X", true),
        "INR" => ("INR=X", false),
        _ => return None,
    })
}
pub fn fx(currency: &str, day: NaiveDate, data: &Histories) -> Result<f64> {
    if currency == "USD" {
        return Ok(1.0);
    }
    let (ticker, multiply) = fx_ticker(currency).ok_or_else(|| {
        Error::validation(format!("지원하지 않거나 확인할 수 없는 통화: {currency}"))
    })?;
    let rates = data
        .get(ticker)
        .ok_or_else(|| Error::validation(format!("{currency}: 환율이 없습니다.")))?;
    let i = rates.bars.partition_point(|b| b.date <= day);
    let rate = i
        .checked_sub(1)
        .map(|i| rates.bars[i].close)
        .filter(|r| r.is_finite() && *r > 0.0)
        .ok_or_else(|| {
            Error::validation(format!("{currency}: {day} 이전의 유효한 환율이 없습니다."))
        })?;
    Ok(if multiply { rate } else { 1.0 / rate })
}
fn curve(dates: &[NaiveDate], values: &[f64], scale: f64) -> Value {
    Value::Object(
        dates
            .iter()
            .zip(values)
            .map(|(d, v)| (d.to_string(), json!(v * scale)))
            .collect(),
    )
}
fn checked(cancel: &CancellationToken) -> Result<()> {
    if cancel.is_cancelled() {
        Err(Error(499, "계산이 취소되었습니다.".into()))
    } else {
        Ok(())
    }
}
pub fn run(req: &BacktestRequest, data: &Histories, cancel: &CancellationToken) -> Result<Value> {
    checked(cancel)?;
    req.clone().validate(30)?;
    for h in data.values() {
        let conversion_only = h.symbol.ends_with("=X")
            && !req
                .portfolio
                .iter()
                .any(|a| !a.cash() && a.symbol == h.symbol);
        if h.bars.iter().any(|b| {
            if conversion_only {
                !b.valid_rate()
            } else {
                !b.valid_prices()
            }
        }) {
            return Err(Error::validation("유효하지 않은 가격 데이터입니다."));
        }
    }
    let mut result = if req.buy_hold() {
        buy_hold(req, data, cancel)?
    } else {
        technical(req, data, cancel)?
    };
    let stats = &result["data"]["portfolio_statistics"];
    if [
        "Initial_Value",
        "Final_Value",
        "Total_Return",
        "Annual_Return",
        "Annual_Volatility",
    ]
    .iter()
    .any(|field| stats[field].as_f64().is_none_or(|n| !n.is_finite()))
    {
        return Err(Error::validation(
            "계산 결과가 지원하는 숫자 범위를 초과했습니다.",
        ));
    }
    // Execution prices used by accounting are USD; price charts use the native
    // adjusted quote. Carry both explicitly, using the execution day's FX only.
    let currencies: BTreeMap<_, _> = result["data"]["individual_returns"]
        .as_object()
        .unwrap()
        .iter()
        .filter_map(|(key, item)| {
            data.get(item["symbol"].as_str()?)
                .map(|h| (key.clone(), h.currency.clone()))
        })
        .collect();
    for (key, stats) in result["data"]["strategy_details"].as_object_mut().unwrap() {
        let Some(currency) = currencies.get(key) else {
            continue;
        };
        for section in ["trade_log", "open_positions"] {
            if let Some(logs) = stats[section].as_array_mut() {
                for trade in logs {
                    trade["PriceCurrency"] = json!("USD");
                    trade["NativeCurrency"] = json!(currency);
                    trade["QuantityUnit"] = json!("fractional_adjusted_unit");
                    for side in ["Entry", "Exit"] {
                        let time_key = format!("{side}Time");
                        let price_key = format!("{side}Price");
                        if let (Some(time), Some(price)) =
                            (trade[&time_key].as_str(), trade[&price_key].as_f64())
                        {
                            let day = NaiveDate::parse_from_str(&time[..10], "%Y-%m-%d")
                                .map_err(|_| Error::validation("유효하지 않은 거래 날짜입니다."))?;
                            trade[format!("{side}PriceNative")] =
                                json!(price / fx(currency, day, data)?);
                        }
                    }
                }
            }
        }
    }
    result["data"]["calculation_assumptions"] = json!({
        "quantity_unit":"fractional_adjusted_unit", "account_currency":"USD",
        "weight_basis":"asset_account_including_uninvested_cash",
        "price_basis":"adjusted_total_return"
    });
    Ok(result)
}
struct Holding {
    asset: Asset,
    key: String,
    planned: f64,
    per_period: f64,
    schedule: Vec<NaiveDate>,
    executed: usize,
    shares: f64,
    cash: f64,
    price: Option<f64>,
    tradeable: bool,
    contributed: f64,
    profit: f64,
    previous: f64,
    returns: Vec<f64>,
    trades: Vec<Value>,
    buy_size: f64,
    buy_notional: f64,
}
impl Holding {
    fn value(&self) -> f64 {
        self.cash + self.shares * self.price.unwrap_or(0.0)
    }
    fn trade(&mut self, day: NaiveDate, size: f64, commission: f64) {
        if size.abs() <= 1e-12 {
            return;
        }
        let price = self.price.unwrap();
        self.trades.push(json!({"EntryTime":format!("{day}T00:00:00"),"EntryPrice":price,"Size":size.abs(),"Commission":size.abs()*price*commission,"Type":if size>0.0{"BUY"}else{"SELL"},"ExitTime":null,"ExitPrice":null,"PnL":null,"ReturnPct":null,"Duration":null}));
        if size > 0.0 {
            self.buy_size += size;
            self.buy_notional += size * price;
        }
    }
}
fn buy_hold(req: &BacktestRequest, data: &Histories, cancel: &CancellationToken) -> Result<Value> {
    let mut holdings = Vec::new();
    let mut warnings = Vec::new();
    let mut dates = BTreeSet::new();
    for (asset_index, asset) in req.portfolio.iter().enumerate() {
        if !asset.cash() {
            match data.get(&asset.symbol) {
                Some(h) if !h.bars.is_empty() => {
                    dates.extend(
                        h.bars
                            .iter()
                            .filter(|b| b.date >= req.start_date && b.date <= req.end_date)
                            .map(|b| b.date),
                    );
                }
                _ => {
                    let amount = format!("{:.2}", asset.amount());
                    let (whole, fraction) = amount.split_once('.').unwrap();
                    let grouped = whole
                        .chars()
                        .enumerate()
                        .fold(String::new(), |mut s, (i, c)| {
                            if i > 0 && (whole.len() - i) % 3 == 0 {
                                s.push(',');
                            }
                            s.push(c);
                            s
                        });
                    warnings.push(format!("종목 {}의 가격 데이터를 불러오지 못해 백테스트에서 제외했습니다 (투자금 ${grouped}.{fraction}는 수익률 계산에 포함되지 않음).",asset.symbol));
                    continue;
                }
            }
        }
        let mut plan = vec![req.start_date];
        if asset.dca() {
            plan.extend(schedule::schedule(
                req.start_date,
                req.end_date,
                &asset.dca_frequency,
            ));
        }
        let planned = asset.total_amount.unwrap_or_else(|| {
            if asset.weight.is_some() {
                asset.amount()
            } else {
                asset.amount() * plan.len() as f64
            }
        });
        let per_period = if asset.total_amount.is_some() {
            (planned * 100.0 / plan.len() as f64).floor() / 100.0
        } else if asset.weight.is_some() {
            planned / plan.len() as f64
        } else {
            asset.amount()
        };
        let cash = 0.0;
        let key = asset.id(asset_index);
        holdings.push(Holding {
            asset: asset.clone(),
            key,
            planned,
            per_period,
            schedule: plan,
            executed: 0,
            shares: 0.0,
            cash,
            price: None,
            tradeable: false,
            contributed: cash,
            profit: 0.0,
            previous: cash,
            returns: vec![],
            trades: vec![],
            buy_size: 0.0,
            buy_notional: 0.0,
        });
    }
    if holdings.is_empty() {
        return Err(Error::validation(
            "[ValidationError] 포트폴리오의 어떤 종목도 데이터를 가져올 수 없습니다.",
        ));
    }
    // A common daily valuation calendar makes deposits on holidays visible as
    // cash and makes portfolio/benchmark risk observations use the same units.
    let dates: Vec<_> = (0..=(req.end_date - req.start_date).num_days())
        .map(|d| req.start_date + Duration::days(d))
        .collect();
    let planned_total: f64 = holdings.iter().map(|h| h.planned).sum();
    let mut previous = 0.0;
    let mut equity = vec![];
    let mut returns = vec![];
    let mut weights = vec![];
    let mut rebalances = vec![];
    let mut trade_count = 0;
    let rebalance_days = schedule::schedule(req.start_date, req.end_date, req.rebalance());
    let mut rebalance_index = 0;
    let mut rebalance_pending = false;
    for day in &dates {
        checked(cancel)?;
        for h in &mut holdings {
            if h.asset.cash() {
                continue;
            }
            let history = &data[&h.asset.symbol];
            let i = history.bars.partition_point(|b| b.date <= *day);
            h.tradeable = false;
            if i > 0 {
                let bar = &history.bars[i - 1];
                if bar.close.is_finite() && bar.close > 0.0 {
                    h.price = Some(bar.close * fx(&history.currency, *day, data)?);
                    h.tradeable = bar.date == *day;
                }
            }
        }
        let before: Vec<f64> = holdings.iter().map(Holding::value).collect();
        let pre_flow: f64 = before.iter().sum();
        let mut inflows = vec![0.0; holdings.len()];
        let mut transfers = vec![0.0; holdings.len()];
        for (i, h) in holdings.iter_mut().enumerate() {
            h.profit += before[i] - h.previous;
            while h.executed < h.schedule.len() && h.schedule[h.executed] <= *day {
                let amount = if h.asset.total_amount.is_some() && h.executed + 1 == h.schedule.len()
                {
                    h.planned - h.contributed
                } else {
                    h.per_period
                };
                h.cash += amount;
                h.contributed += amount;
                inflows[i] += amount;
                h.executed += 1;
            }
            if !h.asset.cash() && h.tradeable && h.cash > 0.0 {
                let size = h.cash / (h.price.unwrap() * (1.0 + req.commission));
                h.shares += size;
                h.cash = 0.0;
                trade_count += 1;
                h.trade(*day, size, req.commission);
            }
        }
        while rebalance_index < rebalance_days.len() && rebalance_days[rebalance_index] <= *day {
            rebalance_pending = !equity.is_empty();
            rebalance_index += 1;
        }
        // The valuation calendar includes holidays. Keep due orders pending
        // until every funded non-cash asset can trade; never rebalance a subset.
        if rebalance_pending
            && holdings.len() > 1
            && holdings
                .iter()
                .all(|h| h.asset.cash() || h.planned == 0.0 || h.tradeable)
        {
            rebalance_pending = false;
            let current: Vec<f64> = holdings.iter().map(Holding::value).collect();
            let total: f64 = current.iter().sum();
            let eligible: Vec<bool> = holdings
                .iter()
                .map(|h| h.asset.cash() || h.tradeable)
                .collect();
            let allocated: f64 = current
                .iter()
                .zip(&eligible)
                .filter(|(_, ok)| **ok)
                .map(|(v, _)| *v)
                .sum();
            let target_sum: f64 = holdings
                .iter()
                .zip(&eligible)
                .filter(|(_, ok)| **ok)
                .map(|(h, _)| h.planned / planned_total)
                .sum();
            if total > 0.0 && target_sum > 0.0 {
                let target_weights: Vec<f64> = holdings
                    .iter()
                    .map(|h| h.planned / planned_total / target_sum)
                    .collect();
                // Solve V_after + actual turnover fees(V_after) = V_before.
                // The function is monotone because commission < 0.1.
                let mut low = 0.0;
                let mut high = allocated;
                for _ in 0..80 {
                    let mid = (low + high) / 2.0;
                    let fees: f64 = holdings
                        .iter()
                        .enumerate()
                        .filter(|(i, h)| eligible[*i] && !h.asset.cash())
                        .map(|(i, _)| (mid * target_weights[i] - current[i]).abs() * req.commission)
                        .sum();
                    if mid + fees > allocated {
                        high = mid;
                    } else {
                        low = mid;
                    }
                }
                let net = (low + high) / 2.0;
                let target: Vec<f64> = current
                    .iter()
                    .enumerate()
                    .map(|(i, v)| {
                        if eligible[i] {
                            net * target_weights[i]
                        } else {
                            *v
                        }
                    })
                    .collect();
                let mut fees = 0.0;
                let mut event_trades = vec![];
                let mut before_weights = Map::new();
                let mut after_weights = Map::new();
                for (i, h) in holdings.iter_mut().enumerate() {
                    before_weights.insert(h.key.clone(), json!(current[i] / total));
                    if !eligible[i] {
                        continue;
                    }
                    let difference = target[i] - current[i];
                    let fee = if h.asset.cash() {
                        0.0
                    } else {
                        difference.abs() * req.commission
                    };
                    fees += fee;
                    transfers[i] = difference + fee;
                    if h.asset.cash() {
                        h.cash = target[i];
                        if difference.abs() > 1e-9 {
                            event_trades.push(json!({"asset_id":h.key,"symbol":h.asset.symbol,"action":if difference>0.0{"increase"}else{"decrease"},"amount":difference.abs(),"price":1.0,"commission":0.0}));
                        }
                    } else {
                        let shares = target[i] / h.price.unwrap();
                        let size = shares - h.shares;
                        if size.abs() > 1e-12 {
                            trade_count += 1;
                            h.trade(*day, size, req.commission);
                            event_trades.push(json!({"asset_id":h.key,"symbol":h.asset.symbol,"action":if size>0.0{"buy"}else{"sell"},"shares":size.abs(),"price":h.price,"commission":fee}));
                        }
                        h.shares = shares;
                    }
                }
                let after_total: f64 = holdings.iter().map(Holding::value).sum();
                for h in &holdings {
                    after_weights.insert(h.key.clone(), json!(h.value() / after_total));
                }
                if !event_trades.is_empty() {
                    rebalances.push(json!({"date":day,"trades":event_trades,"weights_before":before_weights,"weights_after":after_weights,"commission_cost":fees}));
                }
            }
        }
        let value: f64 = holdings.iter().map(Holding::value).sum();
        let inflow: f64 = inflows.iter().sum();
        let daily = if previous > 0.0 && inflow > 0.0 {
            pre_flow / previous * (value / (pre_flow + inflow)) - 1.0
        } else if previous > 0.0 {
            (value - previous - inflow) / previous
        } else if inflow > 0.0 {
            value / inflow - 1.0
        } else {
            0.0
        };
        let mut weight = Map::new();
        weight.insert("date".into(), json!(day));
        for (i, h) in holdings.iter_mut().enumerate() {
            let after = h.value();
            h.profit += after - before[i] - inflows[i] - transfers[i];
            h.returns.push(metrics::clean_return(
                if h.previous > 0.0 && before[i] + inflows[i] > 0.0 {
                    before[i] / h.previous * ((after - transfers[i]) / (before[i] + inflows[i]))
                        - 1.0
                } else if inflows[i] > 0.0 {
                    (after - transfers[i]) / inflows[i] - 1.0
                } else {
                    0.0
                },
            ));
            h.previous = after;
            if value > 0.0 {
                let w = weight
                    .get(if h.asset.cash() {
                        &h.key
                    } else {
                        &h.asset.symbol
                    })
                    .and_then(Value::as_f64)
                    .unwrap_or(0.0)
                    + after / value;
                weight.insert(
                    if h.asset.cash() {
                        h.key.clone()
                    } else {
                        h.asset.symbol.clone()
                    },
                    json!(w),
                );
            }
        }
        weights.push(Value::Object(weight));
        equity.push(value);
        returns.push(metrics::clean_return(daily));
        previous = value;
    }
    let contributed: f64 = holdings.iter().map(|h| h.contributed).sum();
    if contributed <= 0.0 {
        return Err(Error::validation("기간 내에 실행된 투자가 없습니다."));
    }
    let stats = metrics::statistics(&dates, &equity, &returns, contributed, 1.0, trade_count);
    let mut individual = Map::new();
    let mut details = Map::new();
    let mut composition = vec![];
    for h in &holdings {
        let mut item = json!({"asset_id":h.key,"symbol":h.asset.symbol,"weight":h.contributed/contributed,"amount":h.contributed,"return":if h.contributed>0.0{h.profit/h.contributed*100.0}else{0.0},"start_price":if h.buy_size>0.0{Some(h.buy_notional/h.buy_size)}else if h.asset.cash(){Some(1.0)}else{None},"end_price":if h.asset.cash(){Some(1.0)}else{h.price},"investment_type":h.asset.investment_type,"dca_periods":if h.asset.dca(){Some(h.executed)}else{None},"final_value":h.value(),"trades":h.trades.len(),"sharpe_ratio":metrics::sharpe(&h.returns),"asset_type":h.asset.asset_type});
        if h.asset.cash() {
            item["asset_type"] = json!("cash");
        } else {
            details.insert(h.key.clone(), json!({"trade_log":h.trades}));
        }
        individual.insert(h.key.clone(), item);
        composition.push(json!({"asset_id":h.key,"symbol":h.asset.symbol,"weight":h.contributed/contributed,"amount":h.contributed,"investment_type":h.asset.investment_type,"dca_periods":if h.asset.dca(){Some(h.executed)}else{None},"asset_type":h.asset.asset_type}));
    }
    let ordered = holdings.iter().map(|h| &individual[&h.key]);
    let results:Vec<_>=ordered.map(|v|json!({"asset_id":v["asset_id"],"ticker":v["symbol"],"final_equity":v["final_value"],"total_return_pct":v["return"],"sharpe_ratio":v["sharpe_ratio"],"weight":v["weight"],"amount":v["amount"],"trades":v["trades"],"win_rate":null,"asset_type":v["asset_type"]})).collect();
    Ok(
        json!({"status":"success","data":{"portfolio_result":{"total_equity":stats["Final_Value"],"total_return_pct":stats["Total_Return"]},"portfolio_statistics":stats,"individual_returns":individual,"individual_results":results,"portfolio_composition":composition,"strategy_details":details,"equity_curve":curve(&dates,&equity,1.0),"daily_returns":curve(&dates,&returns,100.0),"weight_history":weights,"rebalance_history":rebalances,"warnings":warnings}}),
    )
}

fn technical(req: &BacktestRequest, data: &Histories, cancel: &CancellationToken) -> Result<Value> {
    let mut curves = BTreeMap::new();
    let mut details = Map::new();
    let mut individual = Map::new();
    let mut assets = vec![];
    let dates: Vec<_> = (0..=(req.end_date - req.start_date).num_days())
        .map(|d| req.start_date + Duration::days(d))
        .collect();
    let mut warnings = vec![];
    let mut wins = 0;
    let mut trades = 0;
    let mut realized_pnl = vec![];
    for (idx, a) in req.portfolio.iter().enumerate() {
        checked(cancel)?;
        if a.amount() <= 0.0 {
            warnings.push(format!(
                "종목 {} 백테스트 실패: 투자금액은 0보다 커야 합니다.",
                a.symbol
            ));
            continue;
        }
        let key = a.id(idx);
        let (equity, stats, n, w) = if a.cash() {
            (
                BTreeMap::new(),
                json!({"total_trades":0,"win_rate_pct":0.0,"max_drawdown_pct":0.0,"sharpe_ratio":0.0,"final_equity":a.amount()}),
                0,
                0,
            )
        } else {
            let Some(history) = data.get(&a.symbol) else {
                warnings.push(format!(
                    "종목 {} 백테스트 실패: 가격 데이터가 없습니다.",
                    a.symbol
                ));
                continue;
            };
            let mut bars: Vec<Bar> = history
                .bars
                .iter()
                .filter(|b| b.date >= req.start_date && b.date <= req.end_date)
                .cloned()
                .collect();
            for b in &mut bars {
                let f = fx(&history.currency, b.date, data)?;
                b.open *= f;
                b.high *= f;
                b.low *= f;
                b.close *= f;
            }
            let valuations = dates
                .iter()
                .map(|day| {
                    let n = history.bars.partition_point(|b| b.date <= *day);
                    let price = if n == 0 {
                        0.0
                    } else {
                        history.bars[n - 1].close * fx(&history.currency, *day, data)?
                    };
                    Ok((*day, price))
                })
                .collect::<Result<Vec<_>>>()?;
            let began = std::time::Instant::now();
            let mut output = strategy::run(
                &req.strategy,
                req.strategy_params.as_ref(),
                &strategy::StrategyMarket {
                    bars: &bars,
                    valuations: &valuations,
                },
                a.amount(),
                req.commission,
                cancel,
            )?;
            output.stats["ticker"] = json!(a.symbol);
            output.stats["strategy"] = json!(req.strategy);
            output.stats["start_date"] = json!(req.start_date);
            output.stats["end_date"] = json!(req.end_date);
            output.stats["duration_days"] = json!((req.end_date - req.start_date).num_days());
            output.stats["execution_time_seconds"] = json!(began.elapsed().as_secs_f64());
            output.stats["timestamp"] = json!(chrono::Utc::now());
            (
                dates
                    .iter()
                    .zip(&output.equity)
                    .map(|(day, e)| (*day, *e))
                    .collect(),
                output.stats,
                output.trades,
                output.wins,
            )
        };
        if let Some(log) = stats["trade_log"].as_array() {
            realized_pnl.extend(log.iter().filter_map(|t| t["PnL"].as_f64()));
        }
        trades += n;
        wins += w;
        let final_value = stats["final_equity"].as_f64().unwrap();
        individual.insert(key.clone(),json!({"asset_id":key,"asset_type":a.asset_type,"symbol":a.symbol,"weight":0.0,"amount":a.amount(),"return":(final_value/a.amount()-1.0)*100.0,"initial_value":a.amount(),"final_value":final_value,"trades":n,"win_rate":if n>0{Some(w as f64/n as f64*100.0)}else{None}}));
        details.insert(key.clone(), stats);
        curves.insert(key.clone(), equity);
        assets.push((key, a));
    }
    let amount: f64 = assets.iter().map(|(_, a)| a.amount()).sum();
    if amount <= 0.0 {
        return Err(Error::validation("모든 종목의 백테스트가 실패했습니다."));
    }
    let mut equity = vec![];
    let mut weights = vec![];
    for d in &dates {
        let values: Vec<_> = assets
            .iter()
            .map(|(key, a)| {
                curves[key]
                    .range(..=*d)
                    .next_back()
                    .map_or(a.amount(), |(_, v)| *v)
            })
            .collect();
        let total: f64 = values.iter().sum();
        equity.push(total);
        let mut weight = Map::new();
        weight.insert("date".into(), json!(d));
        for ((key, _), v) in assets.iter().zip(values) {
            weight.insert(
                key.clone(),
                json!(if total > 0.0 { v / total } else { 0.0 }),
            );
        }
        weights.push(weight);
    }
    for (key, a) in &assets {
        individual[key]["weight"] = json!(a.amount() / amount);
    }
    let returns = metrics::daily(&equity);
    let mut stats = metrics::statistics(
        &dates,
        &equity,
        &returns,
        amount,
        equity[0] / amount,
        trades,
    );
    let duration = (req.end_date - req.start_date).num_days();
    stats["Start"] = json!(req.start_date);
    stats["End"] = json!(req.end_date);
    stats["Duration"] = json!(format!("{duration} days"));
    stats["Annual_Return"] =
        json!((equity.last().unwrap() / amount).powf(365.25 / duration as f64) * 100.0 - 100.0);
    stats["Trade_Win_Rate"] = json!(if trades > 0 {
        Some(wins as f64 / trades as f64 * 100.0)
    } else {
        None
    });
    stats["Profit_Factor"] = json!(metrics::profit_factor(&realized_pnl));
    let results:Vec<_>=assets.iter().map(|(key,_)|{let v=&individual[key];json!({"asset_id":key,"asset_type":v["asset_type"],"ticker":v["symbol"],"final_equity":v["final_value"],"total_return_pct":v["return"],"sharpe_ratio":details[key]["sharpe_ratio"],"weight":v["weight"],"amount":v["amount"],"trades":v["trades"],"win_rate":v["win_rate"]})}).collect();
    let composition: Vec<_> = assets
        .iter()
        .map(|(key, a)| json!({"asset_id":key,"symbol":a.symbol,"weight":a.amount()/amount,"amount":a.amount(),"asset_type":a.asset_type}))
        .collect();
    Ok(
        json!({"status":"success","data":{"portfolio_result":{"total_equity":stats["Final_Value"],"total_return_pct":stats["Total_Return"]},"portfolio_statistics":stats,"individual_returns":individual,"individual_results":results,"portfolio_composition":composition,"strategy_details":details,"equity_curve":curve(&dates,&equity,1.0),"daily_returns":curve(&dates,&returns,100.0),"weight_history":weights,"rebalance_history":[],"warnings":warnings}}),
    )
}
