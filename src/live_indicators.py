"""
Real-time Market Indicators Module
Fetches and calculates live market indicators for dashboard
"""

import pandas as pd
from datetime import datetime
from typing import Dict, Optional
import logging

from src.market_data import MStockAPI
from src.indicators import TechnicalIndicators

logger = logging.getLogger(__name__)


class LiveIndicators:
    """Fetch and calculate real-time market indicators"""
    
    def __init__(self, api: MStockAPI):
        """
        Initialize live indicators
        
        Parameters:
        -----------
        api : MStockAPI
            mStock API instance
        """
        self.api = api
    
    def get_live_indicators(self, symbol: str, exchange: str, instrument_token: str) -> Dict:
        """
        Get live indicators for a symbol with REAL-TIME updates
        Creates a live forming candle from current price for streaming indicators
        
        Parameters:
        -----------
        symbol : str
            Symbol name (e.g., 'NIFTY 50', 'NIFTY BANK')
        exchange : str
            Exchange (NSE)
        instrument_token : str
            Instrument token
            
        Returns:
        --------
        Dict
            Dictionary with daily and 15min indicators
        """
        try:
            # Get current spot price FIRST for live candle
            quote = self.api.get_quote(symbol, exchange)
            spot_price = quote.get('last_price', 0) if quote else 0
            
            # Fetch daily data
            daily_df = self.api.get_historical_data(symbol, exchange, instrument_token, "day", days=60)
            if daily_df is None or len(daily_df) < 30:
                logger.warning(f"Insufficient daily data for {symbol}")
                return self._empty_indicators()
            
            # Fetch 15-minute data (using 10 days hybrid for Today's bars)
            intraday_df = self.api.get_hybrid_history(symbol, exchange, instrument_token, "15minute", days=10)
            if intraday_df is None or len(intraday_df) < 50:
                logger.warning(f"Insufficient intraday data for {symbol}")
                return self._empty_indicators()
            
            # CREATE LIVE FORMING CANDLE for real-time indicators
            # This makes RSI/ADX/MACD update every second instead of every 15 minutes!
            import pytz
            from datetime import datetime as dt
            
            ist = pytz.timezone("Asia/Kolkata")
            current_time = dt.now(ist)
            
            # ALIGN TO 15-MINUTE BAR START (Standardizes indicator calculation)
            bar_start = current_time.replace(minute=current_time.minute - current_time.minute % 15, second=0, microsecond=0)
            
            # Create a new row for the current forming candle
            if spot_price > 0:
                # Use current spot price as close, and last candle's close as open
                last_close = intraday_df.iloc[-1]['close']
                
                # Build live candle (open=last close, high/low/close=current price estimate)
                live_candle = pd.DataFrame({
                    'open': [last_close],
                    'high': [max(last_close, spot_price)],
                    'low': [min(last_close, spot_price)],
                    'close': [spot_price]
                }, index=[bar_start])
                
                # Append live candle to historical data
                intraday_df_live = pd.concat([intraday_df, live_candle])
            else:
                intraday_df_live = intraday_df
            
            # Calculate daily indicators (no live candle needed for daily)
            daily_macd, daily_macd_signal, _ = TechnicalIndicators.calculate_macd(daily_df['close'])
            daily_rsi = TechnicalIndicators.calculate_rsi(daily_df['close'])
            daily_adx, _, _ = TechnicalIndicators.calculate_adx(daily_df['high'], daily_df['low'], daily_df['close'])
            
            # Calculate 15min indicators WITH LIVE CANDLE - updates in real-time!
            intraday_macd, intraday_macd_signal, _ = TechnicalIndicators.calculate_macd(intraday_df_live['close'])
            intraday_rsi = TechnicalIndicators.calculate_rsi(intraday_df_live['close'])
            intraday_adx, _, _ = TechnicalIndicators.calculate_adx(intraday_df_live['high'], intraday_df_live['low'], intraday_df_live['close'])
            
            # Use spot price if available, otherwise fallback
            if spot_price == 0:
                spot_price = quote.get('last_price', intraday_df.iloc[-1]['close']) if quote else intraday_df.iloc[-1]['close']
            
            # Get latest values
            daily_macd_val = daily_macd.iloc[-1]
            daily_signal_val = daily_macd_signal.iloc[-1]
            daily_rsi_val = daily_rsi.iloc[-1]
            daily_adx_val = daily_adx.iloc[-1]
            
            intraday_macd_val = intraday_macd.iloc[-1]
            intraday_signal_val = intraday_macd_signal.iloc[-1]
            intraday_rsi_val = intraday_rsi.iloc[-1]
            intraday_adx_val = intraday_adx.iloc[-1]
            
            # Determine MACD trend
            daily_macd_trend = "Bullish" if daily_macd_val > daily_signal_val else "Bearish"
            intraday_macd_trend = "Bullish" if intraday_macd_val > intraday_signal_val else "Bearish"
            
            return {
                'spot_price': spot_price,
                'daily': {
                    'rsi': daily_rsi_val,
                    'adx': daily_adx_val,
                    'macd_trend': daily_macd_trend,
                    'macd_value': daily_macd_val,
                    'macd_signal': daily_signal_val
                },
                'intraday_15m': {
                    'rsi': intraday_rsi_val,
                    'adx': intraday_adx_val,
                    'macd_trend': intraday_macd_trend,
                    'macd_value': intraday_macd_val,
                    'macd_signal': intraday_signal_val
                },
                'timestamp': datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error fetching indicators for {symbol}: {e}")
            return self._empty_indicators()
    
    def get_vix(self) -> Optional[float]:
        """
        Get current VIX value
        
        Returns:
        --------
        Optional[float]
            VIX value or None
        """
        try:
            # VIX symbol on NSE
            quote = self.api.get_quote("INDIA VIX", "NSE")
            if quote:
                return quote.get('last_price', 15.0)
            return 15.0  # Default
        except Exception as e:
            logger.error(f"Error fetching VIX: {e}")
            return 15.0
    
    def _empty_indicators(self) -> Dict:
        """Return empty indicators structure"""
        return {
            'spot_price': 0,
            'daily': {
                'rsi': 0,
                'adx': 0,
                'macd_trend': 'N/A',
                'macd_value': 0,
                'macd_signal': 0
            },
            'intraday_15m': {
                'rsi': 0,
                'adx': 0,
                'macd_trend': 'N/A',
                'macd_value': 0,
                'macd_signal': 0
            },
            'timestamp': datetime.now().isoformat()
        }
    
    def get_all_indicators(self) -> Dict:
        """
        Get indicators for all symbols
        
        Returns:
        --------
        Dict
            Dictionary with indicators for all indices and VIX
        """
        indicators = {}
        
        # Nifty50
        indicators['NIFTY50'] = self.get_live_indicators(
            "NIFTY 50",
            "NSE",
            "26000"
        )
        
        # BankNifty
        indicators['BANKNIFTY'] = self.get_live_indicators(
            "NIFTY BANK",
            "NSE",
            "26009"
        )
        
        # FINNIFTY
        indicators['FINNIFTY'] = self.get_live_indicators(
            "NIFTY FIN SERVICE",
            "NSE",
            "26037"
        )
        
        # SENSEX (BSE)
        # Note: MStock uses 'SENSEX' on BSE with Token 51 (Verified via debug_sensex_history.py)
        indicators['SENSEX'] = self.get_live_indicators(
            "SENSEX",
            "BSE", 
            "51" 
        )
        
        # VIX
        indicators['VIX'] = self.get_vix()
        
        return indicators
