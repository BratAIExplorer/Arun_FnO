import json
import os

def find_symbol():
    filename = "nfo_master.csv"
    if not os.path.exists(filename):
        print("File not found.")
        return

    with open(filename, 'r', encoding='utf-8', errors='ignore') as f:
        data = json.load(f)

    matches = []
    for item in data:
        name = item.get("name", "")
        if "NIFTY2621025500" in name or "NIFTY-10Feb2026-25500" in name:
            matches.append(item)
        elif item.get("symbol") == "NIFTY" and item.get("expiry") == "10Feb2026":
             # Just to see what exists for this expiry
             if len(matches) < 5:
                 matches.append(item)

    print(json.dumps(matches, indent=2))

if __name__ == "__main__":
    find_symbol()
