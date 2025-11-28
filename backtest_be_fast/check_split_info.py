import yfinance as yf
import json
from datetime import datetime

def check_split_metadata():
    ticker = "TQQQ"
    print(f"Fetching info for {ticker}...")
    stock = yf.Ticker(ticker)
    info = stock.info
    
    print("\nSplit related info:")
    keys = [k for k in info.keys() if 'split' in k.lower()]
    for k in keys:
        print(f"{k}: {info[k]}")
        
    if 'lastSplitDate' in info:
        ts = info['lastSplitDate']
        if ts:
            dt = datetime.fromtimestamp(ts)
            print(f"\nlastSplitDate (formatted): {dt}")

if __name__ == "__main__":
    check_split_metadata()
