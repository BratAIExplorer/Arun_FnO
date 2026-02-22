"""
Position Sync Module
Syncs positions from broker API to bot tracking
"""

import logging
from typing import List, Optional
from datetime import datetime
from src.trading_models import TradeType, ExitReason
from src.market_data import MStockAPI

logger = logging.getLogger(__name__)


def sync_positions_from_broker(bot, api: MStockAPI) -> int:
    """
    Sync open positions from broker to bot tracking
    
    Parameters:
    -----------
    bot : FnOTradingBot
        Trading bot instance
    api : MStockAPI
        API instance
        
    Returns:
    --------
    int
        Number of positions synced
    """
    try:
        # RETRY LOGIC for 500 errors
        import time
        max_retries = 3
        positions_dict = None
        
        for attempt in range(max_retries):
            positions_dict = api.get_positions()
            if positions_dict is not None:
                break
            if attempt < max_retries - 1:
                logger.warning(f"Positions fetch failed (Attempt {attempt+1}/{max_retries}). Retrying in 2s...")
                time.sleep(2)
        
        # CRITICAL HARDENING: Handle API Error vs Empty Portfolio
        if positions_dict is None:
            logger.error("!!! BROKER CONNECTION BREACH (HTTP 500) !!!")
            
            # CHECK LOCAL MEMORY
            if bot.positions:
                logger.warning(f"ENTERING 'BLIND MONITORING' MODE: Using Local Memory for {len(bot.positions)} positions.")
                logger.info("The bot will continue to monitor your EXIT conditions using local data until the broker recovers.")
                return len(bot.positions)
            else:
                logger.error("NO LOCAL MEMORY FOUND. Bot is blind to carry-forward positions until API recovers.")
                return 0
            

            
        # Also fetch Net Positions (F&O / Intraday)
        net_positions_list = api.get_net_positions()
        if net_positions_list:
            # Convert list to dict format compatible with loop below
            # Structure: {(symbol, exchange): {'qty': qty, 'price': price, ...}}
            if positions_dict is None: positions_dict = {}
            
            for pos in net_positions_list:
                sym = pos.get('tradingsymbol')
                exc = pos.get('exchange')
                qty = pos.get('quantity', 0)
                if qty == 0: qty = pos.get('netQuantity', 0) # Handle netQuantity
                
                if sym and exc:
                    positions_dict[(sym, exc)] = {
                        'qty': qty,
                        'price': pos.get('averagePrice', pos.get('avgPrice', 0.0)),
                        'ltp': pos.get('lastPrice', 0.0)
                    }
            
        # Track which underlyings are active in broker
        broker_underlyings = set()
        synced_count = 0
        
        # Process the positions dictionary
        for (symbol, exchange), pos_data in positions_dict.items():
            qty = pos_data.get('qty', 0)
            
            # Skip if quantity is 0 or negative
            if qty <= 0:
                continue
                
            # Filter for F&O Options (NSE/NFO/BSE/BFO)
            if exchange not in ['NSE', 'NFO', 'BSE', 'BFO']:
                continue
            
            # Parse symbol: NIFTY-10Feb2026-25800-CE or NIFTY 10FEB26 23000 CE
            symbol_clean = symbol.replace('-', ' ')
            parts = symbol_clean.split()
            
            # We need at least Underlying, Expiry/Strike, and Type (e.g., NIFTY 23000 CE)
            if len(parts) < 3:
                continue
            
            # Common pattern: Underlying is first, Option Type is last
            underlying_raw = parts[0]
            # Special case for "NIFTY 50" or "NIFTY BANK"
            if underlying_raw == "NIFTY" and len(parts) > 1:
                if parts[1] == "50":
                     underlying_raw = "NIFTY50"
                     parts.pop(1)
                elif parts[1] == "BANK":
                     underlying_raw = "BANKNIFTY"
                     parts.pop(1)
            
            option_type = parts[-1] if parts[-1] in ['CE', 'PE'] else None
            if not option_type:
                continue

            # Try to extract strike price (usually second to last or explicitly numeric)
            strike_price = None
            try:
                # Iterate parts to find the strike
                for p in parts:
                    if p.isdigit() or (p.replace('.', '', 1).isdigit() and float(p) > 1000):
                         strike_price = float(p)
            except:
                pass
            
            underlying_map = {
                "NIFTY": "NIFTY50",
                "NIFTY50": "NIFTY50",
                "BANKNIFTY": "BANKNIFTY",
                "NIFTYBANK": "BANKNIFTY",
                "FINNIFTY": "FINNIFTY",
                "NIFTYFIN": "FINNIFTY",
                "SENSEX": "SENSEX"
            }
            underlying = underlying_map.get(underlying_raw.upper(), underlying_raw.upper())
            
            # CRITICAL: Normalize Symbol for Quote Fetching
            # API returns: NIFTY-10Feb2026-25500-PE
            # Quote needs: NIFTY 10FEB26 25500 PE (or similar)
            # We can reconstruct it or use SymbolMaster if possible.
            # Let's try to reconstruct strictly based on mStock pattern: SYMBOL DDMMMYY STRIKE TYPE
            # Or better, just format it as the "instrument name" which usually works.
            # But debug_option_chain saw: NIFTY26FEB24000CE (Algorithm) working.
            # Let's try to generate the "algorithmic" symbol that SymbolMaster uses.
            
            # Parse Date: 10Feb2026
            # We need to be careful. Let's use SymbolMaster to find the "mStock Code" if possible.
            # Or just reformat manually to: NIFTY + YY + MMM + Strike + Type (e.g. NIFTY26FEB25500PE)
            
            try:
                # 10Feb2026 -> datetime
                import datetime
                # Handle "10Feb2026"
                expiry_dt = datetime.datetime.strptime(parts[1], "%d%b%Y")
                
                # Use SymbolMaster for robust normalization
                from src.symbol_master import SymbolMaster
                symbol_final = SymbolMaster().get_symbol(underlying, expiry_dt, strike_price, option_type)
                
                if not symbol_final:
                    # Final Fallback if SymbolMaster failed
                    logger.warning(f"SymbolMaster could not resolve {underlying} {parts[1]}. Using raw symbol {symbol}")
                    symbol_final = symbol
                else:
                    logger.info(f"Normalized Symbol: {symbol_final} (from {symbol})")
                
            except Exception as e:
                logger.warning(f"Could not normalize symbol {symbol}: {e}")
                symbol_final = symbol
            
            # Use the normalized symbol for tracking
            tracking_symbol = symbol_final
            
            # Mark as active in broker
            broker_underlyings.add(underlying)
            
            # Check if ALREADY tracking (Restored from state)
            if underlying in bot.positions:
                logger.info(f"Verified {underlying} position matches broker. Maintaining state.")
                bot.positions[underlying].lot_size = int(qty)
                # Update symbol details if missing or invalid (broker raw format has hyphens)
                current_sym = bot.positions[underlying].option_symbol
                if not current_sym or "-" in current_sym:
                     bot.positions[underlying].option_symbol = tracking_symbol
                     logger.info(f"Updated {underlying} symbol to {tracking_symbol} (was {current_sym})")
                if not bot.positions[underlying].strike_price and strike_price:
                     bot.positions[underlying].strike_price = strike_price
                continue
            
            # Determine trade type
            trade_type = TradeType.CE if option_type == "CE" else TradeType.PE
            
            # Get current market data (Estimation for NEW trades only)
            spot_symbol_map = {
                "NIFTY50": "NIFTY 50",
                "BANKNIFTY": "NIFTY BANK",
                "FINNIFTY": "NIFTY FIN SERVICE",
                "SENSEX": "SENSEX"
            }
            spot_symbol = spot_symbol_map.get(underlying, underlying)
            
            # Use correct exchange for spot fetch
            spot_exchange = "BSE" if underlying == "SENSEX" else "NSE"
            quote = api.get_quote(spot_symbol, spot_exchange)

            current_spot = quote.get('last_price', 0) if quote else 0
            
            # Get VIX
            try:
                vix_quote = api.get_quote("INDIA VIX", "NSE")
                current_vix = vix_quote.get('last_price', 15.0) if vix_quote else 15.0
            except:
                current_vix = 15.0
            
            # Try to fetch current LTP for more accurate imported position state
            opt_exchange = "BFO" if underlying == "SENSEX" else "NFO"
            opt_quote = api.get_quote(tracking_symbol, opt_exchange)
            current_premium_ltp = opt_quote.get('last_price', 0.0) if opt_quote else 0.0
            
            # Estimate entry premium: Broker Avg -> Current LTP -> Fallback
            avg_price = pos_data.get('price', 0)
            entry_premium = avg_price if avg_price > 0 else (current_premium_ltp if current_premium_ltp > 0 else (current_spot * 0.015))
            
            # Import NEW position (Manual or unsaved carried forward)
            logger.info(f"IMPORTING CARRIED POSITION: {tracking_symbol} (Qty: {qty}, Avg: {avg_price})")
            
            # We use enter_trade to initialize monitoring
            bot.enter_trade(
                underlying=underlying,
                trade_type=trade_type,
                entry_price=entry_premium,
                entry_underlying_price=current_spot,
                vix=current_vix,
                current_row_idx=0,
                option_symbol=tracking_symbol,
                strike_price=strike_price
            )
            
            # Update lot size specifically to match broker
            if underlying in bot.positions:
                 bot.positions[underlying].lot_size = int(qty)
            
            synced_count += 1

        # RECONCILIATION: Check for "Zombie" positions
        for underlying in list(bot.positions.keys()):
            if underlying not in broker_underlyings:
                logger.warning(f"Position {underlying} found in State but CLOSED in Broker. Removing.")
                bot.exit_trade(
                    underlying=underlying,
                    exit_price=0,      
                    exit_underlying_price=0,
                    exit_reason=ExitReason.BROKER_SYNC_EXIT
                )

        if synced_count > 0:
            logger.info(f"Synced {synced_count} new position(s) from broker")
        else:
            logger.info("Sync complete. State matches Broker.")
            
        return synced_count
        
    except Exception as e:
        logger.error(f"Error syncing positions: {e}")
        return 0
