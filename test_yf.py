import yfinance as yf
import pandas as pd
from datetime import datetime, timedelta
import pytz

def test_yf_bridge():
    # Nifty 50 on Yahoo Finance
    symbol = "NIFTY_FIN_SERVICE.NS" # Try this one
    
    print(f"Fetching 15m data for {symbol} from yfinance...")
    
    try:
        # Fetch 15m data for current day
        df = yf.download(symbol, period="2d", interval="15m")
        
        if df is not None and len(df) > 0:
            print(f"Successfully fetched {len(df)} candles.")
            print("First 3 candles:")
            print(df.head(3))
            print("Last 3 candles:")
            print(df.tail(3))
            
            # Check for today's data
            ist = pytz.timezone("Asia/Kolkata")
            now = datetime.now(ist)
            today_str = now.strftime("%Y-%m-%d")
            
            # Handle multi-index columns if present in newer yfinance versions
            df.columns = [col[0] if isinstance(col, tuple) else col for col in df.columns]
            
            print(f"\nCandles for today ({today_str}):")
            today_df = df[df.index.strftime('%Y-%m-%d') == today_str]
            print(len(today_df))
            if len(today_df) > 0:
                print(today_df.head(1))
                print(today_df.tail(1))
        else:
            print("No data returned from yfinance.")
            
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    test_yf_bridge()
