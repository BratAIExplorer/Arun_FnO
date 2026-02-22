"""
Debug Order Placement
Tries to place a LIMIT order (far from market price) to verify if Token+Symbol combination is accepted.
"""

from src.market_data import MStockAPI
from src.symbol_master import SymbolMaster
from datetime import date
import logging
import json

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def debug_order():
    print("="*60)
    print("DEBUG ORDER PLACEMENT")
    print("="*60)
    
    try:
        api = MStockAPI()
        print("API Initialized")
    except Exception as e:
        print(f"API Init Failed: {e}")
        return

    # TEST EQUITY ORDER (YESBANK)
    # To isolate if the issue is specific to F&O or API wide.
    symbol = "YESBANK"
    exchange = "NSE"
    
    # 2. Get Token
    print(f"\nFetching Token for {symbol}...")
    quote = api.get_quote(symbol, exchange)
    
    if not quote:
        print("Failed to get quote/token")
        return
        
    token = str(quote.get('instrument_token', ''))
    print(f"Token Fetched: {token}")
    print(f"   LTP: {quote.get('last_price')}")
    
    # TEST F&O ORDER (BANKNIFTY) - Final Verification
    symbol = "BANKNIFTY26FEB59900CE"
    exchange = "NFO" 
    
    qty = 30
    price = 1.0 
    
    url = f"{api.base_url}/orders/regular" 
    
    # Payload (Form Data)
    payload = {
        "tradingsymbol": symbol,
        "exchange": exchange,
        "transaction_type": "BUY",
        "order_type": "LIMIT",
        "quantity": str(qty),
        "product": "NRML",        # Use NRML for F&O Carryforward (or MIS for Intraday)
                                  # Documentation example showed MIS.
                                  # Let's try MARGIN (which failed before) logic 
                                  # or standard NRML.
                                  # The user's original code used "MARGIN".
                                  # Let's start with "NRML" as it's safer for F&O acceptance?
                                  # Actually, doc example used "MIS".
        "validity": "DAY",
        "price": str(price),
        # Token? Let's check if it works WITHOUT token first?
        # If not, add token.
    }
    
    # Mstock usually requires token for F&O if symbol is not standard?
    # Let's try WITHOUT token first (as per doc). 
    # If it fails, I will add token in next iteration. 
    # Actually, I should probably generate/fetch token just in case 
    # but let's be pure to the Doc first.
    
    print(f"Testing F&O Payload: {payload}")
    
    try:
        headers = {
            **api.get_headers(), 
            "Content-Type": "application/x-www-form-urlencoded"
        }
        
        import requests
        response = requests.post(url, data=payload, headers=headers)
        
        print(f"Status: {response.status_code}")
        try:
            resp_data = response.json()
            print(f"Response: {resp_data}")
            
            # Handle List response
            if isinstance(resp_data, list):
                if resp_data and resp_data[0].get("status") == "success":
                    print(f"SUCCESS! F&O Order Placed!")
                    print("PLEASE CANCEL THIS ORDER IMMEDIATELY")
                else:
                    print("Failed (List format)")
            elif isinstance(resp_data, dict):
                 if resp_data.get("status") == "success":
                    print(f"SUCCESS! F&O Order Placed!")
                    print("PLEASE CANCEL THIS ORDER IMMEDIATELY")
        except:
             print(f"Raw Response: {response.text}")

    except Exception as e:
        print(f"Exception: {e}")

if __name__ == "__main__":
    debug_order()
