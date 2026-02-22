from src.market_data import MStockAPI
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def probe_sensex():
    api = MStockAPI()
    if not api.access_token:
        print("No access token. Authenticate first.")
        return

    symbols_to_test = [
        ("SENSEX", "BSE"),
        ("SENSEX", "NSE"),
        ("BSE SENSEX", "BSE"),
        ("S&P BSE SENSEX", "BSE"),
        ("BSESENSEX", "BSE"),
        ("SENSEX 50", "NSE") # Maybe it's checking Sensex 50?
    ]

    print(f"{'SYMBOL':<20} | {'EXCHANGE':<10} | {'PRICE':<10} | {'MSG'}")
    print("-" * 60)

    for sym, exc in symbols_to_test:
        try:
            quote = api.get_quote(sym, exc)
            if quote:
                price = quote.get('last_price', 0)
                print(f"{sym:<20} | {exc:<10} | {price:<10} | Success")
            else:
                print(f"{sym:<20} | {exc:<10} | {'N/A':<10} | No Data")
        except Exception as e:
            print(f"{sym:<20} | {exc:<10} | {'ERR':<10} | {e}")

if __name__ == "__main__":
    probe_sensex()
