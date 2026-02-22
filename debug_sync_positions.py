from src.market_data import MStockAPI
import logging

# Configure logging to print to console
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def debug_sync():
    api = MStockAPI()
    if not api.access_token:
        print("No access token. Authenticate first.")
        return

    print("\nFETCHING HOLDINGS (Equity/Demat) FROM BROKER...")
    positions_dict = api.get_positions()
    
    if positions_dict:
        print(f"API returned {len(positions_dict)} holdings.")
        for (symbol, exc), data in positions_dict.items():
            print(f"  {symbol} ({exc}): {data.get('qty')} qty")
    else:
        print("No holdings found.")

    print("\nFETCHING NET POSITIONS (F&O/Intraday) FROM BROKER...")
    net_positions = api.get_net_positions()
    
    if not net_positions:
        print("API returned No Net Positions.")
        return

    print(f"API returned {len(net_positions)} net positions.")
    
    print("\nANALYZING NET POSITIONS:")
    print(f"{'SYMBOL':<30} | {'EXCHANGE':<10} | {'QTY':<10} | {'STATUS'}")
    print("-" * 70)

    # Convert list to dict format for the loop below if needed, or just iterate list
    # The original loop expected dict items. Let's adjust for list of dicts.
    
    for pos_data in net_positions:
        symbol = pos_data.get('tradingsymbol', '')
        exchange = pos_data.get('exchange', '')
        qty = pos_data.get('quantity', 0) # API usually uses 'quantity' or 'netQuantity'
        if qty == 0: qty = pos_data.get('netQuantity', 0)
        
        status = "OK"
        reason = ""

        # Replication of filtering logic
        if int(qty) == 0: # Net position is 0 (Closed)
            status = "SKIPPED"
            reason = "Qty = 0 (Closed)"
        elif exchange not in ['NSE', 'NFO', 'BSE', 'BFO']:
            status = "SKIPPED" 
            reason = f"Exchange {exchange} not supported"
        else:
             # Symbol parsing check
            symbol_clean = symbol.replace('-', ' ')
            parts = symbol_clean.split()
            if len(parts) < 3:
                status = "SKIPPED"
                reason = "Symbol format invalid (len < 3)"
            
            option_type = parts[-1] if parts[-1] in ['CE', 'PE'] else None
            if not option_type:
                 status = "SKIPPED"
                 reason = "Option Type not CE/PE"

        print(f"{symbol:<30} | {exchange:<10} | {qty:<10} | {status} {reason}")
        
        # Test Quote for VALID symbols
        if status == "OK" and symbol:
             print(f"   [TESTING QUOTE] Fetching quote for '{symbol}' on '{exchange}'...")
             q = api.get_quote(symbol, exchange)
             if q:
                 lp = q.get('last_price', 'N/A')
                 print(f"   [SUCCESS] LTP: {lp}")
             else:
                 print(f"   [FAILED] Could not fetch quote. Symbol format might be wrong for get_quote.")

    print("\nDone.")
    return

if __name__ == "__main__":
    debug_sync()
