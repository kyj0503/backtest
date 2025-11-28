import yfinance as yf
import pandas as pd

def check_splits_history():
    ticker = "TQQQ"
    print(f"Fetching splits history for {ticker}...")
    stock = yf.Ticker(ticker)
    splits = stock.splits
    print("\nSplits history:")
    print(splits)
    
    if not splits.empty:
        last_split_date = splits.index.max()
        print(f"\nLast split date: {last_split_date}")

if __name__ == "__main__":
    check_splits_history()
