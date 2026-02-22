"""
Order Manager Module
Handles order placement and status tracking
"""

import logging
from typing import Optional, Dict
from enum import Enum
from dataclasses import dataclass
from datetime import datetime
import json
import os

logger = logging.getLogger(__name__)


class OrderStatus(Enum):
    """Order status enumeration"""
    PENDING = "PENDING"
    PLACED = "PLACED"
    REJECTED = "REJECTED"
    FILLED = "FILLED"
    CANCELLED = "CANCELLED"
    INSUFFICIENT_FUNDS = "INSUFFICIENT_FUNDS"


@dataclass
class Order:
    """Order data class"""
    order_id: str
    symbol: str
    underlying: str
    strike: int
    option_type: str  # CE/PE
    qty: int
    side: str  # BUY/SELL
    order_time: datetime
    status: OrderStatus
    rejection_reason: Optional[str] = None
    filled_price: Optional[float] = None
    broker_order_id: Optional[str] = None


class OrderManager:
    """Manages order placement and tracking"""
    
    def __init__(self, live_mode: bool = True):
        """
        Initialize order manager
        
        Parameters:
        -----------
        live_mode : bool
            If True, place real orders. If False, paper trading.
        """
        self.live_mode = live_mode
        self.orders: Dict[str, Order] = {}
        self.orders_file = "logs/orders_log.json"
        
        # Load existing orders
        self.load_orders()
    
    def load_orders(self):
        """Load orders from file"""
        if os.path.exists(self.orders_file):
            try:
                with open(self.orders_file, 'r') as f:
                    data = json.load(f)
                    for order_dict in data:
                        order = Order(
                            order_id=order_dict['order_id'],
                            symbol=order_dict['symbol'],
                            underlying=order_dict['underlying'],
                            strike=order_dict['strike'],
                            option_type=order_dict['option_type'],
                            qty=order_dict['qty'],
                            side=order_dict['side'],
                            order_time=datetime.fromisoformat(order_dict['order_time']),
                            status=OrderStatus(order_dict['status']),
                            rejection_reason=order_dict.get('rejection_reason'),
                            filled_price=order_dict.get('filled_price'),
                            broker_order_id=order_dict.get('broker_order_id')
                        )
                        self.orders[order.order_id] = order
            except Exception as e:
                logger.error(f"Error loading orders: {e}")
    
    def save_orders(self):
        """Save orders to file"""
        try:
            os.makedirs("logs", exist_ok=True)
            orders_list = []
            for order in self.orders.values():
                orders_list.append({
                    'order_id': order.order_id,
                    'symbol': order.symbol,
                    'underlying': order.underlying,
                    'strike': order.strike,
                    'option_type': order.option_type,
                    'qty': order.qty,
                    'side': order.side,
                    'order_time': order.order_time.isoformat(),
                    'status': order.status.value,
                    'rejection_reason': order.rejection_reason,
                    'filled_price': order.filled_price,
                    'broker_order_id': order.broker_order_id
                })
            
            with open(self.orders_file, 'w') as f:
                json.dump(orders_list, f, indent=2)
        except Exception as e:
            logger.error(f"Error saving orders: {e}")
    
    def place_order(
        self,
        api,  # MStockAPI instance
        symbol: str,
        underlying: str,
        strike: int,
        option_type: str,
        qty: int,
        side: str,
        exchange: str = "NFO",  # mStock uses NFO for F&O options
        token: str = ""
    ) -> Order:
        """
        Place an order
        
        Parameters:
        -----------
        api : MStockAPI
            API instance
        symbol : str
            Option symbol
        underlying : str
            Underlying (NIFTY50/BANKNIFTY)
        strike : int
            Strike price
        option_type : str
            CE or PE
        qty : int
            Quantity
        side : str
            BUY or SELL
        exchange : str
            Exchange (NFO for F&O)
        token : str
            Argument for symboltoken (optional but recommended)
            
        Returns:
        --------
        Order
            Order object with status
        """
        # Create order ID
        order_id = f"ORDER_{datetime.now().strftime('%Y%m%d%H%M%S%f')}"
        
        # Create order object
        order = Order(
            order_id=order_id,
            symbol=symbol,
            underlying=underlying,
            strike=strike,
            option_type=option_type,
            qty=qty,
            side=side,
            order_time=datetime.now(),
            status=OrderStatus.PENDING
        )
        
        logger.info(f"PLACING ORDER: {side} {qty} x {symbol}")
        
        try:
            if self.live_mode:
                # LIVE MODE: Place real order to mStock
                logger.info(f"DEBUG: Placing Order -> Symbol: '{symbol}', Exch: '{exchange}', Side: '{side}', Qty: {qty}, Type: 'MARKET'")
                
                # If token is missing, try to fetch it dynamically from Quote API
                if not token:
                    logger.info(f"Token missing for {symbol}. Fetching dynamically...")
                    forced_quote = api.get_quote(symbol, exchange)
                    if forced_quote and 'instrument_token' in forced_quote:
                        token = str(forced_quote['instrument_token'])
                        logger.info(f"Dynamic Token Fetched: {token}")
                    else:
                        logger.warning(f"Could not fetch token for {symbol}")

                broker_order_id = api.place_order(
                    symbol=symbol,
                    exchange=exchange,
                    qty=qty,
                    side=side,
                    order_type="MARKET",
                    price=0,
                    paper_mode=False,
                    token=token  # Pass token if available
                )
                
                if broker_order_id:
                    order.status = OrderStatus.PLACED
                    order.broker_order_id = broker_order_id
                    from src.utils import Colors
                    logger.info(Colors.bold_green(f"[SUCCESS] ORDER PLACED! Broker ID: {broker_order_id}"))
                else:
                    order.status = OrderStatus.REJECTED
                    order.rejection_reason = "Order placement failed"
                    from src.utils import Colors
                    logger.error(Colors.bold_red(f"[REJECTED] ORDER REJECTED!"))
            else:
                # PAPER MODE: Simulate order
                order.status = OrderStatus.PLACED
                order.broker_order_id = f"PAPER_{order_id}"
                logger.info(f"PAPER ORDER placed: {symbol}")
        
        except Exception as e:
            error_msg = str(e)
            order.status = OrderStatus.REJECTED
            
            # Check for insufficient funds
            if "insufficient" in error_msg.lower() or "margin" in error_msg.lower():
                order.status = OrderStatus.INSUFFICIENT_FUNDS
                order.rejection_reason = "Insufficient funds"
                logger.error(f"INSUFFICIENT FUNDS for {symbol}")
            else:
                order.rejection_reason = error_msg
                logger.error(f"Order failed: {error_msg}")
        
        # Save order
        self.orders[order_id] = order
        self.save_orders()
        
        return order
    
    def get_recent_orders(self, limit: int = 10) -> list:
        """Get recent orders"""
        sorted_orders = sorted(
            self.orders.values(),
            key=lambda x: x.order_time,
            reverse=True
        )
        return sorted_orders[:limit]
    
    def get_order_summary(self) -> Dict:
        """Get order summary statistics"""
        total = len(self.orders)
        placed = sum(1 for o in self.orders.values() if o.status == OrderStatus.PLACED)
        rejected = sum(1 for o in self.orders.values() if o.status == OrderStatus.REJECTED)
        insufficient_funds = sum(1 for o in self.orders.values() if o.status == OrderStatus.INSUFFICIENT_FUNDS)
        
        return {
            'total_orders': total,
            'placed': placed,
            'rejected': rejected,
            'insufficient_funds': insufficient_funds,
            'success_rate': (placed / total * 100) if total > 0 else 0
        }
