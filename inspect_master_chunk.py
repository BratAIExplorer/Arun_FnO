"""
Inspect Master Chunk
Streams Mstock Master file and prints YESBANK entry to verify payload format.
"""
import requests
import csv
from src.market_data import MStockAPI

def inspect_master():
    url = "https://api.mstock.trade/openapi/typeb/instruments/OpenAPIScripMaster"
    print(f"Streaming master from {url}...")
    
    try:
        response = requests.get(url, stream=True)
        response.raise_for_status()
        
        # Process line by line
        iterator = response.iter_lines(decode_unicode=True)
        
        # Header
        try:
            header = next(iterator)
            print(f"HEADER: {header}")
        except StopIteration:
            print("Empty file")
            return
            
        found = False
        limit = 50 
        count = 0
        
        for line in iterator:
            if not line: continue
            
            # Print first 50 lines unconditionally
            if count < limit:
                print(f"ROW {count}: {line}")
                count += 1
            else:
                break

    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    inspect_master()
