use chrono::{Duration, NaiveDate};
use serde_json::{Value, json};

pub fn mean(v: &[f64]) -> f64 {
    if v.is_empty() {
        0.0
    } else {
        v.iter().sum::<f64>() / v.len() as f64
    }
}
pub fn stddev(v: &[f64]) -> f64 {
    if v.len() < 2 {
        return 0.0;
    }
    let m = mean(v);
    (v.iter().map(|x| (x - m).powi(2)).sum::<f64>() / (v.len() - 1) as f64).sqrt()
}
// All public risk statistics use calendar-daily marked wealth, including closed
// sessions. Ignore only numerical noise below one billionth of a percent.
pub fn clean_return(r: f64) -> f64 {
    if r.abs() <= 1e-11 { 0.0 } else { r }
}
pub fn calendar_curve(dates: &[NaiveDate], equity: &[f64]) -> (Vec<NaiveDate>, Vec<f64>) {
    let mut days = Vec::new();
    let mut values = Vec::new();
    let mut i = 0;
    for offset in 0..=(*dates.last().unwrap() - dates[0]).num_days() {
        let day = dates[0] + Duration::days(offset);
        while i + 1 < dates.len() && dates[i + 1] <= day {
            i += 1;
        }
        days.push(day);
        values.push(equity[i]);
    }
    (days, values)
}
pub fn sharpe(v: &[f64]) -> f64 {
    let std = stddev(v);
    if std * 365.0_f64.sqrt() * 100.0 <= 1e-9 {
        0.0
    } else {
        mean(v) / std * 365.0_f64.sqrt()
    }
}
pub fn daily(equity: &[f64]) -> Vec<f64> {
    equity
        .iter()
        .enumerate()
        .map(|(i, v)| {
            if i == 0 || equity[i - 1] <= 0.0 {
                0.0
            } else {
                clean_return(v / equity[i - 1] - 1.0)
            }
        })
        .collect()
}
/// Realized net dollar profit divided by realized net dollar loss.
/// No realized losses means the ratio is undefined, not an arbitrary constant.
pub fn profit_factor(pnl: &[f64]) -> Option<f64> {
    let gains: f64 = pnl.iter().filter(|p| **p > 0.0).sum();
    let losses: f64 = -pnl.iter().filter(|p| **p < 0.0).sum::<f64>();
    let ratio = gains / losses;
    (losses > 0.0 && ratio.is_finite()).then_some(ratio)
}
pub fn statistics(
    dates: &[NaiveDate],
    equity: &[f64],
    returns: &[f64],
    contributed: f64,
    start_ratio: f64,
    trades: usize,
) -> Value {
    let returns: Vec<f64> = returns.iter().copied().map(clean_return).collect();
    let duration = (*dates.last().unwrap() - dates[0]).num_days();
    let growth = returns.iter().fold(start_ratio, |v, r| v * (1.0 + r));
    let mut index = start_ratio;
    let mut peak = 1.0_f64;
    let mut dd = vec![];
    let (mut gain, mut loss, mut max_gain, mut max_loss) = (0, 0, 0, 0);
    for r in &returns {
        index *= 1.0 + r;
        peak = peak.max(index);
        let d = if peak > 0.0 {
            (index / peak - 1.0) * 100.0
        } else {
            0.0
        };
        dd.push(if d < -1e-9 { d } else { 0.0 });
        gain = if *r > 0.0 { gain + 1 } else { 0 };
        loss = if *r < 0.0 { loss + 1 } else { 0 };
        max_gain = max_gain.max(gain);
        max_loss = max_loss.max(loss);
    }
    let negatives: Vec<f64> = dd.iter().copied().filter(|d| *d < 0.0).collect();
    let volatility = stddev(&returns) * 365.0_f64.sqrt() * 100.0;
    json!({"Start":dates[0],"End":dates.last(),"Duration":format!("{duration} days"),"Initial_Value":contributed,
        "Final_Value":equity.last(),"Peak_Value":equity.iter().copied().fold(0.0_f64,f64::max),
        "Total_Return":(equity.last().unwrap()/contributed-1.0)*100.0,
        "Annual_Return":if duration>0 {(growth.max(0.0).powf(365.25/duration as f64)-1.0)*100.0} else {0.0},
        "Time_Weighted_Return":clean_return(growth-1.0)*100.0,"Return_Observation_Days_Per_Year":365,
        "Annualization_Basis":"calendar_daily","Annual_Volatility":if volatility<=1e-9 {0.0} else {volatility},"Sharpe_Ratio":sharpe(&returns),
        "Max_Drawdown":dd.iter().copied().fold(0.0_f64,f64::min),"Avg_Drawdown":mean(&negatives),
        "Max_Consecutive_Gains":max_gain,"Max_Consecutive_Losses":max_loss,"Total_Trading_Days":dates.len(),
        "Total_Trades":trades,"Positive_Days":returns.iter().filter(|r| **r>0.0).count(),
        "Negative_Days":returns.iter().filter(|r| **r<0.0).count(),
        "Win_Rate":returns.iter().filter(|r| **r>0.0).count() as f64/returns.len() as f64*100.0,
        "Profit_Factor":null})
}
