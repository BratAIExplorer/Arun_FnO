
import requests
import os
import csv
from src.market_data import MStockAPI

def fetch_and_search_master():
    # Initialize API for headers/auth if needed (though this endpoint might be public)
    # We'll use the headers just in case
    try:
        api = MStockAPI()
        headers = api.get_headers()
    except:
        print("Could not init API, trying without headers...")
        headers = {}

    # URL retrieved from search results
    url = "https://api.mstock.trade/openapi/typeb/instruments/OpenAPIScripMaster"
    
    print(f"Downloading master from {url}...")
    try:
        response = requests.get(url, headers=headers, stream=True)
        response.raise_for_status()
        
        filename = "nfo_master.csv"
        with open(filename, 'wb') as f:
            for chunk in response.iter_content(chunk_size=8192): 
                f.write(chunk)
        print(f"Downloaded to {filename}")

        # Now search for NIFTY options
        print("\nSearching for Active NIFTY Options...")
        found_count = 0
        
        with open(filename, 'r', encoding='utf-8', errors='ignore') as f:
            # The file is CSV but might have different delimiters. Let's just read lines.
            header = f.readline()
            print(f"Header: {header.strip()}")
            
            for line in f:
                # We are looking for NIFTY options. 
                # Identifying features: "NIFTY", "PE", "25750" (or near ATM)
                # And "2026" or "26"
                
                # Check for NIFTY and Option features
                if "NIFTY" in line and "PE" in line and ("26" in line or "2026" in line):
                    # Filter for likely weekly/monthly expiry range
                    # Just print the first 5 matches that look like NIFTY options
                    if found_count < 10:
                        print(f"MATCH: {line.strip()}")
                        found_count += 1
                    
                # Also specifically look for the one we failed on: 25750 with correct date
                target = "NIFTY2621025750PE"
                if target in line:
                     print(f"✅ FOUND MATCH: {line.strip()}")
                elif "25750" in line and "NIFTY" in line and "PE" in line:
                     print(f"NEAR MATCH: {line.strip()}")
                     
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    fetch_and_search_master()
