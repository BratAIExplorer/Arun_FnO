"""
mStock API Integration Module
Handles market data fetching, order placement, and position tracking
"""

import requests
import hashlib
import json
import os
from typing import Optional, Dict, List, Tuple
from datetime import datetime
import pandas as pd
from dotenv import load_dotenv
import logging
from urllib.parse import quote
import pytz

logger = logging.getLogger(__name__)


class MStockAPI:
    """mStock API wrapper for market data and order execution"""
    
    def __init__(self):
        """Initialize mStock API with credentials from .env"""
        load_dotenv()
        
        self.api_key = os.getenv('API_KEY')
        self.api_secret = os.getenv('API_SECRET')
        self.client_code = os.getenv('CLIENT_CODE')
        self.password = os.getenv('PASSWORD')
        
        if not all([self.api_key, self.api_secret, self.client_code, self.password]):
            raise ValueError("Missing required environment variables in .env file")
        
        self.access_token = None
        self.load_access_token()
        
        self.base_url = "https://api.mstock.trade/openapi/typea"
        self.headers_base = {"X-Mirae-Version": "1"}
    
    def load_access_token(self):
        """Load access token from credentials.json"""
        try:
            with open("credentials.json", "r") as f:
                creds = json.load(f)
                self.access_token = creds.get("mstock", {}).get("access_token")
        except FileNotFoundError:
            logger.warning("credentials.json not found, will need to authenticate")
    
    def save_access_token(self, token: str):
        """Save access token to credentials.json"""
        try:
            with open("credentials.json", "r") as f:
                creds = json.load(f)
        except FileNotFoundError:
            creds = {}
        
        creds["mstock"] = {"access_token": token}
        with open("credentials.json", "w") as f:
            json.dump(creds, f, indent=2)
        
        self.access_token = token
    
    def initiate_login(self) -> bool:
        """
        Step 1: Initiate login to send OTP
        Returns True if successful
        """
        try:
            login_url = f"{self.base_url}/connect/login"
            login_payload = {"username": self.client_code, "password": self.password}
            headers = {**self.headers_base, "Content-Type": "application/x-www-form-urlencoded"}
            
            login_resp = requests.post(login_url, data=login_payload, headers=headers, timeout=(30, 60))
            if login_resp.status_code != 200:
                logger.error(f"Login failed: {login_resp.status_code}")
                return False
            
            login_data = login_resp.json()
            if login_data.get("status") != "success":
                logger.error(f"Login error: {login_data}")
                return False
            
            logger.info("Login initiated, OTP requested")
            return True
            
        except Exception as e:
            logger.error(f"Error initiating login: {e}")
            return False

    def complete_login(self, otp: str) -> bool:
        """
        Step 2: Complete login with OTP to get access token
        Returns True if successful
        """
        try:
            # Generate checksum
            checksum_str = self.api_key + otp + self.api_secret
            checksum = hashlib.sha256(checksum_str.encode()).hexdigest()
            
            # Get session token
            session_url = f"{self.base_url}/session/token"
            session_payload = {
                "api_key": self.api_key,
                "request_token": otp,
                "checksum": checksum
            }
            session_headers = {**self.headers_base, "Content-Type": "application/x-www-form-urlencoded"}
            
            session_resp = requests.post(session_url, data=session_payload, headers=session_headers, timeout=(30, 60))
            if session_resp.status_code != 200:
                logger.error(f"Session generation failed: {session_resp.status_code}")
                return False
            
            session_data = session_resp.json()
            if session_data.get("status") != "success":
                logger.error(f"Session error: {session_data}")
                return False
            
            # Save access token
            access_token = session_data["data"]["access_token"]
            self.save_access_token(access_token)
            
            logger.info("Access token generated successfully via OTP")
            return True
            
        except Exception as e:
            logger.error(f"Error completing login: {e}")
            return False

    def refresh_token(self) -> bool:
        """
        Full authentication flow (interactive)
        Used by authenticate.py
        """
        if self.initiate_login():
            otp = input("Enter OTP sent to your registered device: ")
            return self.complete_login(otp)
        return False
    
    def get_headers(self) -> Dict[str, str]:
        """Get headers with authorization"""
        return {
            "Authorization": f"token {self.api_key}:{self.access_token}",
            **self.headers_base
        }
    
    def get_quote(self, symbol: str, exchange: str = "NSE") -> Optional[Dict]:
        """
        Get current market quote for a symbol
        
        Parameters:
        -----------
        symbol : str
            Trading symbol (e.g., 'NIFTY 50', 'NIFTY BANK')
        exchange : str
            Exchange (NSE/BSE)
            
        Returns:
        --------
        Optional[Dict]
            Quote data with last_price, ohlc, etc.
        """
        try:
            url = f"{self.base_url}/instruments/quote/ohlc"
            params = {"i": f"{exchange}:{symbol.upper()}"}
            
            response = requests.get(url, headers=self.get_headers(), params=params, timeout=(30, 60))
            if response.status_code != 200:
                logger.error(f"Quote fetch error for {symbol}: {response.status_code}")
                return None
            
            data = response.json()
            if data.get("status") == "success":
                return data.get("data", {}).get(params["i"])
            
            return None
            
        except Exception as e:
            logger.error(f"Error fetching quote for {symbol}: {e}")
            return None
    
    def get_hybrid_history(
        self,
        symbol: str,
        exchange: str,
        instrument_token: str,
        timeframe: str = "15minute",
        days: int = 10
    ) -> Optional[pd.DataFrame]:
        """
        Fetch history from mStock and fill missing today's bars from yfinance.
        """
        # 1. Fetch from mStock (Standard)
        mstock_df = self.get_historical_data(symbol, exchange, instrument_token, timeframe, days)
        
        # If we need today's data for an index, check for gap
        ist = pytz.timezone("Asia/Kolkata")
        now = datetime.now(ist)
        
        # Only use hybrid for major indices
        yf_symbols = {
            "NIFTY 50": "^NSEI",
            "NIFTY BANK": "^NSEBANK",
            "NIFTY FIN SERVICE": "NIFTY_FIN_SERVICE.NS",
            "SENSEX": "^BSESN"
        }
        
        if symbol in yf_symbols and timeframe == "15minute":
            try:
                import yfinance as yf
                yf_ticker = yf_symbols[symbol]
                
                # Fetch last 3 days from yfinance (15m)
                yf_df = yf.download(yf_ticker, period="3d", interval="15m", progress=False, auto_adjust=False)
                
                if yf_df is not None and not yf_df.empty:
                    # Clean up yfinance columns
                    yf_df.columns = [col[0] if isinstance(col, tuple) else col for col in yf_df.columns]
                    yf_df = yf_df.rename(columns={
                        'Open': 'open', 'High': 'high', 'Low': 'low', 'Close': 'close'
                    })
                    yf_df = yf_df[['open', 'high', 'low', 'close']]
                    
                    # Convert index to IST
                    if yf_df.index.tz is None:
                        yf_df.index = yf_df.index.tz_localize("UTC").tz_convert("Asia/Kolkata")
                    else:
                        yf_df.index = yf_df.index.tz_convert("Asia/Kolkata")
                    
                    # Filter only market hours
                    yf_df = yf_df.between_time("09:15", "15:30")
                    
                    if mstock_df is None or mstock_df.empty:
                        return yf_df
                    
                    # Stitching logic:
                    # Keep mstock_df as base, append yf_df bars that are NOT in mstock_df
                    last_mstock_time = mstock_df.index[-1]
                    missing_bars = yf_df[yf_df.index > last_mstock_time]
                    
                    if not missing_bars.empty:
                        logger.info(f"Hybrid Data: Added {len(missing_bars)} missing bars from yfinance for {symbol}")
                        combined_df = pd.concat([mstock_df, missing_bars])
                        return combined_df
                        
            except Exception as e:
                logger.warning(f"Failed to fetch hybrid data from yfinance for {symbol}: {e}")
                
        return mstock_df

    def get_historical_data(
        self,
        symbol: str,
        exchange: str,
        instrument_token: str,
        timeframe: str = "15minute",
        days: int = 10
    ) -> Optional[pd.DataFrame]:
        """
        Fetch historical OHLC data
        
        Parameters:
        -----------
        symbol : str
            Trading symbol
        exchange : str
            Exchange (NSE/BSE)
        instrument_token : str
            Instrument token
        timeframe : str
            '1minute', '5minute', '15minute', '60minute', 'day'
        days : int
            Number of days of history
            
        Returns:
        --------
        Optional[pd.DataFrame]
            OHLC dataframe with datetime index
        """
        try:
            # Build time window
            from datetime import timedelta
            import pytz
            
            ist = pytz.timezone("Asia/Kolkata")
            now_ist = datetime.now(ist)
            from_dt = (now_ist - timedelta(days=days)).replace(hour=9, minute=15, second=0, microsecond=0)
            to_dt = now_ist
            
            from_encoded = quote(from_dt.strftime("%Y-%m-%d %H:%M:%S"))
            to_encoded = quote(to_dt.strftime("%Y-%m-%d %H:%M:%S"))
            
            url = (
                f"{self.base_url}/instruments/historical/"
                f"{exchange.upper()}/{instrument_token}/{timeframe}"
                f"?from={from_encoded}&to={to_encoded}"
            )
            
            response = requests.get(url, headers=self.get_headers(), timeout=(30, 60))
            if response.status_code != 200:
                logger.error(f"Historical data error: {response.status_code}")
                return None
            
            data = response.json()
            if data.get("status") != "success":
                logger.error(f"Historical data fetch failed: {data.get('message')}")
                return None
            
            candles = data.get("data", {}).get("candles", [])
            if not candles:
                logger.warning(f"No candles returned for {symbol}")
                return None
            
            # Convert to DataFrame
            cols = ["timestamp", "open", "high", "low", "close", "volume"]
            df = pd.DataFrame(candles, columns=cols)
            df["timestamp"] = pd.to_datetime(df["timestamp"], utc=True).dt.tz_convert("Asia/Kolkata")
            df.set_index("timestamp", inplace=True)
            
            # Filter market hours
            if timeframe != "day":
                df = df.between_time("09:15", "15:30")
            
            return df[["open", "high", "low", "close"]]
            
        except Exception as e:
            logger.error(f"Error fetching historical data for {symbol}: {e}")
            return None
    
    def get_positions(self) -> Optional[Dict[Tuple[str, str], Dict]]:
        """
        Get current holdings (Equity/Long-term)
        """
        try:
            url = f"{self.base_url}/portfolio/holdings"
            response = requests.get(url, headers=self.get_headers(), timeout=(30, 60))
            
            if response.status_code != 200:
                logger.error(f"Holdings fetch error: {response.status_code}")
                return None
            
            data = response.json()
            positions_list = data.get("data", []) or []
            
            positions = {}
            for pos in positions_list:
                symbol = pos.get("tradingsymbol")
                qty = pos.get("quantity", 0)
                if qty > 0:
                    exchange = pos.get("exchange") or pos.get("exchangeSegment") or "NSE"
                    positions[(symbol, exchange)] = {
                        "qty": qty,
                        "price": pos.get("averageprice", pos.get("price", 0.0)),
                        "ltp": pos.get("last_price", 0.0),
                        "pnl": pos.get("pnl", 0.0)
                    }
            
            return positions
            
        except Exception as e:
            logger.error(f"Error fetching holdings: {e}")
            return None

    def get_net_positions(self, timeout=(30, 60)) -> Optional[List[Dict]]:
        """
        Get all Active F&O Net Positions (Today's Open/Closed positions)
        Includes Manual and Bot trades.
        """
        try:
            # Endpoint verified for Daywise Net Positions
            url = f"{self.base_url}/portfolio/positions"
            response = requests.get(url, headers=self.get_headers(), timeout=timeout)
            
            if response.status_code != 200:
                logger.error(f"Net Positions fetch error: {response.status_code}")
                return None
                
            data = response.json()
            if data.get("status") != "success":
                return None
                
            positions = data.get("data", [])
            
            # Robustness: Handle Dict response (e.g. {'net': [...], 'day': [...]})
            if isinstance(positions, dict):
                # Mirae/mStock often returns {'net': [...], 'day': [...]}
                # We want 'net' typically, but let's combine or prioritize net.
                # Actually, 'net' is usually what we want (open positions).
                # 'day' might be today's activity?
                # Let's aggregate both to be safe, or just take 'net'.
                # Recommendation: Use 'net' as it represents the actual open position.
                
                net_pos = positions.get('net', [])
                day_pos = positions.get('day', [])
                
                if isinstance(net_pos, list):
                    return net_pos
                elif isinstance(day_pos, list):
                    return day_pos
                else:
                    return []
                    
            elif isinstance(positions, list):
                return positions
            else:
                logger.warning(f"Net positions returned unexpected type: {type(positions)}")
                return []
            
        except Exception as e:
            logger.error(f"Error fetching net positions: {e}")
            return None

    def get_tradebook(self, timeout=(30, 60)) -> Optional[List[Dict]]:
        """
        Get all Trades executed today (Manual + Bot)
        """
        try:
            # Tradebook endpoint
            url = f"{self.base_url}/orders/tradebook"
            # Some APIs require GET, some require POST. Probing showed 405 for GET.
            # Try POST with empty payload if GET fails, but usually Mirae is GET. 
            # If 405, it might be a different endpoint or specific to Type A/B.
            response = requests.get(url, headers=self.get_headers(), timeout=timeout)
            
            if response.status_code != 200:
                if response.status_code == 405:
                    logger.warning("Tradebook endpoint returned 405 (Method Not Allowed). Skipping tradebook fetch.")
                    return []
                
                # Fallback check for alternate endpoint
                url_alt = f"{self.base_url}/orders/trades"
                response = requests.get(url_alt, headers=self.get_headers(), timeout=timeout)
                
            if response.status_code != 200:
                logger.error(f"Tradebook fetch error: {response.status_code}")
                return None
                
            data = response.json()
            trades = data.get("data", [])
            
            # Robustness check
            if isinstance(trades, list):
                return trades
            elif isinstance(trades, dict):
                logger.warning("Tradebook returned dict instead of list")
                return []
                
            return []
            
        except Exception as e:
            logger.error(f"Error fetching tradebook: {e}")
            return None

    def get_historical_trades(self, from_date: str, to_date: str) -> Optional[List[Dict]]:
        """
        Fetch historical trades for a date range (if supported)
        from_date / to_date format: YYYY-MM-DD
        """
        try:
            url = f"{self.base_url}/reports/tradelist"
            params = {"from": from_date, "to": to_date}
            response = requests.get(url, headers=self.get_headers(), params=params, timeout=(30, 60))
            
            if response.status_code == 200:
                data = response.json()
                return data.get("data", [])
            return None
        except: return None
    
    def place_order(
        self,
        symbol: str,
        exchange: str,
        qty: int,
        side: str,  # 'BUY' or 'SELL'
        order_type: str = "MARKET",
        price: float = 0,
        paper_mode: bool = True,
        token: str = ""
    ) -> Optional[str]:
        """
        Place an order
        
        Parameters:
        -----------
        symbol : str
            Trading symbol
        exchange : str
            Exchange
        qty : int
            Quantity
        side : str
            'BUY' or 'SELL'
        order_type : str
            'MARKET' or 'LIMIT'
        price : float
            Limit price (for LIMIT orders)
        paper_mode : bool
            If True, don't place real order (paper trading)
            
        Returns:
        --------
        Optional[str]
            Order ID if successful, None if failed
        """
        if paper_mode:
            logger.info(
                f"PAPER TRADE: {side} {qty} x {symbol} @ {exchange} | "
                f"Type: {order_type} {f'@ Rs {price}' if order_type == 'LIMIT' else ''}"
            )
            # Return mock order ID
            return f"PAPER_{datetime.now().strftime('%Y%m%d%H%M%S')}"
        
        # LIVE MODE: Place real order
        try:
            # Type A API usually requires Order Variety in URL
            url = f"{self.base_url}/orders/regular"
            
            # Construct Form Data Payload (application/x-www-form-urlencoded)
            # Keys verified via documentation: transaction_type, order_type, etc.
            payload = {
                "tradingsymbol": symbol,
                "exchange": exchange.upper(),
                "transaction_type": side,   # Changed from transactiontype
                "order_type": order_type,   # Changed from ordertype
                "quantity": str(qty),
                "product": "NRML",          # Default to NRML for F&O. Doc used MIS.
                "validity": "DAY", 
            }
            
            # Optional Price for LIMIT
            if order_type == "LIMIT":
                payload["price"] = str(price)
                
            # Add token if available (though testing showed it works without)
            if token:
                payload["symboltoken"] = str(token)

            headers = {
                **self.get_headers(),
                "Content-Type": "application/x-www-form-urlencoded"
            }
            
            # Debug: Log the exact payload
            logger.info(f"Placing LIVE order: {side} {qty} x {symbol}")
            logger.info(f"DEBUG Payload: {payload}")
            
            # Use data=payload for Form Data (not json=payload)
            response = requests.post(url, data=payload, headers=headers, timeout=(30, 60))
            
            if response.status_code != 200:
                logger.error(f"ERROR Order placement failed: HTTP {response.status_code}")
                logger.error(f"Response: {response.text}")
                return None
            
            data = response.json()
            
            # Handle List response (API returns list of dicts)
            responseData = {}
            if isinstance(data, list) and len(data) > 0:
                responseData = data[0]
            elif isinstance(data, dict):
                responseData = data
            
            if responseData.get("status") == "success":
                # Extract Order ID
                # Response format: [{"status": "success", "data": {"order_id": "..."}}]
                order_id = responseData.get("data", {}).get("order_id") # Note: order_id (underscore?)
                # Check debug output: 'order_id': '13422602062692'
                
                # Check if it was "orderid" in previous code?
                if not order_id:
                     order_id = responseData.get("data", {}).get("orderid")
                     
                logger.info(f"Order placed successfully! Order ID: {order_id}")
                return order_id
            else:
                error_msg = responseData.get("message", "Unknown error")
                logger.error(f"Order rejected: {error_msg}")
                
                # Check for insufficient funds
                if "insufficient" in str(error_msg).lower() or "margin" in str(error_msg).lower():
                    raise Exception("Insufficient funds")
                
                return None
                
        except Exception as e:
            logger.error(f"ERROR placing order: {e}")
            raise e

