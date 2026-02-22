from src.market_data import MStockAPI
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_bn_quote():
    api = MStockAPI()
    
    symbol = "BANKNIFTY26FEB60700PE"
    exchange = "NFO"
    
    print(f"\nProbing quote for {exchange}:{symbol}...")
    quote = api.get_quote(symbol, exchange)
    
    if quote:
        print(f"SUCCESS!")
        print(f"LTP: {quote.get('last_price')}")
        print(f"Full Data: {quote}")
    else:
        print(f"FAILED to fetch quote.")
        
    # Also test with hyphens just in case
    symbol_hyphen = "BANKNIFTY-24Feb2026-60700-PE"
    print(f"\nProbing quote for {exchange}:{symbol_hyphen}...")
    quote2 = api.get_quote(symbol_hyphen, exchange)
    if quote2:
        print(f"SUCCESS (Hyphen)!")
        print(f"LTP: {quote2.get('last_price')}")
    else:
        print(f"FAILED (Hyphen).")

if __name__ == "__main__":
    test_bn_quote()
