import yfinance as yf
import pandas as pd

def test_split():
    ticker = "SMCI"
    # Split date was roughly 2024-10-01
    start = "2024-09-25"
    end = "2024-10-05"
    
    print(f"Fetching {ticker} from {start} to {end} with auto_adjust=True")
    stock = yf.Ticker(ticker)
    df = stock.history(start=start, end=end, auto_adjust=True)
    
    print("Columns:", df.columns)
    print("\nData sample:")
    print(df[['Close', 'Stock Splits']])
    
    # Check if Stock Splits is present and has values
    if 'Stock Splits' in df.columns:
        splits = df[df['Stock Splits'] != 0]
        if not splits.empty:
            print("\nSplits detected:")
            print(splits['Stock Splits'])
        else:
            print("\nNo splits detected in this range.")
    else:
        print("\n'Stock Splits' column not found.")

if __name__ == "__main__":
    test_split()
