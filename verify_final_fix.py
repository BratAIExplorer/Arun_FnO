from src.market_data import MStockAPI
import logging

def verify_fix():
    api = MStockAPI()
    symbol = "NIFTY2621025500PE"
    exchange = "NFO"
    
    print(f"Verifying Quote Fetch for {symbol} on {exchange}...")
    quote = api.get_quote(symbol, exchange)
    
    if quote:
        print(f"SUCCESS: LTP = {quote.get('last_price')}")
    else:
        print("FAILED: Quote still returning 400 or None.")

if __name__ == "__main__":
    verify_fix()
