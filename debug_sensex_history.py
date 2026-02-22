from src.market_data import MStockAPI
import logging
import pandas as pd

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def probe_sensex_history():
    api = MStockAPI()
    if not api.access_token:
        print("No access token. Authenticate first.")
        return

    # Test cases: (Symbol, Exchange, Token)
    tests = [
        ("SENSEX", "BSE", "1"),
        ("SENSEX", "BSE", "51"), # Token found in all_instruments.json
        ("SENSEX", "BSE", "26008"), # Previous NSE token, just in case
        ("SENSEX", "NSE", "26008"),
        ("BSESENSEX", "BSE", "1"),
        ("S&P BSE SENSEX", "BSE", "1")
    ]

    print(f"{'SYMBOL':<20} | {'EXC':<5} | {'TOK':<8} | {'HISTORY STATUS'}")
    print("-" * 65)

    for sym, exc, tok in tests:
        try:
            # Try fetching just 1 day of daily data
            df = api.get_historical_data(sym, exc, tok, "day", days=5)
            if df is not None and not df.empty:
                last_close = df.iloc[-1]['close']
                print(f"{sym:<20} | {exc:<5} | {tok:<8} | Success ({len(df)} candles, Last: {last_close})")
            else:
                 print(f"{sym:<20} | {exc:<5} | {tok:<8} | Failed (Empty/None)")
        except Exception as e:
            print(f"{sym:<20} | {exc:<5} | {tok:<8} | Error: {e}")

if __name__ == "__main__":
    probe_sensex_history()
