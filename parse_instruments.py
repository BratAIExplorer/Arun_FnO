"""
Parse the CSV instrument file from Mstock and extract F&O symbols
"""

import csv
import json

def parse_csv_to_json():
    """Parse the CSV file and extract F&O instruments"""
    
    print("="*70)
    print("PARSING MSTOCK INSTRUMENT CSV")
    print("="*70)
    
    all_instruments = []
    fo_instruments = []
    
    nifty_count = 0
    banknifty_count = 0
    finnifty_count = 0
    sensex_count = 0
    
    nifty_samples = []
    banknifty_samples = []
    finnifty_samples = []
    sensex_samples = []
    
    print("\nReading mstock_scriptmaster_raw.txt...")
    
    with open('mstock_scriptmaster_raw.txt', 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        
        for row in reader:
            all_instruments.append(row)
            
            # Check if it's an F&O instrument
            instrument_type = row.get('instrument_type', '')
            segment = row.get('segment', '')
            symbol = row.get('tradingsymbol', '')
            
            # Look for options (OPTIDX) or F&O segment
            if instrument_type == 'OPTIDX' or segment == 'FO':
                fo_instruments.append(row)
                
                # Count and collect samples for each index
                if 'NIFTY' in symbol and 'BANK' not in symbol and 'FIN' not in symbol:
                    nifty_count += 1
                    if len(nifty_samples) < 5:
                        nifty_samples.append(row)
                elif 'BANKNIFTY' in symbol:
                    banknifty_count += 1
                    if len(banknifty_samples) < 5:
                        banknifty_samples.append(row)
                elif 'FINNIFTY' in symbol:
                    finnifty_count += 1
                    if len(finnifty_samples) < 5:
                        finnifty_samples.append(row)
                elif 'SENSEX' in symbol:
                    sensex_count += 1
                    if len(sensex_samples) < 5:
                        sensex_samples.append(row)
    
    print(f"\nTotal instruments: {len(all_instruments)}")
    print(f"F&O instruments: {len(fo_instruments)}")
    print(f"\nBreakdown by index:")
    print(f"  NIFTY: {nifty_count}")
    print(f"  BANKNIFTY: {banknifty_count}")
    print(f"  FINNIFTY: {finnifty_count}")
    print(f"  SENSEX: {sensex_count}")
    
    # Display samples
    if nifty_samples:
        print(f"\nSample NIFTY options:")
        for sample in nifty_samples:
            print(f"  {sample.get('tradingsymbol')} | Expiry: {sample.get('expiry')} | Strike: {sample.get('strike')}")
    else:
        print("\n[WARNING] No NIFTY options found!")
    
    if banknifty_samples:
        print(f"\nSample BANKNIFTY options:")
        for sample in banknifty_samples:
            print(f"  {sample.get('tradingsymbol')} | Expiry: {sample.get('expiry')} | Strike: {sample.get('strike')}")
    else:
        print("\n[WARNING] No BANKNIFTY options found!")
    
    if finnifty_samples:
        print(f"\nSample FINNIFTY options:")
        for sample in finnifty_samples:
            print(f"  {sample.get('tradingsymbol')} | Expiry: {sample.get('expiry')} | Strike: {sample.get('strike')}")
    else:
        print("\n[WARNING] No FINNIFTY options found!")
    
    if sensex_samples:
        print(f"\nSample SENSEX options:")
        for sample in sensex_samples:
            print(f"  {sample.get('tradingsymbol')} | Expiry: {sample.get('expiry')} | Strike: {sample.get('strike')}")
    else:
        print("\n[WARNING] No SENSEX options found!")
    
    # Save F&O instruments to JSON
    if fo_instruments:
        output_file = "nfo_master.json"
        with open(output_file, 'w') as f:
            json.dump(fo_instruments, f, indent=2)
        print(f"\n[SUCCESS] Saved {len(fo_instruments)} F&O instruments to: {output_file}")
    else:
        print("\n[ERROR] No F&O instruments found to save!")
    
    # Also save all instruments as JSON for reference
    with open("all_instruments.json", 'w') as f:
        json.dump(all_instruments, f, indent=2)
    print(f"[SUCCESS] Saved {len(all_instruments)} total instruments to: all_instruments.json")
    
    return fo_instruments


if __name__ == "__main__":
    parse_csv_to_json()
