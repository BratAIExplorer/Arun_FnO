import json
import os

def extract_samples():
    filename = "nfo_master.csv"
    if not os.path.exists(filename):
        print("File not found.")
        return

    with open(filename, 'r', encoding='utf-8', errors='ignore') as f:
        data = json.load(f)

    samples = {}
    for item in data:
        symbol = item.get("symbol")
        if symbol not in ["NIFTY", "BANKNIFTY"]:
            continue
        
        expiry = item.get("expiry")
        if expiry not in samples:
            samples[expiry] = []
        
        if len(samples[expiry]) < 3:
            samples[expiry].append(item.get("name"))

    print(json.dumps(samples, indent=2))

if __name__ == "__main__":
    extract_samples()
