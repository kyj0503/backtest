import sys
import os
import logging
from datetime import date, timedelta
from sqlalchemy import text

# Add parent directory to path to allow importing app modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.services.database.connection_manager import DatabaseConnectionManager
from app.services.yfinance_db import save_ticker_data
from app.utils.data_fetcher import data_fetcher

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def update_all_stock_data(batch_size: int = 50, limit: int = None):
    """
    Update all stock data daily.
    - Fetches last 5 years of data with auto_adjust=True (handles splits automatically)
    - Overwrites DB data
    """
    logger.info("Starting daily stock data update...")
    
    engine = DatabaseConnectionManager.get_engine()
    conn = engine.connect()
    
    try:
        # Get all tickers from DB
        tickers = conn.execute(text("SELECT ticker FROM stocks")).fetchall()
        tickers = [t[0] for t in tickers]
        
        if limit:
            logger.info(f"Limiting update to first {limit} tickers.")
            tickers = tickers[:limit]
        
        logger.info(f"Found {len(tickers)} tickers to update.")
        
        success_count = 0
        fail_count = 0
        
        for i, ticker in enumerate(tickers):
            try:
                logger.info(f"[{i+1}/{len(tickers)}] Updating {ticker}...")
                
                # Fetch last 5 years of data
                # auto_adjust=True is default in data_fetcher (via yfinance history)
                start_date = date.today() - timedelta(days=365*5)
                end_date = date.today()
                
                df = data_fetcher.fetch_stock_data(
                    ticker,
                    start_date=start_date,
                    end_date=end_date,
                    use_cache=False 
                )
                
                if df is not None and not df.empty:
                    # Save to DB (upsert)
                    rows_updated = save_ticker_data(ticker, df)
                    logger.info(f"✓ {ticker}: {rows_updated} rows updated/inserted")
                    success_count += 1
                else:
                    logger.warning(f"⚠ {ticker}: No data fetched")
                    fail_count += 1
                    
            except Exception as e:
                logger.error(f"✗ {ticker}: Update failed - {e}")
                fail_count += 1
                continue
                
        logger.info(f"Daily update completed. Success: {success_count}, Failed: {fail_count}")
        
    except Exception as e:
        logger.error(f"Critical error during daily update: {e}")
        raise
    finally:
        conn.close()

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--limit", type=int, help="Limit number of tickers to update (for testing)")
    args = parser.parse_args()
    
    update_all_stock_data(limit=args.limit)
