"""
Trading Configuration Module
Centralized configuration for F&O Trading Bot
"""

from dataclasses import dataclass, field
from datetime import time
from typing import Dict
import json
import os
import logging

logger = logging.getLogger(__name__)


@dataclass
class TradingConfig:
    """Central configuration for trading bot"""
    
    # Capital Management
    initial_capital: float = 100000.0  # Starting capital in INR
    daily_loss_limit_pct: float = 3.0  # Maximum daily loss percentage
    
    # Trading Hours (IST)
    market_open: time = time(9, 15)    # 9:15 AM
    market_close: time = time(15, 30)  # 3:30 PM
    entry_cutoff: time = time(15, 15)  # 3:15 PM - no new entries after this
    
    # VIX Configuration
    vix_min_threshold: float = 10.0    # Skip trading if VIX < this
    
    # VIX-Adjusted Stop Loss Ranges (Based on UNDERLYING SPOT MOVEMENT, not premium)
    # For CE: SL triggers when spot DROPS by percentage
    # For PE: SL triggers when spot RISES by percentage
    vix_sl_ranges: Dict = field(default_factory=lambda: {
        "NIFTY50": {
            "base_sl": 0.70,
            "low": (12, 15, 0.70),
            "mid": (15, 20, 0.75),
            "high": (20, 100, 0.80)
        },
        "BANKNIFTY": {
            "base_sl": 1.20,
            "low": (12, 15, 1.20),
            "mid": (15, 20, 1.25),
            "high": (20, 100, 1.50)
        },
        "FINNIFTY": {
            "base_sl": 1.00,
            "low": (12, 15, 1.00),
            "mid": (15, 20, 1.25),
            "high": (20, 100, 1.50)
        },
        "SENSEX": {
            "base_sl": 1.00,
            "low": (12, 15, 1.00),
            "mid": (15, 20, 1.25),
            "high": (20, 100, 1.50)
        }
    })
    
    # Profit Targets (Based on AMOUNT, editable)
    profit_target_amount: float = 500.0    # Profit target in Rs (Fixed Rule)
    daily_profit_limit: float = 1200.0     # Daily profit cap in Rs (Stop for day if reached)
    
    # Safety Net (Max Premium Loss)
    max_premium_loss_percent: float = -50.0 # Force exit if premium drops by this %
    
    # Technical Indicator Periods
    macd_fast: int = 12
    macd_slow: int = 26
    macd_signal: int = 9
    rsi_period: int = 14
    adx_period: int = 14
    
    # RSI Range for Entry
    # RSI Range for Entry
    rsi_min: float = 30.0
    rsi_max: float = 65.0
    
    # ADX Threshold
    adx_min: float = 25.0              # Minimum ADX for trend strength (OPTIONAL - can be ignored)
    adx_daily_min: float = 25.0        # Minimum Daily ADX for higher timeframe trend
    
    # Lot Sizes
    lot_sizes: Dict = field(default_factory=lambda: {
        "NIFTY50": 65,                 # 1 lot = 65 quantity
        "BANKNIFTY": 30,               # 1 lot = 30 quantity
        "FINNIFTY": 60,                # 1 lot = 60 quantity
        "SENSEX": 20                   # 1 lot = 20 quantity
    })
    
    # Position Management
    max_positions_per_underlying: int = 1  # Max 1 position per underlying
    default_num_lots: int = 1              # Default lot size
    
    # Trading Mode
    live_trading: bool = True              # True = Live orders, False = Paper trading
    
    # Strike Selection
    strike_depth: int = 0                  # 0=ATM, 1=ITM1, 2=ITM2 etc.
    
    # Logging
    log_file: str = "logs/trading_bot.log"
    trade_log_file: str = "logs/trades_{date}.csv"
    
    def __post_init__(self):
        """Load configuration from file after initialization"""
        self.load_from_file()
    
    def load_from_file(self, config_file: str = "config.json"):
        """
        Load configuration from JSON file
        
        Parameters:
        -----------
        config_file : str
            Path to configuration JSON file
        """
        if not os.path.exists(config_file):
            logger.info(f"Config file '{config_file}' not found, using default values")
            return
        
        try:
            with open(config_file, 'r') as f:
                config_data = json.load(f)
            
            # Load trading mode - Hardcoded to True per user request
            self.live_trading = True
            if 'trading_mode' in config_data:
                self.strike_depth = config_data['trading_mode'].get('strike_depth', 0)
            
            # Load capital settings
            if 'capital' in config_data:
                self.initial_capital = config_data['capital'].get('initial_capital', self.initial_capital)
                self.daily_loss_limit_pct = config_data['capital'].get('daily_loss_limit_percent', self.daily_loss_limit_pct)
            
            # Load stop loss settings
            if 'stop_loss' in config_data:
                for underlying, sl_config in config_data['stop_loss'].items():
                    if underlying in self.vix_sl_ranges:
                        base_sl = sl_config.get('base_sl_percent', self.vix_sl_ranges[underlying]['base_sl'])
                        vix_adj = sl_config.get('vix_adjustments', {})
                        
                        self.vix_sl_ranges[underlying] = {
                            'base_sl': base_sl,
                            'low': (12, 15, vix_adj.get('vix_12_15', base_sl)),
                            'mid': (15, 20, vix_adj.get('vix_15_20', base_sl * 1.07)),
                            'high': (20, 100, vix_adj.get('vix_above_20', base_sl * 1.14))
                        }
                    elif underlying == 'max_premium_loss_percent':
                        self.max_premium_loss_percent = sl_config
            
            # Load profit target
            if 'profit_targets' in config_data:
                # Support both old key 'profit_target_percent' (convert to value? no, just default) 
                # and new key 'profit_target_amount'
                self.profit_target_amount = config_data['profit_targets'].get('profit_target_amount', self.profit_target_amount)
                self.daily_profit_limit = config_data['profit_targets'].get('daily_profit_limit', self.daily_profit_limit)
            
            # Load lot sizes
            if 'lot_sizes' in config_data:
                for underlying, lot_config in config_data['lot_sizes'].items():
                    self.lot_sizes[underlying] = lot_config.get('lot_size', self.lot_sizes.get(underlying, 65))
                    if 'num_lots' in lot_config:
                        self.default_num_lots = lot_config['num_lots']
            
            # Load trading hours
            if 'trading_hours' in config_data:
                hours = config_data['trading_hours']
                if 'market_open' in hours:
                    h, m = map(int, hours['market_open'].split(':'))
                    self.market_open = time(h, m)
                if 'market_close' in hours:
                    h, m = map(int, hours['market_close'].split(':'))
                    self.market_close = time(h, m)
                if 'entry_cutoff' in hours:
                    h, m = map(int, hours['entry_cutoff'].split(':'))
                    self.entry_cutoff = time(h, m)
            
            # Load indicator settings
            if 'indicators' in config_data:
                ind = config_data['indicators']
                self.vix_min_threshold = ind.get('vix_min_threshold', self.vix_min_threshold)
                self.rsi_min = ind.get('rsi_min', self.rsi_min)
                self.rsi_max = ind.get('rsi_max', self.rsi_max)
                self.adx_min = ind.get('adx_min', self.adx_min)
                self.adx_daily_min = ind.get('adx_daily_min', self.adx_daily_min)
                self.macd_fast = ind.get('macd_fast', self.macd_fast)
                self.macd_slow = ind.get('macd_slow', self.macd_slow)
                self.macd_signal = ind.get('macd_signal', self.macd_signal)
                self.rsi_period = ind.get('rsi_period', self.rsi_period)
                self.adx_period = ind.get('adx_period', self.adx_period)
            
            logger.info(f"[OK] Configuration loaded from '{config_file}'")
            logger.info(f"   [!] LIVE TRADING MODE: {'ENABLED' if self.live_trading else 'DISABLED (Paper)'}")
            logger.info(f"   Initial Capital: Rs {self.initial_capital:,.2f}")
            logger.info(f"   Profit Target: Rs {self.profit_target_amount}")
            logger.info(f"   Nifty SL: {self.vix_sl_ranges['NIFTY50']['base_sl']}%")
            logger.info(f"   BankNifty SL: {self.vix_sl_ranges['BANKNIFTY']['base_sl']}%")
            logger.info(f"   Nifty Lot Size: {self.lot_sizes['NIFTY50']} x {self.default_num_lots} lots")
            logger.info(f"   BankNifty Lot Size: {self.lot_sizes['BANKNIFTY']} x {self.default_num_lots} lots")
            
        except Exception as e:
            logger.error(f"Error loading config file: {e}")
            logger.info("Using default configuration values")
    
    def get_sl_percentage(self, underlying: str, vix: float) -> float:
        """
        Get stop loss percentage based on underlying and VIX level
        
        Parameters:
        -----------
        underlying : str
            'NIFTY50' or 'BANKNIFTY'
        vix : float
            Current VIX value
            
        Returns:
        --------
        float
            Stop loss percentage
        """
        if underlying not in self.vix_sl_ranges:
            return 0.70  # Default
        
        ranges = self.vix_sl_ranges[underlying]
        
        # Check VIX ranges
        for range_key in ['low', 'mid', 'high']:
            vix_min, vix_max, sl_pct = ranges[range_key]
            if vix_min <= vix < vix_max:
                return sl_pct
        
        # Default to base SL
        return ranges['base_sl']
    
    def get_lot_size(self, underlying: str) -> int:
        """Get lot size for underlying"""
        # Normalize keys
        key_map = {
            "NIFTY": "NIFTY50", 
            "NIFTY 50": "NIFTY50",
            "NIFTYBANK": "BANKNIFTY",
            "NIFTY BANK": "BANKNIFTY",
            "NIFTYFINSERVICE": "FINNIFTY",
            "NIFTY FIN SERVICE": "FINNIFTY"
        }
        normalized = key_map.get(underlying, underlying)
        return self.lot_sizes.get(normalized, 65)  # Default to NIFTY lot size if not found
    
    def is_market_open(self, current_time: time) -> bool:
        """Check if market is currently open"""
        return self.market_open <= current_time <= self.market_close
    
    def can_enter_new_position(self, current_time: time) -> bool:
        """Check if new positions can be entered"""
        return self.market_open <= current_time < self.entry_cutoff


# Global config instance
config = TradingConfig()

