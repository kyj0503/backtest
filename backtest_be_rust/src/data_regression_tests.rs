use super::*;

#[tokio::test]
#[ignore = "requires a disposable MySQL with schema.sql; RUST_TEST_DATABASE=1"]
async fn t01_t02_unverified_snapshots_and_impossible_cached_ohlc_are_refetched() {
    assert_eq!(std::env::var("RUST_TEST_DATABASE").as_deref(), Ok("1"));
    let mut source = DataSource::new().unwrap();
    let first = NaiveDate::from_ymd_opt(2023, 1, 2).unwrap();
    let last = first + Duration::days(39);
    let h = History {
        symbol: "ZZT01CACHE".into(),
        currency: "USD".into(),
        company_name: "test".into(),
        exchange: "synthetic".into(),
        first_trade_date: None,
        bars: (0..40)
            .map(|i| Bar {
                date: first + Duration::days(i),
                open: 50.,
                high: 50.,
                low: 50.,
                close: 50.,
                volume: 1000.,
            })
            .collect(),
    };
    source.fixtures = Some(Arc::new(Histories::from([(h.symbol.clone(), h.clone())])));
    source.save(&h, first, last).await.unwrap();
    let pool = source.pool.as_ref().unwrap();
    sqlx::query("UPDATE stocks SET info_json=JSON_SET(info_json,'$.rust_price_snapshot.version',3) WHERE ticker='ZZT01CACHE'").execute(pool).await.unwrap();
    assert!(
        source
            .cached(&h.symbol, first, last)
            .await
            .unwrap()
            .is_none()
    );
    assert!(
        source
            .history(&h.symbol, first, last)
            .await
            .unwrap()
            .bars
            .iter()
            .all(|b| b.close == 50.)
    );
    assert!(
        source
            .cached(&h.symbol, first, last)
            .await
            .unwrap()
            .is_some()
    );
    sqlx::query("UPDATE daily_prices SET open=1 WHERE stock_id=(SELECT id FROM stocks WHERE ticker='ZZT01CACHE') AND date=?").bind(first).execute(pool).await.unwrap();
    assert!(
        source
            .cached(&h.symbol, first, last)
            .await
            .unwrap()
            .is_none()
    );
    source.cache.lock().await.clear();
    assert_eq!(
        source.history(&h.symbol, first, last).await.unwrap().bars[0].open,
        50.
    );
}

#[tokio::test(flavor = "multi_thread", worker_threads = 4)]
#[ignore = "requires a disposable MySQL with schema.sql; RUST_TEST_DATABASE=1"]
async fn r03_concurrent_snapshot_reads_never_accept_another_ranges_rows() {
    assert_eq!(std::env::var("RUST_TEST_DATABASE").as_deref(), Ok("1"));
    let source = DataSource::new().unwrap();
    let first = NaiveDate::from_ymd_opt(2023, 1, 2).unwrap();
    let last = first + Duration::days(39);
    let make = |offset| History {
        symbol: "ZZRACE".into(),
        currency: "USD".into(),
        company_name: "audit".into(),
        exchange: "test".into(),
        first_trade_date: None,
        bars: [
            first + Duration::days(offset),
            last + Duration::days(offset),
        ]
        .into_iter()
        .map(|date| Bar {
            date,
            open: 100.0,
            high: 100.0,
            low: 100.0,
            close: 100.0,
            volume: 1000.0,
        })
        .collect(),
    };
    let early = make(0);
    let late = make(365);
    source.save(&early, first, last).await.unwrap();
    assert_eq!(
        source
            .cached("ZZRACE", first, last)
            .await
            .unwrap()
            .unwrap()
            .bars
            .len(),
        2
    );
    let barrier = Arc::new(tokio::sync::Barrier::new(5));
    let writer_source = source.clone();
    let writer_barrier = barrier.clone();
    let writer = tokio::spawn(async move {
        writer_barrier.wait().await;
        for i in 0..500 {
            let h = if i % 2 == 0 { &late } else { &early };
            writer_source
                .save(h, h.bars[0].date, h.bars[1].date)
                .await
                .unwrap();
            tokio::task::yield_now().await;
        }
    });
    let mut readers = Vec::new();
    for _ in 0..4 {
        let source = source.clone();
        let barrier = barrier.clone();
        readers.push(tokio::spawn(async move {
            barrier.wait().await;
            let (mut hits, mut invalid) = (0, 0);
            for _ in 0..500 {
                if let Some(h) = source.cached("ZZRACE", first, last).await.unwrap() {
                    hits += 1;
                    if h.bars.len() != 2
                        || h.bars[0].date != first
                        || h.bars.last().unwrap().date != last
                    {
                        invalid += 1;
                    }
                }
                tokio::task::yield_now().await;
            }
            (hits, invalid)
        }));
    }
    writer.await.unwrap();
    let (mut hits, mut invalid) = (0, 0);
    for reader in readers {
        let (a, b) = reader.await.unwrap();
        hits += a;
        invalid += b;
    }
    let result = json!({"attempts":2000,"snapshot_writes":500,"cache_hits":hits,"invalid_histories":invalid});
    if let Ok(directory) = std::env::var("RUST_TEST_REPORT_DIR") {
        std::fs::write(
            format!("{directory}/cache-race.json"),
            serde_json::to_vec_pretty(&result).unwrap(),
        )
        .unwrap();
    }
    println!("{result}");
    assert!(hits > 0, "cache hit path must be exercised");
    assert_eq!(invalid, 0, "metadata and rows must come from one snapshot");
}
