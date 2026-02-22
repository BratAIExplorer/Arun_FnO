"""
Option Selection Module
Automatically selects ATM strikes for Nifty50 and BankNifty
"""

import logging
from typing import Optional, Tuple
import math

logger = logging.getLogger(__name__)


class OptionSelector:
    """Automatically select ATM option strikes"""
    
    # Strike intervals
    STRIKE_INTERVALS = {
        "NIFTY50": 50,      # Nifty: 50
        "BANKNIFTY": 100,   # BankNifty: 100
        "NIFTYBANK": 100,   # Alias for BankNifty
        "FINNIFTY": 50,     # FinNifty: 50
        "NIFTYFINSERVICE": 50, # Alias for FinNifty
        "SENSEX": 100       # Sensex: 100
    }
    
    @staticmethod
    def get_atm_strike(spot_price: float, underlying: str) -> int:
        """
        Get ATM (At The Money) strike price
        
        Parameters:
        -----------
        spot_price : float
            Current spot price
        underlying : str
            'NIFTY50' or 'BANKNIFTY'
            
        Returns:
        --------
        int
            ATM strike price
        """
        interval = OptionSelector.STRIKE_INTERVALS.get(underlying, 50)
        
        # Round to nearest strike
        atm_strike = round(spot_price / interval) * interval
        
        logger.info(f"{underlying}: Spot={spot_price:.2f}, ATM Strike={atm_strike}")
        return int(atm_strike)
    
    @staticmethod
    def _normalize_symbol(underlying: str) -> str:
        """Map internal names to Master File symbol names"""
        mapping = {
            "NIFTY50": "NIFTY",
            "NIFTYBANK": "BANKNIFTY",
            "BANKNIFTY": "BANKNIFTY", 
            "NIFTYFINSERVICE": "FINNIFTY",
            "FINNIFTY": "FINNIFTY",
            "SENSEX": "SENSEX"
        }
        return mapping.get(underlying, underlying)

    @staticmethod
    def get_option_symbol(
        underlying: str,
        strike: int,
        option_type: str,
        expiry_date: object
    ) -> str:
        """
        Get option symbol from Symbol Master
        """
        from src.symbol_master import SymbolMaster
        
        # Normalize Option Type
        type_suffix = "CE" if option_type in ["CE", "CALL"] else "PE"
        
        # Normalize Underlying (NIFTY50 -> NIFTY)
        master_symbol = OptionSelector._normalize_symbol(underlying)
        
        symbol = SymbolMaster().get_symbol(master_symbol, expiry_date, strike, type_suffix)
        
        if symbol:
            return symbol
            
        # Fallback if symbol not found in master
        logger.error(f"Symbol not found in master for {master_symbol} ({underlying}) {expiry_date} {strike} {type_suffix}")
        return f"{master_symbol}???"
    
    @staticmethod
    def get_expiry(underlying: str) -> object:
        """
        Get nearest expiry date from Symbol Master
        Returns: datetime object
        """
        from src.symbol_master import SymbolMaster
        from datetime import datetime
        
        # Normalize Underlying (NIFTY50 -> NIFTY)
        master_symbol = OptionSelector._normalize_symbol(underlying)
        
        nearest_expiry = SymbolMaster().get_nearest_expiry(master_symbol)
        
        if nearest_expiry:
            logger.info(f"{underlying} (mapped to {master_symbol}): Nearest Expiry = {nearest_expiry}")
            return nearest_expiry
            
        logger.error(f"No expiry found for {underlying} (mapped to {master_symbol})!")
        return datetime.now().date() # Fallback

    @staticmethod
    def get_weekly_expiry(underlying: str) -> object:
        """
        Deprecated shim
        """
        return OptionSelector.get_expiry(underlying)
    
    @staticmethod
    def select_option(
        underlying: str,
        spot_price: float,
        option_type: str,
        depth: int = 0
    ) -> Tuple[int, str]:
        """
        Automatically select option for trading
        - Nifty50: Weekly expiry ATM
        - BankNifty: Monthly expiry ATM
        
        Parameters:
        -----------
        underlying : str
        spot_price : float
        option_type : str
        depth : int
            Strike depth (0=ATM, 1=ITM1, 2=ITM2, etc.)
            
        Returns:
        --------
        Tuple[int, str]
            (strike_price, option_symbol)
        """
        interval = OptionSelector.STRIKE_INTERVALS.get(underlying, 50)
        
        # Get ATM strike
        atm_strike = OptionSelector.get_atm_strike(spot_price, underlying)
        
        # Adjust for Depth (ITM)
        # CE (Call): Buying ITM means LOWER strike (e.g., Spot 20000, ATM 20000, ITM1 19950)
        # PE (Put): Buying ITM means HIGHER strike (e.g., Spot 20000, ATM 20000, ITM1 20050)
        
        if option_type == "CE":
            selected_strike = atm_strike - (depth * interval)
            # NEVER OTM logic: For CE, strike must be <= spot_price
            if selected_strike > spot_price:
                logger.info(f"  [STRIKE ADJUST] Closest strike {selected_strike} is OTM for CE. Shifting to {selected_strike - interval} (ITM/ATM)")
                selected_strike -= interval
        else: # PE
            selected_strike = atm_strike + (depth * interval)
            # NEVER OTM logic: For PE, strike must be >= spot_price
            if selected_strike < spot_price:
                logger.info(f"  [STRIKE ADJUST] Closest strike {selected_strike} is OTM for PE. Shifting to {selected_strike + interval} (ITM/ATM)")
                selected_strike += interval
            
        selected_strike = int(selected_strike)
        
        # Get expiry (weekly for Nifty, monthly for BankNifty)
        expiry = OptionSelector.get_expiry(underlying)
        
        # Construct symbol
        symbol = OptionSelector.get_option_symbol(underlying, selected_strike, option_type, expiry)
        
        expiry_type = "Weekly"
        
        depth_label = "ATM" if depth == 0 else f"ITM-{depth}"
        logger.info(f"[OK] Selected: {symbol} | Strike: {selected_strike} ({depth_label}) | Type: {option_type} | Expiry: {expiry_type}")
        
        return selected_strike, symbol


# Example usage
if __name__ == "__main__":
    # Test
    print("Testing Option Selection...\n")
    
    # Nifty example
    nifty_spot = 19537.45
    strike, symbol = OptionSelector.select_option("NIFTY50", nifty_spot, "CE")
    print(f"Nifty Spot: {nifty_spot}")
    print(f"Selected: {symbol}")
    print(f"Strike: {strike}\n")
    
    # BankNifty example
    bn_spot = 45123.75
    strike, symbol = OptionSelector.select_option("BANKNIFTY", bn_spot, "PE")
    print(f"BankNifty Spot: {bn_spot}")
    print(f"Selected: {symbol}")
    print(f"Strike: {strike}")
