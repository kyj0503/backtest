import logging
import time
from datetime import date, timedelta
from app.services.yfinance_db import _fetch_and_save_missing_data, _get_engine, save_ticker_data, _get_date_coverage
from sqlalchemy import text
import pandas as pd

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def verify_split_handling():
    ticker = "SMCI"
    # Split date was roughly 2024-10-01 (10:1 split)
    
    engine = _get_engine()
    conn = engine.connect()
    
    try:
        # 1. Clean up existing data for SMCI
        logger.info("Cleaning up existing data for SMCI...")
        conn.execute(text("DELETE FROM daily_prices WHERE stock_id = (SELECT id FROM stocks WHERE ticker = :t)"), {"t": ticker})
        conn.execute(text("DELETE FROM stocks WHERE ticker = :t"), {"t": ticker})
        conn.commit()
        
        # 2. Insert fake pre-split data (high prices) for a date before the split
        # Let's say we have data up to 2024-09-20 with pre-split prices (~$400 range)
        logger.info("Inserting fake pre-split data...")
        
        # Ensure stock exists
        conn.execute(text("INSERT INTO stocks (ticker, name, exchange, sector, industry, summary, info_json, last_info_update) VALUES (:t, 'Super Micro', 'NAS', 'Tech', 'Hardware', '', '{}', NOW())"), {"t": ticker})
        stock_id_row = conn.execute(text("SELECT id FROM stocks WHERE ticker = :t"), {"t": ticker}).fetchone()
        stock_id = stock_id_row[0]
        
        conn.commit()

        # 3. Insert fake pre-split data (high price)
        # SMCI split date: 2024-10-01 (10:1 split)
        # We insert high price data up to 2024-10-02 to simulate "already fetched but unadjusted" data
        split_date = date(2024, 10, 1)
        fake_date_end = date(2024, 10, 2)
        
        logger.info(f"Inserting fake pre-split data up to {fake_date_end}...")
        
        # Fake data: Price around $450 (pre-split level)
        dates = pd.date_range(start='2024-09-20', end=fake_date_end)
        fake_df = pd.DataFrame({
            'Open': [450.0] * len(dates),
            'High': [460.0] * len(dates),
            'Low': [440.0] * len(dates),
            'Close': [455.0] * len(dates),
            'Volume': [1000000] * len(dates),
            'StockSplits': [0.0] * len(dates)
        }, index=dates)
        
        save_ticker_data(ticker, fake_df)
        
        # 4. Trigger fetch for a range *after* the split date
        # This ensures the split date itself is NOT in the fetch range, testing the metadata check
        req_start = date(2024, 10, 5)
        req_end = date(2024, 10, 10)
        
        logger.info(f"Requesting data for {req_start} ~ {req_end} (Split date {split_date} is OUTSIDE this range)")
        
        conn = _get_engine().connect()
        stock_id_row = conn.execute(text("SELECT id FROM stocks WHERE ticker = :t"), {"t": ticker}).fetchone()
        stock_id = stock_id_row[0]
        db_min, db_max = _get_date_coverage(conn, stock_id) # Assuming ID 1 for SMCI after cleanup
        
        _fetch_and_save_missing_data(conn, _get_engine(), ticker, req_start, req_end, db_min, db_max)
        
        # 5. Verify data is corrected
        conn = _get_engine().connect()
        # Check a date that was previously "fake high"
        check_date = '2024-09-20'
        row = conn.execute(text("SELECT close FROM daily_prices WHERE stock_id = (SELECT id FROM stocks WHERE ticker = :t) AND date = :d"), {"t": ticker, "d": check_date}).fetchone()
        
        if row:
            price = float(row[0])
            logger.info(f"Price on {check_date} after fetch: {price:.4f}")
            
            if price < 100:
                logger.info("SUCCESS: Price is adjusted (post-split level). Retroactive split detection worked!")
            else:
                logger.error("FAILURE: Price is still high (pre-split level). Retroactive split detection failed.")
        else:
            logger.error(f"FAILURE: No data found for {check_date}")

    except Exception as e:
        logger.exception("Verification failed")
    finally:
        conn.close()

if __name__ == "__main__":
    verify_split_handling()
