from src.market_data import MStockAPI
from src.option_selector import OptionSelector
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def probe_options():
    api = MStockAPI()
    if not api.access_token:
        print("No access token. Authenticate first.")
        return

    # 1. Get Spot Prices
    indices = [
        ("NIFTY 50", "NSE", "NIFTY50"),
        ("SENSEX", "BSE", "SENSEX")
    ]
    
    print(f"\n{'UNDERLYING':<15} | {'SPOT PRICE':<10} | {'ATM STRIKE':<10}")
    print("-" * 50)
    
    spots = {}
    for name, exc, key in indices:
        quote = api.get_quote(name, exc)
        if quote:
            price = quote.get('last_price', 0)
            print(f"{name:<15} | {price:<10.2f} | {int(round(price, -2))}")
            spots[key] = price
        else:
             print(f"{name:<15} | {'ERR':<10} | -")

    print("\n\nTesting Option Symbols & Quotes:")
    print(f"{'UNDERLYING':<10} | {'TYPE':<5} | {'GENERATED SYMBOL':<25} | {'EXC':<5} | {'QUOTE'}")
    print("-" * 75)

    test_cases = [
        ("NIFTY50", spots.get("NIFTY50", 24000), "CE", "NFO"),
        ("SENSEX", spots.get("SENSEX", 80000), "CE", "BFO"),
        ("SENSEX", spots.get("SENSEX", 80000), "CE", "BSE") # Test BSE for options too?
    ]

    for und, spot, otype, exc in test_cases:
        if spot == 0: continue
        
        # 1. Select Option
        try:
            strike, opt_sym = OptionSelector.select_option(und, spot, otype, depth=0)
            
            # 2. Try Fetch Quote
            quote = api.get_quote(opt_sym, exc)
            
            if quote:
                lp = quote.get('last_price', 'N/A')
                print(f"{und:<10} | {otype:<5} | {opt_sym:<25} | {exc:<5} | Success ({lp})")
            else:
                print(f"{und:<10} | {otype:<5} | {opt_sym:<25} | {exc:<5} | FAILED (No Data)")
                
        except Exception as e:
            print(f"{und:<10} | {otype:<5} | {'ERROR':<25} | {exc:<5} | {e}")

if __name__ == "__main__":
    probe_options()
