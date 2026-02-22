"""
TRADING BOT: Nifty50 & BankNifty Options Strategy
Strategy Details: MACD + RSI + ADX Entry with Underlying SL + Premium Profit Targets
Author: Trading Bot
Date: Jan 2026
"""

import pandas as pd
import numpy as np
from datetime import datetime, time
import logging
from dataclasses import dataclass, field
from enum import Enum
from typing import Optional, Dict, List, Tuple

# ===========================
# CONFIGURATION & CONSTANTS
# ===========================

class TradeType(Enum):
    CE = "CALL"  # Call option
    PE = "PUT"   # Put option

class PositionStatus(Enum):
    OPEN = "OPEN"
    CLOSED = "CLOSED"
    EXITED_PROFIT = "EXITED_PROFIT"
    EXITED_SL = "EXITED_SL"
    EXITED_TECHNICAL = "EXITED_TECHNICAL"
    EXITED_EOD = "EXITED_EOD"

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('trading_bot.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# ===========================
# DATA CLASSES
# ===========================

@dataclass
class TradeConfig:
    """Configuration for a specific underlying"""
    underlying: str  # "NIFTY50" or "BANKNIFTY"
    lot_size: int
    sl_percentage: float  # Base SL (0.70 for Nifty, 1.00 for BankNifty)
    profit_target_percentage: float  # 15% for both
    
    # VIX-adjusted SL percentages
    vix_sl_ranges: Dict = field(default_factory=lambda: {
        "nifty": {
            "low": (12, 15, 0.70),      # VIX 12-15: 0.70%
            "mid": (15, 20, 0.75),      # VIX 15-20: 0.75%
            "high": (20, 100, 0.80)     # VIX > 20: 0.80%
        },
        "banknifty": {
            "low": (12, 15, 1.00),      # VIX 12-15: 1.00%
            "mid": (15, 20, 1.25),      # VIX 15-20: 1.25%
            "high": (20, 100, 1.50)     # VIX > 20: 1.50%
        }
    })

@dataclass
class Position:
    """Active trading position"""
    position_id: str
    underlying: str  # "NIFTY50" or "BANKNIFTY"
    trade_type: TradeType  # CE or PE
    entry_time: datetime
    entry_price: float  # Premium paid
    entry_underlying_price: float  # Spot price at entry
    entry_strike: float  # ATM strike
    lot_size: int
    status: PositionStatus = PositionStatus.OPEN
    sl_percentage: float = 0.0  # SL based on VIX
    profit_target_percentage: float = 15.0
    
    # Exit details
    exit_time: Optional[datetime] = None
    exit_price: Optional[float] = None
    exit_underlying_price: Optional[float] = None
    exit_reason: Optional[str] = None
    pnl: float = 0.0
    pnl_percentage: float = 0.0
    
    # For tracking MACD crossover entry
    macd_crossover_candle: Optional[int] = None  # To track if new crossover

    def calculate_pnl(self, current_premium: float) -> float:
        """Calculate P&L on position"""
        pnl = (current_premium - self.entry_price) * self.lot_size
        pnl_percentage = ((current_premium - self.entry_price) / self.entry_price) * 100
        return pnl, pnl_percentage

    def check_sl_hit(self, current_underlying_price: float) -> bool:
        """Check if SL is hit based on underlying movement"""
        if self.trade_type == TradeType.CE:
            # CE: SL hits if spot drops by SL%
            sl_level = self.entry_underlying_price * (1 - self.sl_percentage / 100)
            return current_underlying_price <= sl_level
        else:  # PE
            # PE: SL hits if spot rises by SL%
            sl_level = self.entry_underlying_price * (1 + self.sl_percentage / 100)
            return current_underlying_price >= sl_level

    def check_profit_hit(self, current_premium: float) -> bool:
        """Check if profit target is hit"""
        profit_percentage = ((current_premium - self.entry_price) / self.entry_price) * 100
        return profit_percentage >= self.profit_target_percentage

# ===========================
# TECHNICAL INDICATORS
# ===========================

class TechnicalIndicators:
    """Calculate technical indicators"""
    
    @staticmethod
    def calculate_macd(data: pd.Series, fast: int = 12, slow: int = 26, signal: int = 9) -> Tuple[pd.Series, pd.Series, pd.Series]:
        """
        Calculate MACD
        Returns: MACD line, Signal line, Histogram
        """
        ema_fast = data.ewm(span=fast, adjust=False).mean()
        ema_slow = data.ewm(span=slow, adjust=False).mean()
        macd_line = ema_fast - ema_slow
        signal_line = macd_line.ewm(span=signal, adjust=False).mean()
        histogram = macd_line - signal_line
        return macd_line, signal_line, histogram
    
    @staticmethod
    def calculate_rsi(data: pd.Series, period: int = 14) -> pd.Series:
        """Calculate RSI (Relative Strength Index)"""
        delta = data.diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
        rs = gain / loss
        rsi = 100 - (100 / (1 + rs))
        return rsi
    
    @staticmethod
    def calculate_adx(high: pd.Series, low: pd.Series, close: pd.Series, period: int = 14) -> Tuple[pd.Series, pd.Series, pd.Series]:
        """
        Calculate ADX, +DI, -DI
        Returns: ADX, +DI, -DI
        """
        tr = pd.concat([
            high - low,
            abs(high - close.shift()),
            abs(low - close.shift())
        ], axis=1).max(axis=1)
        atr = tr.rolling(window=period).mean()
        
        up_move = high.diff()
        down_move = -low.diff()
        
        plus_dm = up_move.where((up_move > down_move) & (up_move > 0), 0)
        minus_dm = down_move.where((down_move > up_move) & (down_move > 0), 0)
        
        plus_di = 100 * (plus_dm.rolling(window=period).mean() / atr)
        minus_di = 100 * (minus_dm.rolling(window=period).mean() / atr)
        
        dx = 100 * abs(plus_di - minus_di) / (plus_di + minus_di)
        adx = dx.rolling(window=period).mean()
        
        return adx, plus_di, minus_di

# ===========================
# MAIN TRADING BOT CLASS
# ===========================

class TradingBot:
    """Main trading bot implementing the strategy"""
    
    def __init__(self, initial_capital: float = 100000):
        self.initial_capital = initial_capital
        self.current_capital = initial_capital
        self.positions: Dict[str, Position] = {}  # {position_id: Position}
        self.closed_positions: List[Position] = []
        self.daily_pnl = 0.0
        self.daily_loss_limit = initial_capital * 0.03  # 3% daily loss limit
        self.current_day = None
        self.last_macd_crossover: Dict[str, int] = {}  # Track last MACD crossover candle
        self.trading_config = {
            "NIFTY50": TradeConfig(
                underlying="NIFTY50",
                lot_size=1,
                sl_percentage=0.70,
                profit_target_percentage=15.0
            ),
            "BANKNIFTY": TradeConfig(
                underlying="BANKNIFTY",
                lot_size=1,
                sl_percentage=1.00,
                profit_target_percentage=15.0
            )
        }
        logger.info(f"Trading Bot Initialized with Capital: Rs {initial_capital}")
    
    # ===========================
    # ENTRY LOGIC
    # ===========================
    
    def check_entry_conditions_ce(self, underlying: str, daily_data: pd.DataFrame, intraday_data: pd.DataFrame, 
                                   current_row_idx: int, vix: float) -> bool:
        """
        Check all conditions for CALL (CE) entry
        All conditions are MANDATORY
        """
        # Condition 1: Check if already have position
        if underlying in self.positions:
            logger.debug(f"{underlying}: Position already exists, no duplicate buy")
            return False
        
        # Condition 2: Check time window (9:25am to 2:30pm)
        if not self._is_trading_hours():
            logger.debug(f"{underlying}: Outside trading hours")
            return False
        
        # Condition 3: Check VIX filter
        if vix < 10:
            logger.debug(f"{underlying}: VIX {vix} < 10, skip trade")
            return False
        
        # Condition 4: Daily MACD above signal line (bullish)
        if daily_data['MACD'].iloc[-1] <= daily_data['MACD_Signal'].iloc[-1]:
            logger.debug(f"{underlying}: Daily MACD not above signal line")
            return False
        
        # Condition 5: Daily candle should be GREEN (close > open)
        if daily_data['close'].iloc[-1] <= daily_data['open'].iloc[-1]:
            logger.debug(f"{underlying}: Daily candle not GREEN")
            return False
        
        # Condition 6: 15m MACD crosses above signal line
        if not self._check_macd_crossover_ce(intraday_data, current_row_idx):
            logger.debug(f"{underlying}: 15m MACD did not cross above signal line")
            return False
        
        # Condition 7: 15m RSI between 45-65
        rsi_15m = intraday_data['RSI'].iloc[current_row_idx]
        if not (45 <= rsi_15m <= 65):
            logger.debug(f"{underlying}: 15m RSI {rsi_15m} not in 45-65 range")
            return False
        
        # Condition 8: 15m ADX > 25
        adx_15m = intraday_data['ADX'].iloc[current_row_idx]
        if adx_15m <= 25:
            logger.debug(f"{underlying}: 15m ADX {adx_15m} not > 25")
            return False
        
        logger.info(f"{underlying}: All CE entry conditions met ✓")
        return True
    
    def check_entry_conditions_pe(self, underlying: str, daily_data: pd.DataFrame, intraday_data: pd.DataFrame, 
                                   current_row_idx: int, vix: float) -> bool:
        """
        Check all conditions for PUT (PE) entry
        All conditions are MANDATORY
        """
        # Condition 1: Check if already have position
        if underlying in self.positions:
            logger.debug(f"{underlying}: Position already exists, no duplicate buy")
            return False
        
        # Condition 2: Check time window (9:25am to 2:30pm)
        if not self._is_trading_hours():
            logger.debug(f"{underlying}: Outside trading hours")
            return False
        
        # Condition 3: Check VIX filter
        if vix < 10:
            logger.debug(f"{underlying}: VIX {vix} < 10, skip trade")
            return False
        
        # Condition 4: Daily MACD below signal line (bearish)
        if daily_data['MACD'].iloc[-1] >= daily_data['MACD_Signal'].iloc[-1]:
            logger.debug(f"{underlying}: Daily MACD not below signal line")
            return False
        
        # Condition 5: Daily candle should be RED (close < open)
        if daily_data['close'].iloc[-1] >= daily_data['open'].iloc[-1]:
            logger.debug(f"{underlying}: Daily candle not RED")
            return False
        
        # Condition 6: 15m MACD crosses below signal line
        if not self._check_macd_crossover_pe(intraday_data, current_row_idx):
            logger.debug(f"{underlying}: 15m MACD did not cross below signal line")
            return False
        
        # Condition 7: 15m RSI between 45-65
        rsi_15m = intraday_data['RSI'].iloc[current_row_idx]
        if not (45 <= rsi_15m <= 65):
            logger.debug(f"{underlying}: 15m RSI {rsi_15m} not in 45-65 range")
            return False
        
        # Condition 8: 15m ADX > 25
        adx_15m = intraday_data['ADX'].iloc[current_row_idx]
        if adx_15m <= 25:
            logger.debug(f"{underlying}: 15m ADX {adx_15m} not > 25")
            return False
        
        logger.info(f"{underlying}: All PE entry conditions met ✓")
        return True
    
    def _check_macd_crossover_ce(self, intraday_data: pd.DataFrame, current_idx: int) -> bool:
        """Check if MACD just crossed above signal line (CE entry)"""
        if current_idx < 2:
            return False
        
        macd_curr = intraday_data['MACD'].iloc[current_idx]
        signal_curr = intraday_data['MACD_Signal'].iloc[current_idx]
        macd_prev = intraday_data['MACD'].iloc[current_idx - 1]
        signal_prev = intraday_data['MACD_Signal'].iloc[current_idx - 1]
        
        # Crossover: previous MACD <= signal AND current MACD > signal
        crossover = (macd_prev <= signal_prev) and (macd_curr > signal_curr)
        
        if crossover:
            self.last_macd_crossover['CE'] = current_idx
        
        return crossover
    
    def _check_macd_crossover_pe(self, intraday_data: pd.DataFrame, current_idx: int) -> bool:
        """Check if MACD just crossed below signal line (PE entry)"""
        if current_idx < 2:
            return False
        
        macd_curr = intraday_data['MACD'].iloc[current_idx]
        signal_curr = intraday_data['MACD_Signal'].iloc[current_idx]
        macd_prev = intraday_data['MACD'].iloc[current_idx - 1]
        signal_prev = intraday_data['MACD_Signal'].iloc[current_idx - 1]
        
        # Crossover: previous MACD >= signal AND current MACD < signal
        crossover = (macd_prev >= signal_prev) and (macd_curr < signal_curr)
        
        if crossover:
            self.last_macd_crossover['PE'] = current_idx
        
        return crossover
    
    def _is_trading_hours(self) -> bool:
        """Check if current time is within trading hours 9:25am to 2:30pm"""
        current_time = datetime.now().time()
        start_time = time(9, 25)
        end_time = time(14, 30)
        return start_time <= current_time <= end_time
    
    def enter_trade(self, underlying: str, trade_type: TradeType, 
                   entry_price: float, entry_underlying_price: float, 
                   entry_strike: float, vix: float) -> Optional[str]:
        """Enter a new trade and return position_id"""
        
        config = self.trading_config[underlying]
        
        # Get VIX-adjusted SL
        sl_percentage = self._get_vix_adjusted_sl(underlying, vix)
        
        position_id = f"{underlying}_{trade_type.value}_{datetime.now().strftime('%Y%m%d%H%M%S')}"
        
        position = Position(
            position_id=position_id,
            underlying=underlying,
            trade_type=trade_type,
            entry_time=datetime.now(),
            entry_price=entry_price,
            entry_underlying_price=entry_underlying_price,
            entry_strike=entry_strike,
            lot_size=config.lot_size,
            sl_percentage=sl_percentage,
            profit_target_percentage=config.profit_target_percentage
        )
        
        self.positions[underlying] = position
        logger.info(f"ENTRY: {position_id} | Type: {trade_type.value} | "
                   f"Premium: Rs {entry_price} | Spot: {entry_underlying_price:.2f} | "
                   f"SL: {sl_percentage}% | Target: {config.profit_target_percentage}%")
        
        return position_id
    
    def _get_vix_adjusted_sl(self, underlying: str, vix: float) -> float:
        """Get VIX-adjusted SL percentage"""
        config = self.trading_config[underlying]
        underlying_key = underlying.lower()
        
        if underlying_key not in config.vix_sl_ranges:
            return config.sl_percentage
        
        vix_ranges = config.vix_sl_ranges[underlying_key]
        
        if vix < 12:
            return config.sl_percentage  # Base SL
        elif 12 <= vix < 15:
            return vix_ranges["low"][2]
        elif 15 <= vix < 20:
            return vix_ranges["mid"][2]
        else:
            return vix_ranges["high"][2]
    
    # ===========================
    # EXIT LOGIC
    # ===========================
    
    def process_position_exits(self, underlying: str, current_premium: float, 
                               current_underlying_price: float, intraday_data: pd.DataFrame, 
                               current_row_idx: int) -> bool:
        """
        Process all exit conditions for a position
        Returns True if position was exited, False otherwise
        """
        
        if underlying not in self.positions:
            return False
        
        position = self.positions[underlying]
        
        # Exit 1: SL Hit (based on underlying movement)
        if position.check_sl_hit(current_underlying_price):
            self._exit_position(position, current_premium, current_underlying_price, 
                              PositionStatus.EXITED_SL, "SL Hit")
            return True
        
        # Exit 2: Profit Target Hit (15%+ premium gain)
        if position.check_profit_hit(current_premium):
            self._exit_position(position, current_premium, current_underlying_price, 
                              PositionStatus.EXITED_PROFIT, "Profit Target 15%+")
            return True
        
        # Exit 3: MACD Technical Reversal (only if profit < 15%)
        profit_pct = ((current_premium - position.entry_price) / position.entry_price) * 100
        if profit_pct < 15 and self._check_macd_reversal(position, intraday_data, current_row_idx):
            self._exit_position(position, current_premium, current_underlying_price, 
                              PositionStatus.EXITED_TECHNICAL, "MACD Reversal")
            return True
        
        # Exit 4: EOD Force Close (2:30pm)
        if not self._is_trading_hours():
            self._exit_position(position, current_premium, current_underlying_price, 
                              PositionStatus.EXITED_EOD, "EOD Close (2:30pm)")
            return True
        
        return False
    
    def _check_macd_reversal(self, position: Position, intraday_data: pd.DataFrame, current_idx: int) -> bool:
        """Check if MACD has reversed direction and closed below signal line"""
        if current_idx < 2:
            return False
        
        macd_curr = intraday_data['MACD'].iloc[current_idx]
        signal_curr = intraday_data['MACD_Signal'].iloc[current_idx]
        
        # For CE: Reversal means MACD crosses below signal
        # For PE: Reversal means MACD crosses above signal
        
        if position.trade_type == TradeType.CE:
            # CE reversal: MACD must close below signal line
            return macd_curr < signal_curr
        else:  # PE
            # PE reversal: MACD must close above signal line
            return macd_curr > signal_curr
    
    def _exit_position(self, position: Position, exit_premium: float, 
                      exit_underlying_price: float, exit_status: PositionStatus, 
                      exit_reason: str) -> None:
        """Exit a position and update capital"""
        
        position.exit_time = datetime.now()
        position.exit_price = exit_premium
        position.exit_underlying_price = exit_underlying_price
        position.status = exit_status
        position.exit_reason = exit_reason
        
        # Calculate P&L
        pnl, pnl_pct = position.calculate_pnl(exit_premium)
        position.pnl = pnl
        position.pnl_percentage = pnl_pct
        
        # Update capital
        self.current_capital += pnl
        self.daily_pnl += pnl
        
        # Move to closed positions
        self.closed_positions.append(position)
        del self.positions[position.underlying]
        
        logger.info(f"EXIT: {position.position_id} | Reason: {exit_reason} | "
                   f"Exit Premium: Rs {exit_premium} | P&L: Rs {pnl:.2f} ({pnl_pct:.2f}%) | "
                   f"Capital: Rs {self.current_capital:.2f}")
    
    # ===========================
    # RE-ENTRY LOGIC
    # ===========================
    
    def check_reentry_allowed(self, underlying: str) -> bool:
        """Check if re-entry is allowed"""
        
        # Check daily loss limit (3%)
        if self.daily_pnl <= -self.daily_loss_limit:
            logger.warning(f"Daily loss limit ({self.daily_loss_limit}) reached. No re-entry allowed.")
            return False
        
        # Check if position already exists
        if underlying in self.positions:
            logger.debug(f"{underlying}: Position already open, no re-entry")
            return False
        
        return True
    
    def check_fresh_macd_signal(self, trade_type: TradeType, current_row_idx: int) -> bool:
        """
        Check if we have a fresh MACD crossover
        Different candle from the one we exited on
        """
        key = 'CE' if trade_type == TradeType.CE else 'PE'
        
        if key not in self.last_macd_crossover:
            return True  # No previous crossover, fresh signal
        
        # Fresh signal = current crossover is in different candle than last one
        return current_row_idx > self.last_macd_crossover[key]
    
    # ===========================
    # UTILITY FUNCTIONS
    # ===========================
    
    def reset_daily_stats(self):
        """Reset daily stats at end of day"""
        self.daily_pnl = 0.0
        self.last_macd_crossover = {}
        logger.info("Daily stats reset")
    
    def get_account_summary(self) -> Dict:
        """Get account summary"""
        total_trades = len(self.closed_positions)
        winning_trades = len([p for p in self.closed_positions if p.pnl > 0])
        losing_trades = len([p for p in self.closed_positions if p.pnl < 0])
        
        total_pnl = sum([p.pnl for p in self.closed_positions])
        total_pnl_pct = ((self.current_capital - self.initial_capital) / self.initial_capital) * 100
        
        return {
            "initial_capital": self.initial_capital,
            "current_capital": self.current_capital,
            "total_pnl": total_pnl,
            "total_pnl_percentage": total_pnl_pct,
            "total_trades": total_trades,
            "winning_trades": winning_trades,
            "losing_trades": losing_trades,
            "win_rate": (winning_trades / total_trades * 100) if total_trades > 0 else 0,
            "open_positions": len(self.positions)
        }
    
    def print_account_summary(self):
        """Print account summary to console"""
        summary = self.get_account_summary()
        print("\n" + "="*60)
        print("ACCOUNT SUMMARY")
        print("="*60)
        print(f"Initial Capital:     Rs {summary['initial_capital']:,.2f}")
        print(f"Current Capital:     Rs {summary['current_capital']:,.2f}")
        print(f"Total P&L:           Rs {summary['total_pnl']:,.2f}")
        print(f"Total P&L %:         {summary['total_pnl_percentage']:.2f}%")
        print(f"Total Trades:        {summary['total_trades']}")
        print(f"Winning Trades:      {summary['winning_trades']}")
        print(f"Losing Trades:       {summary['losing_trades']}")
        print(f"Win Rate:            {summary['win_rate']:.2f}%")
        print(f"Open Positions:      {summary['open_positions']}")
        print("="*60 + "\n")
    
    def save_trades_to_csv(self, filename: str = "trades_log.csv"):
        """Save all closed trades to CSV"""
        trades_data = []
        
        for position in self.closed_positions:
            trades_data.append({
                'Position_ID': position.position_id,
                'Underlying': position.underlying,
                'Type': position.trade_type.value,
                'Entry_Time': position.entry_time,
                'Entry_Price': position.entry_price,
                'Entry_Spot': position.entry_underlying_price,
                'SL_Percentage': position.sl_percentage,
                'Exit_Time': position.exit_time,
                'Exit_Price': position.exit_price,
                'Exit_Spot': position.exit_underlying_price,
                'Exit_Reason': position.exit_reason,
                'P&L': position.pnl,
                'P&L_%': position.pnl_percentage
            })
        
        df = pd.DataFrame(trades_data)
        df.to_csv(filename, index=False)
        logger.info(f"Trades saved to {filename}")


# ===========================
# MAIN EXECUTION FUNCTION
# ===========================

def run_trading_bot(daily_data: Dict[str, pd.DataFrame], 
                   intraday_data: Dict[str, pd.DataFrame],
                   vix_data: pd.Series):
    """
    Main function to run the trading bot
    
    Parameters:
    -----------
    daily_data: Dict[str, DataFrame] - Daily OHLC data for each underlying
                Keys: "NIFTY50", "BANKNIFTY"
                Columns: open, high, low, close, MACD, MACD_Signal, RSI, ADX
    
    intraday_data: Dict[str, DataFrame] - 15-min OHLC data for each underlying
                   Keys: "NIFTY50", "BANKNIFTY"
                   Columns: open, high, low, close, MACD, MACD_Signal, RSI, ADX, +DI, -DI
    
    vix_data: pd.Series - VIX values aligned with intraday timestamps
    """
    
    bot = TradingBot(initial_capital=100000)
    
    # Get the number of rows in intraday data
    num_rows = len(intraday_data["NIFTY50"])
    
    # Iterate through each 15-minute candle
    for idx in range(num_rows):
        
        # Get current VIX
        current_vix = vix_data.iloc[idx] if idx < len(vix_data) else 15.0
        
        # Get current time for trading hours check
        current_timestamp = intraday_data["NIFTY50"].index[idx]
        current_time = pd.Timestamp(current_timestamp).time()
        
        # Skip if outside trading hours
        if not (pd.Timestamp('09:25').time() <= current_time <= pd.Timestamp('14:30').time()):
            continue
        
        # Process for each underlying
        for underlying in ["NIFTY50", "BANKNIFTY"]:
            
            # Get current data
            current_premium = intraday_data[underlying]['close'].iloc[idx]
            current_underlying_price = intraday_data[underlying]['close'].iloc[idx]
            
            daily_row = daily_data[underlying].iloc[-1]  # Latest daily candle
            
            # Check for exits first
            bot.process_position_exits(underlying, current_premium, current_underlying_price, 
                                      intraday_data[underlying], idx)
            
            # Check for entries (CE)
            if bot.check_reentry_allowed(underlying):
                if bot.check_entry_conditions_ce(underlying, daily_data[underlying], 
                                                intraday_data[underlying], idx, current_vix):
                    entry_premium = current_premium * 0.95  # Assume slight slippage
                    bot.enter_trade(underlying, TradeType.CE, entry_premium, 
                                  current_underlying_price, daily_row['close'], current_vix)
            
            # Check for entries (PE)
            if bot.check_reentry_allowed(underlying):
                if bot.check_entry_conditions_pe(underlying, daily_data[underlying], 
                                                intraday_data[underlying], idx, current_vix):
                    entry_premium = current_premium * 0.95  # Assume slight slippage
                    bot.enter_trade(underlying, TradeType.PE, entry_premium, 
                                  current_underlying_price, daily_row['close'], current_vix)
        
        # Check if EOD (reset daily stats)
        if current_time >= pd.Timestamp('14:30').time():
            bot.reset_daily_stats()
    
    # Print final summary
    bot.print_account_summary()
    bot.save_trades_to_csv("trading_results.csv")
    
    return bot


# ===========================
# EXAMPLE USAGE
# ===========================

if __name__ == "__main__":
    """
    Example of how to use the trading bot
    
    You need to provide:
    1. daily_data: DataFrame with daily OHLC + MACD + RSI + ADX
    2. intraday_data: DataFrame with 15-min OHLC + MACD + RSI + ADX
    3. vix_data: Series with VIX values
    """
    
    print("Trading Bot Ready")
    print("\nUsage:")
    print("------")
    print("1. Load your daily OHLC data for NIFTY50 and BANKNIFTY")
    print("2. Calculate indicators: MACD, RSI, ADX using TechnicalIndicators class")
    print("3. Load 15-minute OHLC data and calculate same indicators")
    print("4. Call: bot = run_trading_bot(daily_data, intraday_data, vix_data)")
    print("\nSee trading_bot.log for detailed execution logs")
    print("See trading_results.csv for all trades")
