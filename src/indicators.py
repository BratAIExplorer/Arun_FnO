"""
Technical Indicators Module for F&O Trading Bot
Implements MACD, RSI, and ADX calculations
"""

import pandas as pd
import numpy as np
from typing import Tuple


class TechnicalIndicators:
    """Calculate technical indicators for trading decisions"""
    
    @staticmethod
    def calculate_macd(data: pd.Series, fast: int = 12, slow: int = 26, signal: int = 9) -> Tuple[pd.Series, pd.Series, pd.Series]:
        """
        Calculate MACD (Moving Average Convergence Divergence)
        
        Parameters:
        -----------
        data : pd.Series
            Price data (typically close prices)
        fast : int
            Fast EMA period (default: 12)
        slow : int
            Slow EMA period (default: 26)
        signal : int
            Signal line EMA period (default: 9)
            
        Returns:
        --------
        Tuple[pd.Series, pd.Series, pd.Series]
            MACD line, Signal line, MACD histogram
        """
        if not isinstance(data, pd.Series):
            data = pd.Series(data)
        
        # Calculate EMAs
        ema_fast = data.ewm(span=fast, adjust=False).mean()
        ema_slow = data.ewm(span=slow, adjust=False).mean()
        
        # MACD line = Fast EMA - Slow EMA
        macd_line = ema_fast - ema_slow
        
        # Signal line = EMA of MACD line
        signal_line = macd_line.ewm(span=signal, adjust=False).mean()
        
        # MACD histogram = MACD line - Signal line
        macd_histogram = macd_line - signal_line
        
        return macd_line, signal_line, macd_histogram
    
    @staticmethod
    def calculate_rsi(data: pd.Series, period: int = 14) -> pd.Series:
        """
        Calculate RSI (Relative Strength Index) using Wilder's method
        Matches TradingView RSI calculation
        
        Parameters:
        -----------
        data : pd.Series
            Price data (typically close prices)
        period : int
            RSI period (default: 14)
            
        Returns:
        --------
        pd.Series
            RSI values (0-100)
        """
        if not isinstance(data, pd.Series):
            data = pd.Series(data)
        
        # Calculate price changes
        delta = data.diff()
        
        # Separate gains and losses
        gain = delta.clip(lower=0)
        loss = -delta.clip(upper=0)
        
        # Wilder's Smoothing Method (Matches TradingView RMA)
        # Alpha = 1/period uses the recursive smoothing formula
        avg_gain = gain.ewm(alpha=1/period, adjust=False).mean()
        avg_loss = loss.ewm(alpha=1/period, adjust=False).mean()
        
        # Calculate RS and RSI
        rs = avg_gain / avg_loss
        rsi = 100 - (100 / (1 + rs))
        
        return rsi
    
    @staticmethod
    def calculate_adx(high: pd.Series, low: pd.Series, close: pd.Series, period: int = 14) -> Tuple[pd.Series, pd.Series, pd.Series]:
        """
        Calculate ADX (Average Directional Index) with +DI and -DI
        
        Parameters:
        -----------
        high : pd.Series
            High prices
        low : pd.Series
            Low prices
        close : pd.Series
            Close prices
        period : int
            ADX period (default: 14)
            
        Returns:
        --------
        Tuple[pd.Series, pd.Series, pd.Series]
            ADX, +DI, -DI
        """
        if not isinstance(high, pd.Series):
            high = pd.Series(high)
        if not isinstance(low, pd.Series):
            low = pd.Series(low)
        if not isinstance(close, pd.Series):
            close = pd.Series(close)
        
        # Calculate True Range (TR)
        high_low = high - low
        high_close = np.abs(high - close.shift())
        low_close = np.abs(low - close.shift())
        
        tr = pd.concat([high_low, high_close, low_close], axis=1).max(axis=1)
        atr = tr.ewm(alpha=1/period, adjust=False, min_periods=period).mean()
        
        # Calculate directional movements
        up_move = high - high.shift()
        down_move = low.shift() - low
        
        # Positive Directional Movement (+DM)
        plus_dm = np.where((up_move > down_move) & (up_move > 0), up_move, 0)
        plus_dm = pd.Series(plus_dm, index=high.index)
        
        # Negative Directional Movement (-DM)
        minus_dm = np.where((down_move > up_move) & (down_move > 0), down_move, 0)
        minus_dm = pd.Series(minus_dm, index=high.index)
        
        # Smoothed directional movements (RMA)
        plus_dm_smooth = plus_dm.ewm(alpha=1/period, adjust=False).mean()
        minus_dm_smooth = minus_dm.ewm(alpha=1/period, adjust=False).mean()
        
        # Directional Indicators
        plus_di = 100 * (plus_dm_smooth / atr)
        minus_di = 100 * (minus_dm_smooth / atr)
        
        # Calculate DX (Directional Index)
        dx = 100 * np.abs(plus_di - minus_di) / (plus_di + minus_di)
        
        # Calculate ADX (smoothed DX using RMA)
        adx = dx.ewm(alpha=1/period, adjust=False).mean()
        
        return adx, plus_di, minus_di
    
    @staticmethod
    def check_macd_crossover_bullish(macd_line: pd.Series, signal_line: pd.Series, current_idx: int) -> bool:
        """
        Check if MACD just crossed above signal line (bullish crossover)
        
        Parameters:
        -----------
        macd_line : pd.Series
            MACD line values
        signal_line : pd.Series
            Signal line values
        current_idx : int
            Current bar index
            
        Returns:
        --------
        bool
            True if bullish crossover detected
        """
        if current_idx < 1 or current_idx >= len(macd_line):
            return False
        
        try:
            # Previous bar: MACD <= Signal
            # Current bar: MACD > Signal
            prev_macd = macd_line.iloc[current_idx - 1]
            prev_sig = signal_line.iloc[current_idx - 1]
            curr_macd = macd_line.iloc[current_idx]
            curr_sig = signal_line.iloc[current_idx]
            
            # SAFETY: Check for NaN
            if any(np.isnan([prev_macd, prev_sig, curr_macd, curr_sig])):
                return False
                
            return prev_macd <= prev_sig and curr_macd > curr_sig
        except Exception:
            return False
    
    @staticmethod
    def check_macd_crossover_bearish(macd_line: pd.Series, signal_line: pd.Series, current_idx: int) -> bool:
        """
        Check if MACD just crossed below signal line (bearish crossover)
        
        Parameters:
        -----------
        macd_line : pd.Series
            MACD line values
        signal_line : pd.Series
            Signal line values
        current_idx : int
            Current bar index
            
        Returns:
        --------
        bool
            True if bearish crossover detected
        """
        if current_idx < 1 or current_idx >= len(macd_line):
            return False
            
        try:
            # Previous bar: MACD >= Signal
            # Current bar: MACD < Signal
            prev_macd = macd_line.iloc[current_idx - 1]
            prev_sig = signal_line.iloc[current_idx - 1]
            curr_macd = macd_line.iloc[current_idx]
            curr_sig = signal_line.iloc[current_idx]
            
            # SAFETY: Check for NaN
            if any(np.isnan([prev_macd, prev_sig, curr_macd, curr_sig])):
                return False
                
            return prev_macd >= prev_sig and curr_macd < curr_sig
        except Exception:
            return False
    
    @staticmethod
    def is_green_candle(open_price: float, close_price: float) -> bool:
        """Check if candle is green (bullish)"""
        return close_price > open_price
    
    @staticmethod
    def is_red_candle(open_price: float, close_price: float) -> bool:
        """Check if candle is red (bearish)"""
        return close_price < open_price

    @staticmethod
    def check_di_crossover_bullish(plus_di: pd.Series, minus_di: pd.Series, current_idx: int) -> bool:
        """
        Check if +DI crosses ABOVE -DI (Bullish) or -DI crosses BELOW +DI
        Used for trend reversal signals
        """
        if current_idx < 1 or current_idx >= len(plus_di):
            return False
            
        try:
            # Previous: +DI <= -DI
            # Current: +DI > -DI
            prev_plus = plus_di.iloc[current_idx-1]
            prev_minus = minus_di.iloc[current_idx-1]
            curr_plus = plus_di.iloc[current_idx]
            curr_minus = minus_di.iloc[current_idx]
            
            # SAFETY: Check for NaN
            if any(np.isnan([prev_plus, prev_minus, curr_plus, curr_minus])):
                return False
                
            prev_bullish = prev_plus > prev_minus
            curr_bullish = curr_plus > curr_minus
            
            # We want to catch the transition from Bearish to Bullish
            return (not prev_bullish) and curr_bullish
        except Exception:
            return False

    @staticmethod
    def check_di_crossover_bearish(plus_di: pd.Series, minus_di: pd.Series, current_idx: int) -> bool:
        """
        Check if +DI crosses BELOW -DI (Bearish) or -DI crosses ABOVE +DI
        Used for trend reversal signals
        """
        if current_idx < 1 or current_idx >= len(plus_di):
            return False
            
        try:
            # Previous: +DI >= -DI
            # Current: +DI < -DI
            prev_plus = plus_di.iloc[current_idx-1]
            prev_minus = minus_di.iloc[current_idx-1]
            curr_plus = plus_di.iloc[current_idx]
            curr_minus = minus_di.iloc[current_idx]
            
            # SAFETY: Check for NaN
            if any(np.isnan([prev_plus, prev_minus, curr_plus, curr_minus])):
                return False
                
            prev_bearish = prev_plus < prev_minus
            curr_bearish = curr_plus < curr_minus
            
            # We want to catch the transition from Bullish to Bearish
            return (not prev_bearish) and curr_bearish
        except Exception:
            return False
