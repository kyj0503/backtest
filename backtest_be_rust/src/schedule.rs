use chrono::{Datelike, Duration, NaiveDate};

pub fn frequency(s: &str) -> Option<(bool, u32)> {
    match s {
        "weekly_1" => Some((true, 1)),
        "weekly_2" => Some((true, 2)),
        "monthly_1" => Some((false, 1)),
        "monthly_2" => Some((false, 2)),
        "monthly_3" => Some((false, 3)),
        "monthly_6" => Some((false, 6)),
        "monthly_12" => Some((false, 12)),
        _ => None,
    }
}
pub fn schedule(start: NaiveDate, end: NaiveDate, frequency_name: &str) -> Vec<NaiveDate> {
    let Some((weekly, interval)) = frequency(frequency_name) else {
        return vec![];
    };
    let mut dates = vec![];
    let mut cursor = start;
    let nth = (start.day() - 1) / 7;
    loop {
        cursor = if weekly {
            cursor + Duration::weeks(interval as i64)
        } else {
            let month = cursor.month0() + interval;
            let year = cursor.year() + (month / 12) as i32;
            let first = NaiveDate::from_ymd_opt(year, month % 12 + 1, 1).unwrap();
            let offset = (start.weekday().num_days_from_monday() + 7
                - first.weekday().num_days_from_monday())
                % 7;
            let mut candidate = first + Duration::days((offset + nth * 7) as i64);
            if candidate.month() != first.month() {
                candidate -= Duration::weeks(1);
            }
            candidate
        };
        if cursor > end {
            break;
        }
        dates.push(cursor);
    }
    dates
}
