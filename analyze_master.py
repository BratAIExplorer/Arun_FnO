
import json
import os
from datetime import datetime

def analyze_master():
    filename = "nfo_master.csv"
    if not os.path.exists(filename):
        print("File not found.")
        return

    print(f"Reading {filename}...")
    try:
        with open(filename, 'r', encoding='utf-8', errors='ignore') as f:
            data = f.read()
            
        # The file might be a JSON array or fragments. 
        # From the snapshot, it looks like `[{"token":...`
        # Let's try to parse it as JSON.
        try:
            instruments = json.loads(data)
        except json.JSONDecodeError:
            # If it failed, maybe it's because we wrote chunked bytes and it might be cut off or has extra chars?
            # Or maybe it's just a list of objects.
            print("Direct JSON parse failed. Trying to cleanup...")
            # If it's effectively a list of dicts, we can iterate.
            # But simpler: search for "expiry" patterns.
            instruments = [] # Placeholder if full parse fails
            pass

        nifty_expiries = set()
        bn_expiries = set()
        bn_samples = {}
        nifty_formats = set()

        if instruments:
            print(f"JSON Parsed: {len(instruments)} records.")
            for inst in instruments:
                sym = inst.get("symbol")
                name = inst.get("name")
                expiry = inst.get("expiry")
                
                if sym == "NIFTY":
                    nifty_expiries.add(expiry)
                    if "NIFTY" in name:
                         suffix = name.replace("NIFTY", "")
                         nifty_formats.add(suffix[:5])
                elif sym == "BANKNIFTY":
                    bn_expiries.add(expiry)
                    # Print first 5 samples per expiry
                    if expiry not in bn_samples:
                        bn_samples[expiry] = []
                    if len(bn_samples[expiry]) < 5:
                        bn_samples[expiry].append(name)
        else:
            print("Parsing manually/regex...")
            # Fallback: finding expiry strings
            import re
            # Regex to capture symbol and expiry: "symbol":"(NIFTY|BANKNIFTY)","name":"(.*?)","expiry":"(.*?)"
            pattern = re.compile(r'"symbol":"(NIFTY|BANKNIFTY)","name":"(.*?)","expiry":"(.*?)"')
            matches = pattern.findall(data)
            
            for symbol, name, expiry in matches:
                if symbol == "NIFTY":
                    nifty_expiries.add(expiry)
                    # Extract format from Name: NIFTY26210... -> YYMDD
                    # name examples: NIFTY2621028500PE
                    if "NIFTY" in name:
                         # Try to deduce format
                         suffix = name.replace("NIFTY", "")
                         nifty_formats.add(suffix[:5]) # Capture date part
                         
                elif symbol == "BANKNIFTY":
                    bn_expiries.add(expiry)
            
        print("\n--- NIFTY Expiries Found ---")
        for e in sorted(nifty_expiries):
            print(e)
            
        print("\n--- BANKNIFTY Expiries Found ---")
        for e in sorted(bn_expiries):
            print(f"Expiry: {e}")
            if e in bn_samples:
                for s in bn_samples[e]:
                    print(f"  Sample: {s}")
            
        print("\n--- NIFTY Name Date Parts (YYMDD?) ---")
        for f in sorted(list(nifty_formats))[:20]:
            print(f)

    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    analyze_master()
