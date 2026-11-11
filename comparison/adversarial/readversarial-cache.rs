// Appended only to an isolated source copy. Owning DataSource methods are unchanged.
#[cfg(test)]
mod readversarial_probe {
    use super::*;

    #[tokio::test(flavor = "multi_thread", worker_threads = 4)]
    #[ignore = "disposable backtest-readversarial-db only"]
    async fn snapshot_read_race() {
        assert_eq!(std::env::var("DATABASE_HOST").unwrap(), "backtest-readversarial-db");
        let source = DataSource::new().unwrap();
        let first = NaiveDate::from_ymd_opt(2023, 1, 2).unwrap();
        let last = first + Duration::days(39);
        let make = |offset| History {
            symbol: "ZZRACE".into(), currency: "USD".into(),
            company_name: "isolated audit".into(), exchange: "test".into(), first_trade_date: None,
            bars: [first + Duration::days(offset), last + Duration::days(offset)]
                .into_iter().map(|date| Bar {date,open:100.0,high:100.0,low:100.0,close:100.0,volume:1000.0}).collect(),
        };
        let early = make(0);
        let late = make(365);
        source.save(&early, first, last).await.unwrap();
        let writer_source = source.clone();
        let writer = tokio::spawn(async move {
            for i in 0..500 {
                let h = if i % 2 == 0 { &late } else { &early };
                writer_source.save(h,h.bars[0].date,h.bars[1].date).await.unwrap();
                tokio::task::yield_now().await;
            }
        });
        let mut readers = Vec::new();
        for _ in 0..4 {
            let source = source.clone();
            readers.push(tokio::spawn(async move {
                let (mut hits, mut malformed) = (0,0);
                for _ in 0..500 {
                    if let Some(h) = source.cached("ZZRACE",first,last).await.unwrap() {
                        hits += 1;
                        if h.bars.len() != 2 {malformed += 1;}
                    }
                    tokio::task::yield_now().await;
                }
                (hits,malformed)
            }));
        }
        writer.await.unwrap();
        let (mut hits,mut malformed)=(0,0);
        for r in readers {let (a,b)=r.await.unwrap();hits+=a;malformed+=b;}
        let result=json!({"attempts":2000,"snapshot_writes":500,"cache_hits":hits,
            "accepted_incomplete_histories":malformed,"expected_incomplete_histories":0,
            "test_hook_changes_to_production_methods":false});
        std::fs::write("/reports/cache-race.json",serde_json::to_vec_pretty(&result).unwrap()).unwrap();
        println!("{result}");
        assert!(hits>0,"audit did not exercise the cache");
        // Evidence collector, not a passing correctness assertion.
    }
}
