from datetime import datetime
from typing import Optional
from dataclasses import dataclass
from enum import Enum

class TradeType(Enum):
    """Trade type enumeration"""
    CE = "CALL"
    PE = "PUT"


class ExitReason(Enum):
    """Exit reason enumeration"""
    PROFIT_TARGET = "Profit Target Hit"
    STOP_LOSS = "Stop Loss Hit"
    MACD_REVERSAL = "MACD Reversal"
    EOD_CLOSE = "EOD Force Close"
    BROKER_SYNC_EXIT = "Broker Sync Reconciliation"


@dataclass
class Position:
    """Trading position data class"""
    position_id: str
    underlying: str  # "NIFTY50" or "BANKNIFTY"
    trade_type: TradeType  # CE or PE
    entry_time: datetime
    entry_price: float  # Premium price
    entry_underlying_price: float  # Spot price
    lot_size: int
    sl_percentage: float
    vix_at_entry: float
    option_symbol: Optional[str] = None # Added for strict anti-duplication
    strike_price: Optional[float] = None # Added for strict anti-duplication
    
    exit_time: Optional[datetime] = None
    exit_price: Optional[float] = None
    exit_underlying_price: Optional[float] = None
    exit_reason: Optional[ExitReason] = None
    pnl: Optional[float] = None
    pnl_percentage: Optional[float] = None
    
    macd_entry_idx: Optional[int] = None  # Track which candle had entry signal
    
    def calculate_pnl(self, current_premium: float) -> float:
        """Calculate current P&L"""
        return (current_premium - self.entry_price) * self.lot_size
    
    def calculate_pnl_pct(self, current_premium: float) -> float:
        """Calculate current P&L percentage"""
        if self.entry_price == 0:
            # If entry price is zero, we cannot calculate exact percentage.
            # But if current premium is also low, it's likely a significant loss.
            # We return a sentinel value (-100.0) to trigger safety net if LTP is near zero.
            if current_premium < 2.0: # Near worthless
                return -99.9
            return 0.0
        return ((current_premium - self.entry_price) / self.entry_price) * 100
    
    def check_sl_hit(self, current_spot: float) -> bool:
        """
        Check if stop loss is hit based on UNDERLYING SPOT MOVEMENT
        
        For CE (Call): SL triggers when spot DROPS by sl_percentage
        For PE (Put): SL triggers when spot RISES by sl_percentage
        """
        if self.entry_underlying_price == 0:
            return False
            
        spot_movement_pct = ((current_spot - self.entry_underlying_price) / self.entry_underlying_price) * 100
        
        if self.trade_type == TradeType.CE:
            # CE loses value when spot drops
            return spot_movement_pct <= -self.sl_percentage
        else:
            # PE loses value when spot rises
            return spot_movement_pct >= self.sl_percentage
    
    def check_profit_hit(self, current_premium: float, profit_target_amount: float) -> bool:
        """
        Check if profit target is hit based on AMOUNT
        """
        pnl = self.calculate_pnl(current_premium)
        return pnl >= profit_target_amount
