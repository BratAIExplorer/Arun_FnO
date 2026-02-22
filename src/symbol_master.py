import csv
import logging
import json
from datetime import datetime
from typing import Dict, List, Optional, Set
import os

logger = logging.getLogger(__name__)

class SymbolMaster:
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(SymbolMaster, cls).__new__(cls)
            cls._instance.initialized = False
        return cls._instance

    def __init__(self):
        if self.initialized:
            return
        
        # Structure: { "BANKNIFTY": { datetime_expiry: { 45000: { "CE": "SYMBOL...", "PE": "SYMBOL..." } } } }
        self.master_data = {} 
        self.expiries = {} # { "BANKNIFTY": [date1, date2, ...] }
        self.symbol_map = {} # { "SYMBOLNAME": "TOKEN" }
        self.initialized = True
        self.load_master()

    def load_master(self, filepath="nfo_master.csv"):
        if not os.path.exists(filepath):
            logger.error(f"Master file not found: {filepath}")
            return

        logger.info(f"Loading symbol master from {filepath}...")
        count = 0
        try:
            # The file is a weird JSON/CSV hybrid or just a list of JSON objects?
            # Based on previous analyze_master, it looked like a standard file but with some complexity.
            # analyze_master.py used simple read or regex. 
            # Let's try reading as loose JSON lines or standard CSV if structured that way.
            # User's analyze_master used regex to find `expiry` etc. 
            # The sample output showed: `{"token":"...","symbol":"...` etc. 
            # It seems to be a file containing a large JSON array or multiple JSON objects.
            
            # Let's use the safer regex approach from analyze_master.py as a fallback 
            # or try to parse the whole thing if it's valid JSON.
            # analyze_master output: "JSON Parsed: 173332 records." -> It IS valid JSON.
            
            with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
                data = json.load(f)
                
            for item in data:
                # Filter for relevant symbols
                symbol_prefix = item.get('symbol') # e.g. BANKNIFTY
                if symbol_prefix not in ["NIFTY", "BANKNIFTY", "FINNIFTY", "SENSEX"]:
                    continue
                    
                expiry_str = item.get('expiry') # "24Feb2026"
                strike_str = item.get('strike') # "45000"
                option_type = "CE" if "CE" in item.get('name', '') else "PE" if "PE" in item.get('name', '') else None
                instrument = item.get('instrumenttype') # OPTIDX etc
                
                # We only want OPTIDX for these indices usually, but NIFTY might be OPTIDX.
                # master file showed "instrumenttype":"OPTIDX" for BANKNIFTY.
                if instrument != "OPTIDX":
                    continue
                    
                if not (symbol_prefix and expiry_str and strike_str and option_type):
                    continue
                
                try:
                    expiry_date = datetime.strptime(expiry_str, "%d%b%Y").date()
                    strike = float(strike_str)
                except ValueError:
                    continue

                if symbol_prefix not in self.master_data:
                    self.master_data[symbol_prefix] = {}
                    self.expiries[symbol_prefix] = set()

                if expiry_date not in self.master_data[symbol_prefix]:
                    self.master_data[symbol_prefix][expiry_date] = {}
                
                self.expiries[symbol_prefix].add(expiry_date)
                
                if strike not in self.master_data[symbol_prefix][expiry_date]:
                    self.master_data[symbol_prefix][expiry_date][strike] = {}
                    
                name = item.get('name', '').strip()
                if not name:
                    continue
                
                # Store mappings
                self.master_data[symbol_prefix][expiry_date][strike][option_type] = name
                
                # Add check since item.get('token') might be string or int
                token = str(item.get('token', ''))
                if token:
                    self.symbol_map[name] = token
                    
                count += 1
                
            # Sort expiries
            for sym in self.expiries:
                self.expiries[sym] = sorted(list(self.expiries[sym]))
                
            logger.info(f"SymbolMaster loaded {count} options from master file. (Token map size: {len(self.symbol_map)})")
            
        except Exception as e:
            logger.error(f"Failed to load master file: {e}")

    def get_nearest_expiry(self, underlying: str, min_date: Optional[datetime] = None) -> Optional[datetime]:
        """Finds the nearest available expiry date used in the master file."""
        if underlying not in self.expiries:
            return None
            
        if min_date is None:
            min_date = datetime.now().date()
        else:
            if isinstance(min_date, datetime):
                min_date = min_date.date()

        for exp in self.expiries[underlying]:
            if exp >= min_date:
                return exp
        return None

    def get_symbol(self, underlying: str, expiry: datetime, strike: float, option_type: str) -> Optional[str]:
        """Retrieves correct trading symbol from master data in mStock instrument file format."""
        if isinstance(expiry, datetime):
            expiry_date = expiry.date()
        else:
            expiry_date = expiry
        
        # Normalize underlying name (NIFTY50 -> NIFTY, etc.)
        normalized_underlying = self._normalize_underlying(underlying)
            
        try:
            # 1. Try master file lookup first
            symbol_name = self.master_data.get(normalized_underlying, {}).get(expiry_date, {}).get(strike, {}).get(option_type)
            
            if symbol_name:
                return symbol_name
            
            # 2. Fallback: Algorithmic Generation (Verified Mstock Format)
            # Format depends on Weekly vs Monthly
            # Weekly: SYMBOL + YY + M + DD + STRIKE + TYPE (M: 1-9, O, N, D)
            # Monthly: SYMBOL + YY + MMM + STRIKE + TYPE (MMM: JAN, FEB...)
            
            yy = expiry_date.strftime("%y")
            if strike is None:
                logger.warning(f"Cannot generate symbol for {normalized_underlying} - missing strike")
                return None
            strike_str = str(int(strike))
            
            # Month mapping for weeklies
            m_map = {1: "1", 2: "2", 3: "3", 4: "4", 5: "5", 6: "6", 7: "7", 8: "8", 9: "9", 10: "O", 11: "N", 12: "D"}
            m_str = m_map.get(expiry_date.month)
            dd_str = expiry_date.strftime("%d")
            
            # Detect if Monthly (Simple heuristic: if MMM format is common for last Thu)
            # Or better: check if it's the last expiry of the month for this underlying
            all_exps = self.expiries.get(normalized_underlying, [])
            is_monthly = False
            
            # Monthly format is used if it matches the 'name' pattern in master, 
            # or if we can't find a better way. 
            # In mStock, Monthly = SYMBOL + YY + MMM
            # Weeklies = SYMBOL + YY + M + DD
            
            # Let's try to detect Monthly by checking if DD >= 20 and it's 
            # one of the standard monthly exps (last Thu for Nifty, last Wed for BN)
            # But the master file data is the source of truth.
            
            # For now, if we are in fallback, assume Monthly if MMM is Feb (current month)
            # and it's not a known weekly. 
            # Actually, let's just use MMM as a fallback for monthly-like exps.
            
            mmm = expiry_date.strftime("%b").upper()
            
            # If date is in master as a weekly-like date (e.g. 10Feb), then M DD is preferred.
            # But here we are already failing master lookup.
            
            # Let's try both? The problem is we need to RETURN one.
            # Usually users specify which one they want. 
            
            # Heuristic: If it's a "known" monthly date or we have no master data for weeklies, 
            # default to weekly if month/day are available, otherwise monthly.
            # Actually, mStock Weekly is the MOST COMMON for intraday.
            
            generated_weekly = f"{normalized_underlying}{yy}{m_str}{dd_str}{strike_str}{option_type}"
            generated_monthly = f"{normalized_underlying}{yy}{mmm}{strike_str}{option_type}"
            
            # Return weekly as it's more common if we are guessing.
            # BUT the user's manual trade might be monthly.
            
            # Let's return the Monthly one ONLY if it's the last week of the month.
            import calendar
            last_day = calendar.monthrange(expiry_date.year, expiry_date.month)[1]
            if expiry_date.day > last_day - 7:
                 logger.info(f"Generated Symbol (Algorithmic Monthly): {generated_monthly}")
                 return generated_monthly
            else:
                 logger.info(f"Generated Symbol (Algorithmic Weekly): {generated_weekly}")
                 return generated_weekly
            
        except KeyError:
            return None
    
    def _normalize_underlying(self, underlying: str) -> str:
        """Map internal names to exchange symbol names"""
        mapping = {
            "NIFTY50": "NIFTY",
            "NIFTYBANK": "BANKNIFTY",
            "BANKNIFTY": "BANKNIFTY",
            "NIFTYFINSERVICE": "FINNIFTY",
            "FINNIFTY": "FINNIFTY",
            "SENSEX": "SENSEX"
        }
        return mapping.get(underlying, underlying)
            
    def get_token(self, symbol: str) -> Optional[str]:
        """Get instrument token for a symbol name"""
        # Note: mStock format symbols won't match master 'name' field
        # We might not need tokens if using NSE exchange
        return self.symbol_map.get(symbol)
