"""
F&O Trading Bot - Main Trading Engine
Implements MACD + RSI + ADX strategy for Nifty50 & BankNifty Options
"""

import pandas as pd
import numpy as np
from datetime import datetime
from typing import Optional, Dict, List
from dataclasses import dataclass, field
from enum import Enum
import logging
import threading

from src.indicators import TechnicalIndicators
from src.trading_config import TradingConfig
from src.utils import now_ist, get_current_time_ist, calculate_pnl, calculate_pnl_percentage, console
from src.symbol_master import SymbolMaster
from src.persistence import StateManager
from src.trading_models import TradeType, ExitReason, Position

from rich.table import Table
from rich.panel import Panel
from rich import box

logger = logging.getLogger("rich")


class FnOTradingBot:
    """
    F&O Trading Bot implementing MACD + RSI + ADX strategy
    """
    
    def __init__(self, config: TradingConfig):
        """
        Initialize trading bot
        
        Parameters:
        -----------
        config : TradingConfig
            Trading configuration
        """
        self.config = config
        self.initial_capital = config.initial_capital
        self.current_capital = config.initial_capital
        
        # Threading lock for position/history access
        self.lock = threading.Lock()
        
        # Position tracking
        self.positions: Dict[str, Position] = {}  # Active positions
        # Daily tracking
        self.daily_pnl = 0.0
        self.daily_trades = 0
        self.closed_trades: List[Position] = []  # Initialize early to prevent AttributeError
        
        # Load persisted state
        try:
            # Active positions
            loaded_positions = StateManager.load_positions()
            if loaded_positions:
                self.positions = loaded_positions
                logger.info(f"Restored {len(self.positions)} active positions from state file.")
            
            # Daily closed positions (for has_traded_today logic)
            loaded_history = StateManager.load_history()
            if loaded_history:
                # Keep full history in memory for analytics
                self.closed_trades = loaded_history
                
                # Filter to only include today's trades for daily tracking
                today_date = now_ist().date()
                today_trades = [p for p in loaded_history if p.entry_time.date() == today_date]
                self.daily_trades = len(today_trades)
                self.daily_pnl = sum(p.pnl for p in today_trades if p.pnl is not None)
                logger.info(f"Restored {len(self.closed_trades)} total historical trades ({self.daily_trades} from today).")
        except Exception as e:
            logger.error(f"Error loading state: {e}")
        self.daily_start_capital = config.initial_capital
        
        # Initialize Symbol Master
        logger.info("Initializing Symbol Master...")
        SymbolMaster()
        
        logger.info(f"Trading Bot Initialized | Capital: Rs {self.initial_capital:,.2f}")
        
        # Initial state restored
    
    def check_entry_conditions_ce(
        self,
        underlying: str,
        daily_data: pd.DataFrame,
        intraday_data: pd.DataFrame,
        current_row_idx: int,
        vix: float
    ) -> bool:
        """
        Check all 8 MANDATORY conditions for CALL (CE) entry
        
        Conditions:
        1. No duplicate positions
        2. Trading hours (9:25 AM - 2:30 PM)
        ALL of the following conditions must be met for CE entry:
        1. No existing position in underlying
        2. No duplicate signal on same candle
        3. Time between 9:15 AM - 3:15 PM
        4. VIX >= 10.0
        5. MACD > Signal (bullish)
        6. RSI between 30-65
        7. Daily ADX > 25
        
        Returns:
        --------
        bool
            True if all conditions met
        """
        # DEFENSIVE CODE: Ensure closed_trades exists
        if not hasattr(self, 'closed_trades'):
            self.closed_trades = []

        # Condition 1: No duplicate positions
        with self.lock:
            if underlying in self.positions:
                logger.info(f"{underlying} [CE]: Already in position")
                return False
                
            # Condition 1b: STRICT ANTI-DUPLICATION (Symbol Specific)
            # Prevent re-entering the EXACT SAME option symbol for the day
            # But allow trading PE even if CE was traded (and vice versa)
            
            # Get current ATM strike to check against history
            # We need to know what strike would be selected NOW
            from src.option_selector import OptionSelector
            current_spot = intraday_data['close'].iloc[current_row_idx]
            
            # Predicted strike for the potential new trade
            target_strike = OptionSelector.get_atm_strike(current_spot, underlying)
            
            # Check if we have already traded this specific strike & type today
            today_date = now_ist().date()
            for trade in self.closed_trades:
                if (trade.underlying == underlying and 
                    trade.entry_time.date() == today_date and
                    trade.trade_type == TradeType.CE):
                    
                    # Check strict strike duplication
                    if trade.strike_price is not None:
                        if float(trade.strike_price) == float(target_strike):
                             logger.info(f"{underlying} [CE]: Strike {target_strike} already traded today - FAST REJECTION")
                             return False
                    
                    # Fallback to Spot Price Heuristic if strike_price is missing (old data)
                    last_spot = getattr(trade, 'entry_underlying_price', 0.0)
                    if last_spot > 0 and abs(current_spot - last_spot) < (current_spot * 0.001): # 0.1% buffer
                         logger.info(f"{underlying} [CE]: Spot price {current_spot} too close to previous trade {last_spot} - Avoiding Duplicate Strike")
                         return False

        # Condition 2: Trading hours check
        current_time = get_current_time_ist()
        if not self.config.can_enter_new_position(current_time):
            logger.info(f"{underlying} [CE]: Outside entry hours")
            return False
        
        # Condition 3: VIX filter
        if vix < self.config.vix_min_threshold:
            logger.info(f"{underlying} [CE]: VIX too low ({vix:.2f} < {self.config.vix_min_threshold})")
            return False
        
        # Condition 3b: Daily Profit Cap (Hardcoded Default: Rs 1200)
        daily_pnl = getattr(self, 'daily_pnl', 0.0)
        if daily_pnl >= self.config.daily_profit_limit:
            logger.info(f"{underlying} [CE]: Daily Profit Target (Rs {self.config.daily_profit_limit}) Reached. Trading paused until tomorrow.")
            return False
        
        # Get current row data
        current_row = intraday_data.iloc[current_row_idx]
        
        # Condition 4 & 5: Daily filters removed per user update
        
        # Condition 6: MACD Signal (Smart Entry)
        # 1. First Trade of Day: Enter if Trend is Active (MACD > Signal) - No fresh cross needed
        # 2. Subsequent Trades: Enter ONLY on Fresh Crossover (MACD crosses above Signal)
        
        # Check if we have traded this symbol today
        today_date = now_ist().date()
        
        # DEFENSIVE CODE: Ensure closed_trades exists
        if not hasattr(self, 'closed_trades'):
            self.closed_trades = []
            
        with self.lock:
            trades_today = [
                p for p in self.closed_trades 
                if p.underlying == underlying and p.entry_time.date() == today_date
            ]
        has_traded_today = len(trades_today) > 0
        
        macd_val = intraday_data['MACD'].iloc[current_row_idx]
        signal_val = intraday_data['MACD_Signal'].iloc[current_row_idx]
        
        if not has_traded_today:
            # FIRST TRADE: Relaxed - Just check if Bullish Trend is active
            if macd_val <= signal_val:
                logger.info(f"{underlying} [CE]: MACD not bullish (MACD: {macd_val:.2f} <= Signal: {signal_val:.2f})")
                return False
            logger.info(f"{underlying} [CE]: First Trade - Trend Active. Checking secondary conditions...")
            
        else:
            # SUBSEQUENT TRADES: RELAXED (User Update) - Just check if Bullish Trend is active
            # "Latest update No Fresh crossover Needed"
            if macd_val <= signal_val:
                logger.info(f"{underlying} [CE]: MACD not bullish (Subsequent Trade)")
                return False
            logger.info(f"{underlying} [CE]: Subsequent Trade - Trend Active (No Fresh Cross Needed).")
        
        # Condition 6b: MACD Histogram Momentum (Dark Green)
        # Check if Histogram is positive and increasing
        hist_val = intraday_data['MACD_Hist'].iloc[current_row_idx]
        prev_hist_val = intraday_data['MACD_Hist'].iloc[current_row_idx - 1] if current_row_idx > 0 else 0
        
        if hist_val <= 0 or hist_val <= prev_hist_val:
            logger.info(f"{underlying} [CE]: MACD Histogram not Dark Green (Hist: {hist_val:.2f}, Prev: {prev_hist_val:.2f})")
            return False
        logger.info(f"{underlying} [CE]: MACD Histogram Dark Green (Momentum Increasing).")
        
        # Condition 7: 15m RSI in range (45-65)
        rsi = current_row['RSI']
        if not (self.config.rsi_min <= rsi <= self.config.rsi_max):
            logger.info(f"{underlying} [CE]: RSI Check Failed (Value: {rsi:.2f} | Range: {self.config.rsi_min}-{self.config.rsi_max})")
            return False
        # Condition 8: ADX filter removed per user update

        # Condition 9: Daily ADX > 25
        daily_row = daily_data.iloc[-1]
        daily_adx = daily_row.get('ADX', 0)
        if daily_adx <= self.config.adx_daily_min:
            logger.info(f"{underlying} [CE]: Daily ADX Check Failed (Value: {daily_adx:.2f} | Min: {self.config.adx_daily_min})")
            return False
        
        # All conditions met!
        logger.info(f"OK {underlying}: All CE entry conditions met | RSI={rsi:.2f} | Daily ADX={daily_adx:.2f} | VIX={vix:.2f}")
        return True
    
    def check_entry_conditions_pe(
        self,
        underlying: str,
        daily_data: pd.DataFrame,
        intraday_data: pd.DataFrame,
        current_row_idx: int,
        vix: float
    ) -> bool:
        """
        Check all 8 MANDATORY conditions for PUT (PE) entry
        
        Conditions:
        ALL of the following conditions must be met for PE entry:
        1. No existing position in underlying
        2. No duplicate signal on same candle
        3. Time between 9:15 AM - 3:15 PM
        4. VIX >= 10.0
        5. MACD < Signal (bearish)
        6. RSI between 30-65
        7. Daily ADX > 25
        
        Returns:
        --------
        bool
            True if all conditions met
        """
        # DEFENSIVE CODE: Ensure closed_trades exists
        if not hasattr(self, 'closed_trades'):
            self.closed_trades = []

        # Condition 1: No duplicate positions
        with self.lock:
            if underlying in self.positions:
                logger.info(f"{underlying} [PE]: Already in position")
                return False
                
            # Condition 1b: STRICT ANTI-DUPLICATION (Symbol Specific - PE)
            from src.option_selector import OptionSelector
            current_spot = intraday_data['close'].iloc[current_row_idx]
            
            # Check if we have already traded this specific strike & type today
            today_date = now_ist().date()
            
            # Predicted strike for the potential new trade
            target_strike = OptionSelector.get_atm_strike(current_spot, underlying)
            
            for trade in self.closed_trades:
                if (trade.underlying == underlying and 
                    trade.entry_time.date() == today_date and
                    trade.trade_type == TradeType.PE):
                    
                    # Check strict strike duplication
                    if trade.strike_price is not None:
                        if float(trade.strike_price) == float(target_strike):
                             logger.info(f"{underlying} [PE]: Strike {target_strike} already traded today - FAST REJECTION")
                             return False

                    try:
                        # Heuristic: If Spot Price is within 0.1% of previous trade's entry spot, it's likely the same strike/setup
                        last_spot = getattr(trade, 'entry_underlying_price', 0.0)
                        if last_spot > 0 and abs(current_spot - last_spot) < (current_spot * 0.001): # 0.1% buffer
                             logger.info(f"{underlying} [PE]: Spot price {current_spot} too close to previous trade {last_spot} - Avoiding Duplicate Strike")
                             return False
                    except Exception as e:
                        logger.error(f"Error checking duplicate strike for {underlying}: {e}")
                        continue
        
        # Condition 2: Trading hours check
        current_time = get_current_time_ist()
        if not self.config.can_enter_new_position(current_time):
            logger.info(f"{underlying} [PE]: Outside entry hours")
            return False
        
        # Condition 3: VIX filter
        if vix < self.config.vix_min_threshold:
            logger.info(f"{underlying} [PE]: VIX too low ({vix:.2f} < {self.config.vix_min_threshold})")
            return False
            
        # Condition 3b: Daily Profit Cap (Hardcoded Default: Rs 1200)
        daily_pnl = getattr(self, 'daily_pnl', 0.0)
        if daily_pnl >= self.config.daily_profit_limit:
            logger.info(f"{underlying} [PE]: Daily Profit Target (Rs {self.config.daily_profit_limit}) Reached. Trading paused until tomorrow.")
            return False
        
        # Get current row data
        current_row = intraday_data.iloc[current_row_idx]
        
        # Condition 6: MACD Signal (Smart Entry)
        # 1. First Trade of Day: Enter if Trend is Active (MACD < Signal) - No fresh cross needed
        # 2. Subsequent Trades: Enter ONLY on Fresh Crossover (MACD crosses below Signal)
        
        # Check if we have traded this symbol today
        today_date = now_ist().date()
        with self.lock:
            trades_today = [
                p for p in self.closed_trades 
                if p.underlying == underlying and p.entry_time.date() == today_date
            ]
        has_traded_today = len(trades_today) > 0
        
        macd_val = intraday_data['MACD'].iloc[current_row_idx]
        signal_val = intraday_data['MACD_Signal'].iloc[current_row_idx]
        
        if not has_traded_today:
            # FIRST TRADE: Relaxed - Just check if Bearish Trend is active
            if macd_val >= signal_val:
                logger.info(f"{underlying} [PE]: MACD not bearish (MACD: {macd_val:.2f} >= Signal: {signal_val:.2f})")
                return False
            logger.info(f"{underlying} [PE]: First Trade - Trend Active. Checking secondary conditions...")
            
        else:
            # SUBSEQUENT TRADES: RELAXED (User Update) - Just check if Bearish Trend is active
            if macd_val >= signal_val:
                logger.info(f"{underlying} [PE]: MACD not bearish (Subsequent Trade)")
                return False
            logger.info(f"{underlying} [PE]: Subsequent Trade - Trend Active (No Fresh Cross Needed).")
        
        # Condition 6b: MACD Histogram Momentum (Dark Red)
        # Check if Histogram is negative and decreasing
        hist_val = intraday_data['MACD_Hist'].iloc[current_row_idx]
        prev_hist_val = intraday_data['MACD_Hist'].iloc[current_row_idx - 1] if current_row_idx > 0 else 0
        
        if hist_val >= 0 or hist_val >= prev_hist_val:
            logger.info(f"{underlying} [PE]: MACD Histogram not Dark Red (Hist: {hist_val:.2f}, Prev: {prev_hist_val:.2f})")
            return False
        logger.info(f"{underlying} [PE]: MACD Histogram Dark Red (Momentum Increasing).")
        
        # Condition 7: 15m RSI in range (45-65)
        rsi = current_row['RSI']
        if not (self.config.rsi_min <= rsi <= self.config.rsi_max):
            logger.info(f"{underlying} [PE]: RSI Check Failed (Value: {rsi:.2f} | Range: {self.config.rsi_min}-{self.config.rsi_max})")
            return False
        # Condition 9: Daily ADX > 25
        daily_row = daily_data.iloc[-1]
        daily_adx = daily_row.get('ADX', 0)
        if daily_adx <= self.config.adx_daily_min:
            logger.info(f"{underlying} [PE]: Daily ADX Check Failed (Value: {daily_adx:.2f} | Min: {self.config.adx_daily_min})")
            return False
        
        # All conditions met!
        logger.info(f"OK {underlying}: All PE entry conditions met | RSI={rsi:.2f} | Daily ADX={daily_adx:.2f} | VIX={vix:.2f}")
        return True
    
    def enter_trade(
        self,
        underlying: str,
        trade_type: TradeType,
        entry_price: float,
        entry_underlying_price: float,
        vix: float,
        current_row_idx: int,
        option_symbol: Optional[str] = None,
        strike_price: Optional[float] = None
    ) -> Optional[Position]:
        """
        Enter a new trade
        
        Parameters:
        -----------
        underlying : str
            'NIFTY50' or 'BANKNIFTY'
        trade_type : TradeType
            CE or PE
        entry_price : float
            Premium price at entry
        entry_underlying_price : float
            Spot price at entry
        vix : float
            VIX level
        current_row_idx : int
            Candle index
        option_symbol : str, optional
            Trading symbol
        strike_price : float, optional
            Strike price
Returns:
        --------
        Optional[Position]
            Position object if entered successfully
        """
        # Get VIX-adjusted stop loss (based on underlying movement)
        sl_pct = self.config.get_sl_percentage(underlying, vix)
        
        # Calculate lot size
        lot_size = self.config.get_lot_size(underlying) * self.config.default_num_lots
        
        # Create position
        position_id = f"{underlying}_{trade_type.value}_{datetime.now().strftime('%Y%m%d%H%M%S')}"
        position = Position(
            position_id=position_id,
            underlying=underlying,
            trade_type=trade_type,
            entry_time=now_ist(),
            entry_price=entry_price,
            entry_underlying_price=entry_underlying_price,  # Spot price for SL calculation
            lot_size=lot_size,
            sl_percentage=sl_pct,
            vix_at_entry=vix,
            macd_entry_idx=current_row_idx,
            option_symbol=option_symbol,
            strike_price=strike_price
        )
        with self.lock:
            # Store position
            if underlying in self.positions:
                logger.info(f"{underlying}: Already in position")
                return None
                
            self.positions[underlying] = position
            self.daily_trades += 1
            
            # Persist state
            StateManager.save_positions(self.positions)
            
        logger.info(
            f"[bold green]ENTRY SUCCESSFUL:[/bold green] [cyan]{position_id}[/cyan] | "
            f"Type: [bold yellow]{trade_type.value}[/bold yellow] | "
            f"Premium: [white]Rs {entry_price:.2f}[/white] | "
            f"Spot: [white]{entry_underlying_price:.2f}[/white] | "
            f"SL: [bold red]{sl_pct:.2f}%[/bold red] | "
            f"Qty: [bold white]{lot_size}[/bold white]"
        )
        
        return position
    
    def check_exit_conditions(
        self,
        position: Position,
        current_premium: float,
        current_underlying_price: float,
        current_row_idx: int,
        intraday_data: pd.DataFrame
    ) -> Optional[ExitReason]:
        """
        Check all exit conditions in priority order:
        1. Stop Loss (highest priority)
        2. Profit Target (15%+)
        3. MACD Reversal (only if profit < 15%)
        4. EOD Force Close (2:30 PM)
        
        Parameters:
        -----------
        position : Position
            Active position
        current_premium : float
            Current premium price
        current_underlying_price : float
            Current spot price
        current_row_idx : int
            Current candle index
        intraday_data : pd.DataFrame
            Intraday OHLC data with indicators
            
        Returns:
        --------
        Optional[ExitReason]
            Exit reason if should exit, None otherwise
        """
        # DEBUG LOGGING for Exit Logic
        pnl_pct = position.calculate_pnl_pct(current_premium)
        logger.info(f"[EXIT CHECK] {position.underlying} | LTP: {current_premium} | Entry: {position.entry_price} | P&L: {pnl_pct:.2f}% | SL: {position.sl_percentage:.2f}%")
        
        # Priority 0: SAFETY NET - Max Premium Loss (e.g. -50% or more)
        # This catches "imported" positions that are already deep in loss but have reset "spot entry".
        max_premium_loss = self.config.max_premium_loss_percent
        if pnl_pct <= max_premium_loss:
             logger.warning(f"SAFETY EXIT TRIGGERED: Premium P&L ({pnl_pct:.2f}%) exceeds max loss limit ({max_premium_loss}%)")
             return ExitReason.STOP_LOSS

        # Priority 1: Stop Loss
        if position.check_sl_hit(current_underlying_price):
            return ExitReason.STOP_LOSS
        
        # Priority 2: Profit Target (HARDCODED: Rs 250.0)
        if position.check_profit_hit(current_premium, 250.0):
            return ExitReason.PROFIT_TARGET
        
        # Priority 3: TREND REVERSAL (Immediate Exit)
        # Conditions: MACD Reversal OR DI Crossover Reversal
        # Applies regardless of current profit (Safety Exit)
        # CRITICAL UPDATE: Must be on CANDLE CLOSE (Previous Index)
        # We check index `current_row_idx - 1` to ensure the reversal is CONFIRMED.
        
        reversal_detected = False
        check_idx = current_row_idx - 1  # Check PREVIOUS (Closed) Candle
        
        if check_idx > 0: # Ensure valid index
            if position.trade_type == TradeType.CE:
                # For CALL: Exit if MACD Bearish OR DI Bearish (+DI crosses below -DI)
                macd_rev = TechnicalIndicators.check_macd_crossover_bearish(
                    intraday_data['MACD'],
                    intraday_data['MACD_Signal'],
                    check_idx
                )
                di_rev = TechnicalIndicators.check_di_crossover_bearish(
                    intraday_data['+DI'],
                    intraday_data['-DI'],
                    check_idx
                )
                
                if macd_rev or di_rev:
                    logger.info(f"EXIT SIGNAL {position.underlying}: Trend Reversal CONFIRMED on Candle Close (MACD: {macd_rev}, DI: {di_rev})")
                    return ExitReason.MACD_REVERSAL
                    
            else:
                # For PUT: Exit if MACD Bullish OR DI Bullish (+DI crosses above -DI)
                macd_rev = TechnicalIndicators.check_macd_crossover_bullish(
                    intraday_data['MACD'],
                    intraday_data['MACD_Signal'],
                    check_idx
                )
                di_rev = TechnicalIndicators.check_di_crossover_bullish(
                    intraday_data['+DI'],
                    intraday_data['-DI'],
                    check_idx
                )
                
                if macd_rev or di_rev:
                    logger.info(f"EXIT SIGNAL {position.underlying}: Trend Reversal CONFIRMED on Candle Close (MACD: {macd_rev}, DI: {di_rev})")
                    return ExitReason.MACD_REVERSAL

        
        return None
    
    def exit_trade(
        self,
        underlying: str,
        exit_price: float,
        exit_underlying_price: float,
        exit_reason: ExitReason
    ) -> Optional[Position]:
        """
        Exit an active trade
        """
        with self.lock:
            if underlying not in self.positions:
                logger.warning(f"WARN No active position for {underlying}")
                return None
                
            position = self.positions[underlying]
            
            # Update position with exit details
            position.exit_time = now_ist()
            position.exit_price = exit_price
            position.exit_underlying_price = exit_underlying_price
            position.exit_reason = exit_reason
            position.pnl = position.calculate_pnl(exit_price)
            position.pnl_percentage = position.calculate_pnl_pct(exit_price)
            
            # Update capital and daily P&L
            self.current_capital += position.pnl
            self.daily_pnl += position.pnl
            
            # Move to closed positions
            self.closed_trades.append(position)
            del self.positions[underlying]
            
            # Persist state
            StateManager.save_positions(self.positions)
            StateManager.save_history(self.closed_trades)
        
        pnl_style = "bold green" if position.pnl >= 0 else "bold red"
        exit_symbol = "[PROFIT]" if position.pnl >= 0 else "[LOSS]"
        
        logger.info(
            f"[{pnl_style}]{exit_symbol} EXIT SUCCESSFUL: {position.position_id}[/{pnl_style}] | "
            f"Reason: [bold yellow]{exit_reason.value}[/bold yellow] | "
            f"P&L: [{pnl_style}]Rs {position.pnl:,.2f} ({position.pnl_percentage:+.2f}%)[/{pnl_style}]"
        )
        
        return position
    
    def get_account_summary(self) -> Dict:
        """Get account summary statistics"""
        with self.lock:
            total_trades = len(self.closed_trades)
            winning_trades = sum(1 for p in self.closed_trades if p.pnl > 0)
            losing_trades = total_trades - winning_trades
            win_rate = (winning_trades / total_trades * 100) if total_trades > 0 else 0.0
            
            total_pnl = self.current_capital - self.initial_capital
            total_pnl_pct = (total_pnl / self.initial_capital) * 100
            
            summary = {
                'initial_capital': self.initial_capital,
                'current_capital': self.current_capital,
                'total_pnl': total_pnl,
                'total_pnl_pct': total_pnl_pct,
                'total_trades': total_trades,
                'winning_trades': winning_trades,
                'losing_trades': losing_trades,
                'win_rate': win_rate,
                'open_positions': len(self.positions),
                'daily_pnl': self.daily_pnl,
                'daily_trades': self.daily_trades
            }
        return summary
    
    def print_account_summary(self):
        """Print formatted account summary using Rich table"""
        summary = self.get_account_summary()
        
        table = Table(title="ACCOUNT PERFORMANCE SUMMARY", box=box.DOUBLE_EDGE, header_style="bold cyan")
        table.add_column("Metric", style="dim")
        table.add_column("Value", justify="right")
        
        table.add_row("Initial Capital", f"Rs {summary['initial_capital']:,.2f}")
        table.add_row("Current Capital", f"Rs {summary['current_capital']:,.2f}")
        
        pnl_style = "bold green" if summary['total_pnl'] >= 0 else "bold red"
        table.add_row("Total P&L", f"[{pnl_style}]Rs {summary['total_pnl']:+,.2f} ({summary['total_pnl_pct']:+.2f}%)[/{pnl_style}]")
        
        daily_pnl_style = "bold green" if summary['daily_pnl'] >= 0 else "bold red"
        table.add_row("Daily P&L", f"[{daily_pnl_style}]Rs {summary['daily_pnl']:+,.2f}[/{daily_pnl_style}]")
        
        table.add_section()
        table.add_row("Total Trades", str(summary['total_trades']))
        table.add_row("Winning Trades", f"[green]{summary['winning_trades']}[/green]")
        table.add_row("Losing Trades", f"[red]{summary['losing_trades']}[/red]")
        table.add_row("Win Rate", f"[bold cyan]{summary['win_rate']:.2f}%[/bold cyan]")
        
        table.add_section()
        table.add_row("Active Positions", str(summary['open_positions']))
        table.add_row("Daily Trades", str(summary['daily_trades']))
        
        console.print("\n", table, "\n")
    
    def save_trades_to_csv(self, filename: str):
        """Save all closed trades to CSV file"""
        if not self.closed_trades:
            logger.info("No trades to save")
            return
        
        trades_data = []
        for pos in self.closed_trades:
            trades_data.append({
                'Position_ID': pos.position_id,
                'Underlying': pos.underlying,
                'Type': pos.trade_type.value,
                'Entry_Time': pos.entry_time,
                'Entry_Price': pos.entry_price,
                'Entry_Spot': pos.entry_underlying_price,
                'SL_Percentage': pos.sl_percentage,
                'Exit_Time': pos.exit_time,
                'Exit_Price': pos.exit_price,
                'Exit_Spot': pos.exit_underlying_price,
                'Exit_Reason': pos.exit_reason.value if pos.exit_reason else '',
                'P&L': pos.pnl,
                'P&L_%': pos.pnl_percentage,
                'VIX': pos.vix_at_entry
            })
        
        df = pd.DataFrame(trades_data)
        df.to_csv(filename, index=False)
        logger.info(f"SAVED {len(trades_data)} trades to {filename}")
