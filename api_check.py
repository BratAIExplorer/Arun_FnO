import requests
import json
import os
from dotenv import load_dotenv

def probe():
    load_dotenv()
    api_key = os.getenv('API_KEY')
    try:
        with open("credentials.json", "r") as f:
            creds = json.load(f)
            access_token = creds.get("mstock", {}).get("access_token")
    except: 
        print("Credentials missing.")
        return

    headers = {
        "Authorization": f"token {api_key}:{access_token}",
        "X-Mirae-Version": "1"
    }
    
    # Target endpoints
    endpoints = {
        "Positions": "https://api.mstock.trade/openapi/typea/portfolio/positions",
        "Tradebook": "https://api.mstock.trade/openapi/typea/orders/tradebook",
        "Holdings": "https://api.mstock.trade/openapi/typea/portfolio/holdings"
    }

    print("--- API PROBE (SATURDAY NIGHT) ---")
    for name, url in endpoints.items():
        try:
            resp = requests.get(url, headers=headers, timeout=10)
            print(f"{name}: {resp.status_code}")
            if resp.status_code == 200:
                print(f" -> Success! Data keys: {list(resp.json().keys())}")
            elif resp.status_code == 500:
                print(" -> Still in Maintenance (Broker 500 Error)")
        except Exception as e:
            print(f"{name} failed: {e}")

if __name__ == "__main__":
    probe()
