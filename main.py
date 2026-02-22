"""
F&O Trading Bot - Main Entry Point
Monitors market and executes trades based on technical indicators
"""

import pandas as pd
import logging
import os
import sys
import time
import threading
import json
from datetime import datetime

# Add src to path
sys.path.insert(0, os.path.dirname(__file__))

from src.fno_trading_bot import FnOTradingBot
from src.trading_models import TradeType, ExitReason
from src.indicators import TechnicalIndicators
from src.trading_config import TradingConfig, config
from src.market_data import MStockAPI
from src.utils import setup_logging, now_ist, is_trading_day, console, print_holographic_banner
from src.option_selector import OptionSelector
from src.order_manager import OrderManager
from src.symbol_master import SymbolMaster
from src.position_sync import sync_positions_from_broker
from src.position_sync import sync_positions_from_broker

from rich.panel import Panel
from rich.live import Live
from rich.table import Table
from rich import box
from rich.layout import Layout

# Setup futuristic logging
os.makedirs("logs", exist_ok=True)
log_file = f"logs/trading_bot_{datetime.now().strftime('%Y%m%d')}.log"
logger = setup_logging(log_file)

# Global shutdown flag
shutdown_event = threading.Event()


def wait_for_market_open():
    """Wait until market opens"""
    from datetime import time as dtime
    
    while not shutdown_event.is_set():
        current_time = now_ist()
        
        # Check if trading day with strict logging
        if not is_trading_day(current_time):
            # Calculate next Monday 9:15 AM
            days_ahead = 7 - current_time.weekday()
            if days_ahead == 0: days_ahead = 7 # If today is Monday but called before open? No, Monday=0.
            # If today is Saturday(5) -> Mon(0) is +2 days. 7-5=2. Correct.
            # If today is Sunday(6) -> Mon(0) is +1 day. 7-6=1. Correct.
            
            logger.info(f"MARKET CLOSED (Weekend/Holiday). System in SLEEP MODE.")
            logger.info(f"Will resume automatically on Monday at 09:15 AM.")
            time.sleep(3600)
            continue
        
        # Check if during market hours
        current_time_only = current_time.time()
        if config.market_open <= current_time_only <= config.market_close:
            logger.info("Market is OPEN - Starting trading bot")
            return
        
        # Calculate wait time
        if current_time_only < config.market_open:
            logger.info(f"Waiting for market to open at {config.market_open}")
            time.sleep(60)
        else:
            logger.info("Market closed for today. Will resume tomorrow.")
            time.sleep(3600)


def get_market_data_with_indicators(
    api: MStockAPI,
    symbol: str,
    exchange: str,
    instrument_token: str
) -> tuple:
    """
    Fetch market data and calculate indicators with REAL-TIME live candle
    Creates streaming indicators that update every second
    """
    try:
        # Get current spot price FIRST for live candle
        quote = api.get_quote(symbol, exchange)
        current_spot = quote.get('last_price', 0) if quote else 0
        
        # Fetch daily data
        daily_df = api.get_historical_data(symbol, exchange, instrument_token, "day", days=60)
        if daily_df is None or len(daily_df) < 30:
            logger.error(f"Insufficient daily data for {symbol}")
            return None, None, None, None
        
        # Calculate daily indicators (no live candle needed)
        daily_df['MACD'], daily_df['MACD_Signal'], daily_df['MACD_Hist'] = \
            TechnicalIndicators.calculate_macd(daily_df['close'])
        daily_df['RSI'] = TechnicalIndicators.calculate_rsi(daily_df['close'])
        daily_df['ADX'], daily_df['+DI'], daily_df['-DI'] = \
            TechnicalIndicators.calculate_adx(daily_df['high'], daily_df['low'], daily_df['close'])
        
        # Fetch intraday 15min data (used for RSI, MACD, ADX)
        intraday_df = api.get_hybrid_history(symbol, exchange, instrument_token, "15minute", days=10)
        if intraday_df is None or len(intraday_df) < 50:
            logger.error(f"Insufficient intraday data for {symbol}")
            return None, None, None, None
        
        # CREATE LIVE FORMING CANDLE for real-time indicators
        # This makes RSI/ADX/MACD update every second!
        import pytz
        
        ist = pytz.timezone("Asia/Kolkata")
        current_time = now_ist()
        
        # ALIGN TO 15-MINUTE BAR START (Standardizes indicator calculation)
        bar_start = current_time.replace(minute=current_time.minute - current_time.minute % 15, second=0, microsecond=0)
        
        if current_spot > 0:
            # Use current spot price as close, last candle's close as open
            last_close = intraday_df.iloc[-1]['close']
            
            # Use last candle's high/low if current spot is within that range, 
            # otherwise expand to current spot
            
            # Build live candle
            live_candle = pd.DataFrame({
                'open': [last_close],
                'high': [max(last_close, current_spot)],
                'low': [min(last_close, current_spot)],
                'close': [current_spot]
            }, index=[bar_start])
            
            # Append live candle to historical data
            intraday_df_live = pd.concat([intraday_df, live_candle])
        else:
            intraday_df_live = intraday_df
            if current_spot == 0:
                current_spot = intraday_df.iloc[-1]['close']
        
        # Calculate intraday indicators WITH LIVE CANDLE - updates in real-time!
        intraday_df_live['MACD'], intraday_df_live['MACD_Signal'], intraday_df_live['MACD_Hist'] = \
            TechnicalIndicators.calculate_macd(intraday_df_live['close'])
        intraday_df_live['RSI'] = TechnicalIndicators.calculate_rsi(intraday_df_live['close'])
        intraday_df_live['ADX'], intraday_df_live['+DI'], intraday_df_live['-DI'] = \
            TechnicalIndicators.calculate_adx(intraday_df_live['high'], intraday_df_live['low'], intraday_df_live['close'])
        
        # Fetch VIX with robust fallback
        try:
            vix_quote = api.get_quote("INDIA VIX", "NSE")
            current_vix = vix_quote.get('last_price', 15.0) if vix_quote else 15.0
        except Exception as e:
            logger.warning(f"Failed to fetch India VIX: {e}. Using default 15.0")
            current_vix = 15.0
            
        if current_vix <= 0:
            current_vix = 15.0
        
        # Return the live dataframe with real-time indicators
        return daily_df, intraday_df_live, current_spot, current_vix
    except Exception as e:
        logger.error(f"Error fetching market data: {e}")
        return None, None, None, None


def exit_monitoring_loop(api: MStockAPI, bot: FnOTradingBot, order_manager: OrderManager, symbols_config: dict):
    """
    REAL-TIME EXIT MONITORING
    Runs every 1 second to check SL and Profit targets
    """
    logger.info("EXIT MONITORING THREAD STARTED (1-second checks)")
    
    # Track consecutive bad ticks for safety exits
    safety_counts = {} # {position_id: count}
    
    while not shutdown_event.is_set():
        try:
            # Check if market closed
            current_time = now_ist().time()
            if current_time > config.market_close:
                logger.info("EXIT THREAD: Market closed")
                break
            
            # Check each active position
            with bot.lock:
                underlyings = list(bot.positions.keys())
                
            for underlying in underlyings:
                with bot.lock:
                    if underlying not in bot.positions:
                        continue
                    position = bot.positions[underlying]
                
                # Get symbol info from config (reverse lookup or use position's underlying)
                symbol_info = None
                for sym_name, info in symbols_config.items():
                    if info[2] == underlying:
                        symbol_info = (sym_name, info[0], info[1])
                        break
                
                if not symbol_info:
                    # Fallback for imported positions
                    symbol_map = {
                        "NIFTY50": "NIFTY 50",
                        "BANKNIFTY": "NIFTY BANK",
                        "NIFTYBANK": "NIFTY BANK",
                        "FINNIFTY": "NIFTY FIN SERVICE",
                        "NIFTYFINSERVICE": "NIFTY FIN SERVICE",
                        "SENSEX": "SENSEX"
                    }
                    symbol = symbol_map.get(underlying, underlying)
                    exchange, instrument_token = symbols_config.get(symbol, ("NSE", "", underlying))[:2]
                else:
                    symbol, exchange, instrument_token = symbol_info
                
                # Get current spot price (FAST - just spot price)
                quote = api.get_quote(symbol, exchange)
                if not quote:
                    continue
                    
                current_spot = quote.get('last_price', 0)
                if current_spot == 0:
                    continue
                
                # CRITICAL: We need the OPTION PREMIUM to check Safety Net
                current_premium = 0.0
                if position.option_symbol:
                    # Determine correct exchange: BFO for SENSEX, NFO for others
                    opt_exchange = "BFO" if underlying == "SENSEX" else "NFO"
                    opt_quote = api.get_quote(position.option_symbol, opt_exchange)
                    if opt_quote:
                        current_premium = opt_quote.get('last_price', 0.0)
                
                # LOGGING: Added tracking logs for visibility
                if current_premium > 0:
                     pnl = position.calculate_pnl(current_premium)
                     logger.info(f"MONITORING {underlying}: Spot={current_spot:.2f}, LTP={current_premium:.2f}, P&L=Rs {pnl:.2f}")
                else:
                     logger.warning(f"MONITORING {underlying}: Blind (Failed to fetch quote for {position.option_symbol})")
                     # REMOVED DANGEROUS FALLBACK - current_premium stays 0.0
                
                # SIMPLIFIED EXIT CHECK FOR MAIN LOOP (Safety + SL + TP):
                if current_premium > 0:
                    # 1. Safety Net (Max Loss)
                    pnl_pct = position.calculate_pnl_pct(current_premium)
                    max_loss = config.max_premium_loss_percent
                    
                    exit_reason = None
                    
                    pos_id = position.position_id
                    if pnl_pct <= max_loss:
                        safety_counts[pos_id] = safety_counts.get(pos_id, 0) + 1
                        logger.warning(f"SAFETY CHECK {underlying}: Premium P&L ({pnl_pct:.2f}%) <= {max_loss}% (Count: {safety_counts[pos_id]}/3)")
                        
                        if safety_counts[pos_id] >= 3:
                            logger.error(f"!!! SAFETY EXIT TRIGGERED !!!: -50% loss confirmed for 3 ticks")
                            exit_reason = ExitReason.STOP_LOSS
                    else:
                        if pos_id in safety_counts:
                            logger.info(f"SAFETY RESET {underlying}: Premium recovered to {pnl_pct:.2f}%")
                            del safety_counts[pos_id]
                    
                        # 2. Stop Loss (Spot based)
                        if position.check_sl_hit(current_spot):
                            logger.warning(f"EXIT THREAD: STOP LOSS HIT for {underlying}")
                            exit_reason = ExitReason.STOP_LOSS
                            
                        # 3. Profit Target (HARDCODED: Rs 250.0)
                        elif position.check_profit_hit(current_premium, 250.0):
                            logger.info(f"EXIT THREAD: PROFIT TARGET HIT for {underlying}")
                            exit_reason = ExitReason.PROFIT_TARGET
                
                # EXECUTE EXIT
                if exit_reason:
                    logger.info(f"LIVE MODE: Placing EXIT order for {position.position_id} | Reason: {exit_reason}")
                    
                    if config.live_trading:
                        exit_symbol = position.option_symbol
                        if exit_symbol:
                            # Exchange logic: SENSEX options are on BFO, others NFO? 
                            # MStock usually NFO for NSE, BFO for BSE.
                            # position.option_symbol should be correct from sync.
                            
                            # Determine exchange based on underlying or symbol
                            exit_exchange = "BFO" if "SENSEX" in underlying else "NFO" 
                            
                            order_manager.place_order(
                                api=api,
                                symbol=exit_symbol,
                                underlying=underlying,
                                strike=position.strike_price,
                                option_type=position.trade_type.value,
                                qty=position.lot_size,
                                side='SELL',
                                exchange=exit_exchange
                            )
                        else:
                            logger.error(f"Cannot exit {underlying}: Missing option_symbol")

                    bot.exit_trade(underlying, current_premium, current_spot, exit_reason)
                    continue
            
            # Sleep 1 second before next check
            time.sleep(1)
            
        except Exception as e:
            logger.error(f"EXIT THREAD ERROR: {e}")
            time.sleep(1)
    
    logger.info("EXIT MONITORING THREAD STOPPED")


def entry_monitoring_loop(api: MStockAPI, bot: FnOTradingBot, order_manager: OrderManager, symbols_config: dict):
    """
    ENTRY MONITORING (1-second real-time checks)
    Checks entry conditions and MACD reversals continuously
    """
    logger.info("ENTRY MONITORING THREAD STARTED (1-second real-time checks)")
    
    iteration = 0
    
    while not shutdown_event.is_set():
        try:
            # Check if market closed
            current_time = now_ist().time()
            if current_time > config.market_close:
                logger.info("ENTRY THREAD: Market closed")
                break
            
            # Check if within order placement window (9:15 AM - 3:25 PM)
            from datetime import time as dtime
            order_start = dtime(9, 15)  # 9:15 AM
            
            iteration += 1
            logger.info(f"\n{'='*60}")
            logger.info(f"ENTRY CHECK #{iteration} | Time: {now_ist().strftime('%H:%M:%S')}")
            logger.info(f"{'='*60}")
            
            # Process each symbol
            for symbol, (exchange, instrument_token, underlying) in symbols_config.items():
                
                logger.info(f"\nProcessing {underlying}...")
                
                # Get market data with indicators
                daily_df, intraday_df, current_spot, current_vix = get_market_data_with_indicators(
                    api, symbol, exchange, instrument_token
                )
                
                if daily_df is None or intraday_df is None:
                    logger.warning(f"Skipping {underlying} due to data issues")
                    continue
                
                current_row_idx = len(intraday_df) - 1
                logger.info(f"  Spot: Rs {current_spot:,.2f} | VIX: {current_vix:.2f}")
                
                
                # Check MACD reversal for active positions (needs new 15-min candle)
                if underlying in bot.positions:
                    position = bot.positions[underlying]
                    # Try to fetch actual option premium for accuracy
                    current_premium = 0.0
                    if position.option_symbol:
                        opt_exchange = "BFO" if underlying == "SENSEX" else "NFO"
                        opt_quote = api.get_quote(position.option_symbol, opt_exchange)
                        if opt_quote:
                            current_premium = opt_quote.get('last_price', 0.0)
                    
                    if current_premium == 0:
                        logger.warning(f"MACD CHECK {underlying}: Blind (Failed to fetch quote for {position.option_symbol})")
                        
                    current_profit_pct = position.calculate_pnl_pct(current_premium)
                    current_pnl = position.calculate_pnl(current_premium)
                    
                    # Only check reversal if profit < target amount (HARDCODED: 250.0)
                    if current_pnl < 250.0:
                        # Check for MACD reversal on CONFIRMED CANDLE ONLY
                        check_idx = current_row_idx - 1
                        
                        with bot.lock:
                            # Re-verify position still exists within lock
                            if underlying not in bot.positions:
                                continue
                            position = bot.positions[underlying]
                            
                        if position.trade_type == TradeType.CE:
                            # CALL REVERSAL: MACD Bearish OR DI Bearish (+DI < -DI)
                            macd_rev = (check_idx > 0 and TechnicalIndicators.check_macd_crossover_bearish(
                                intraday_df['MACD'],
                                intraday_df['MACD_Signal'],
                                check_idx
                            ))
                            di_rev = (check_idx > 0 and TechnicalIndicators.check_di_crossover_bearish(
                                intraday_df['+DI'],
                                intraday_df['-DI'],
                                check_idx
                            ))

                            if macd_rev or di_rev:
                                reason = "MACD" if macd_rev else "DI"
                                logger.info(f"ENTRY THREAD: {reason} REVERSAL (Confirmed) for {underlying}")
                                
                                if config.live_trading:
                                    logger.info(f"LIVE MODE: Placing SELL order ({reason}) for {position.position_id}")
                                    
                                    exit_symbol = position.option_symbol
                                    if exit_symbol:
                                        exit_exchange = "BFO" if underlying == "SENSEX" else "NFO"
                                        order_manager.place_order(
                                            api=api,
                                            symbol=exit_symbol,
                                            underlying=underlying,
                                            strike=position.strike_price,
                                            option_type=position.trade_type.value,
                                            qty=position.lot_size,
                                            side='SELL',
                                            exchange=exit_exchange
                                        )
                                
                                bot.exit_trade(underlying, current_premium, current_spot, ExitReason.MACD_REVERSAL)
                        else:  # PE
                            # PUT REVERSAL: MACD Bullish OR DI Bullish (+DI > -DI)
                            macd_rev = (check_idx > 0 and TechnicalIndicators.check_macd_crossover_bullish(
                                intraday_df['MACD'],
                                intraday_df['MACD_Signal'],
                                check_idx
                            ))
                            di_rev = (check_idx > 0 and TechnicalIndicators.check_di_crossover_bullish(
                                intraday_df['+DI'],
                                intraday_df['-DI'],
                                check_idx
                            ))
                            
                            if macd_rev or di_rev:
                                reason = "MACD" if macd_rev else "DI"
                                logger.info(f"ENTRY THREAD: {reason} REVERSAL (Confirmed) for {underlying}")
                                
                                if config.live_trading:
                                    logger.info(f"LIVE MODE: Placing SELL order ({reason}) for {position.position_id}")
                                    
                                    exit_symbol = position.option_symbol
                                    if exit_symbol:
                                        exit_exchange = "BFO" if underlying == "SENSEX" else "NFO"
                                        order_manager.place_order(
                                            api=api,
                                            symbol=exit_symbol,
                                            underlying=underlying,
                                            strike=position.strike_price,
                                            option_type=position.trade_type.value,
                                            qty=position.lot_size,
                                            side='SELL',
                                            exchange=exit_exchange
                                        )
                                
                                bot.exit_trade(underlying, current_premium, current_spot, ExitReason.MACD_REVERSAL)
                
                # Check entry conditions (only if no position)
                if underlying not in bot.positions:
                    trade_type = None
                    
                    # Check CE entry
                    if bot.check_entry_conditions_ce(underlying, daily_df, intraday_df, current_row_idx, current_vix):
                        logger.info(f"Entry signal detected for {underlying} CE")
                        trade_type = TradeType.CE
                    
                    # Check PE entry
                    elif bot.check_entry_conditions_pe(underlying, daily_df, intraday_df, current_row_idx, current_vix):
                        logger.info(f"Entry signal detected for {underlying} PE")
                        trade_type = TradeType.PE
                    
                    if trade_type:
                        # Select option contract
                        strike, option_symbol = OptionSelector.select_option(
                            underlying, 
                            current_spot, 
                            trade_type.value,
                            depth=config.strike_depth
                        )
                        logger.info(f"  Selected option: {option_symbol}")
                        
                        # Get option premium (initial estimate for logging entry)
                        current_premium = 0.0
                        opt_exchange = "BFO" if underlying == "SENSEX" else "NFO"
                        opt_quote = api.get_quote(option_symbol, opt_exchange)
                        if opt_quote:
                            current_premium = opt_quote.get('last_price', 0.0)
                        
                        if current_premium == 0:
                             current_premium = current_spot * 0.015 # Safe only for initial logging estimate
                        
                        # Get instrument token for the symbol
                        token = SymbolMaster().get_token(option_symbol)
                        if not token:
                            logger.warning(f"Token not found for {option_symbol}")
                            token = "" # Try anyway? Or fail? Better try with empty.
                        
                        # Determine exchange: BFO for SENSEX, NFO for others
                        exchange = "BFO" if underlying == "SENSEX" else "NFO"

                        if config.live_trading:
                            # Place LIVE order
                            logger.info(f"LIVE MODE: Placing BUY order for {option_symbol} (Token: {token}, Exchange: {exchange})")
                            order_result = order_manager.place_order(
                                api=api,
                                symbol=option_symbol,
                                underlying=underlying,
                                strike=strike,
                                option_type=trade_type.value,
                                qty=config.get_lot_size(underlying) * config.default_num_lots,
                                side='BUY',
                                token=token,
                                exchange=exchange
                            )
                            
                            if order_result.status.value == 'PLACED':
                                from src.utils import Colors
                                logger.info(Colors.bold_green(f"[TRADE ENTERED] {underlying} {trade_type.value} @ Strike {strike}"))
                                bot.enter_trade(
                                    underlying, 
                                    trade_type, 
                                    current_premium, 
                                    current_spot, 
                                    current_vix, 
                                    current_row_idx,
                                    option_symbol=option_symbol,
                                    strike_price=strike
                                )
                            else:
                                logger.warning(f"Order REJECTED: {order_result.rejection_reason}")
                        else:
                            # Paper trading mode
                            logger.info(f"PAPER MODE: Simulating BUY for {option_symbol}")
                            bot.enter_trade(
                                underlying, 
                                trade_type, 
                                current_premium, 
                                current_spot, 
                                current_vix, 
                                current_row_idx,
                                option_symbol=option_symbol,
                                strike_price=strike
                            )
                    else:
                        # No entry conditions met - the detailed reasons are already logged
                        # by check_entry_conditions_ce/pe functions
                        pass
            
            # Print current status (only every 10 iterations to reduce log spam)
            if iteration % 10 == 0:
                summary = bot.get_account_summary()
                logger.info(f"\nActive Positions: {summary['open_positions']}")
                logger.info(f"Daily P&L: Rs {summary['daily_pnl']:+,.2f}")
            
            # Wait 1 second before next check
            time.sleep(1)
            
        except Exception as e:
            import traceback
            logger.error(f"ENTRY THREAD ERROR: {e}")
            logger.error(traceback.format_exc())
            time.sleep(60)
    
    logger.info("ENTRY MONITORING THREAD STOPPED")


def run_live_trading(symbols_config: dict):
    """
    Run LIVE trading with dual-speed monitoring
    """
    mode = "LIVE TRADING" if config.live_trading else "PAPER TRADING"
    
    # Print the "Top 1%" Futuristic UI Startup
    print_holographic_banner()
    
    logger.info(f"[bold cyan]INITIALIZING {mode} SESSION...[/bold cyan]")
    logger.info(f"Capital: [bold green]Rs {config.initial_capital:,.2f}[/bold green] | Mode: [bold yellow]{'LIVE' if config.live_trading else 'PAPER'}[/bold yellow]")
    logger.info(f"Daily Loss Limit: [bold red]{config.daily_loss_limit_pct}%[/bold red]")
    logger.info("[dim]--------------------------------------------------[/dim]")
    logger.info("MONITORING STRATEGY:")
    logger.info("  Entry Checks: Every 1 second (REAL-TIME)")
    logger.info("  Exit Checks: Every 1 second (REAL-TIME)")
    logger.info("="*60)
    
    # Initialize API, bot, and order manager
    api = MStockAPI()
    bot = FnOTradingBot(config)
    order_manager = OrderManager()
    
    # Sync any existing positions from broker
    logger.info("Checking for existing positions in broker account...")
    synced_count = sync_positions_from_broker(bot, api)
    if synced_count > 0:
        logger.info(f"Imported {synced_count} existing position(s) for monitoring")
    
    # Wait for market to open
    wait_for_market_open()
    
    try:
        # Start both monitoring threads
        entry_thread = threading.Thread(
            target=entry_monitoring_loop,
            args=(api, bot, order_manager, symbols_config),
            name="EntryMonitor"
        )
        
        exit_thread = threading.Thread(
            target=exit_monitoring_loop,
            args=(api, bot, order_manager, symbols_config),
            name="ExitMonitor"
        )
        
        entry_thread.start()
        exit_thread.start()
        
        logger.info("\nBoth monitoring threads started!")
        logger.info("Press Ctrl+C to stop...\n")
        
        # Wait for threads
        entry_thread.join()
        exit_thread.join()
        
    except KeyboardInterrupt:
        logger.info("\nShutdown signal received...")
        shutdown_event.set()
        
    finally:
        # Final summary
        logger.info("\n" + "="*60)
        logger.info(f"{mode} SESSION COMPLETE")
        logger.info("="*60)
        bot.print_account_summary()
        
        # Save trades
        suffix = "live" if config.live_trading else "paper"
        output_file = f"logs/{suffix}_trades_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
        bot.save_trades_to_csv(output_file)


def load_symbols_from_config():
    """Load trading symbols from config.json"""
    try:
        with open('config.json', 'r') as f:
            cfg = json.load(f)
        
        symbols = {}
        if 'symbols' in cfg:
            # New config format with symbols section
            for symbol_name, symbol_data in cfg['symbols'].items():
                if symbol_name == 'comment':
                    continue
                # Each symbol entry: (exchange, token, underlying_key)
                symbols[symbol_name] = (
                    symbol_data['exchange'], 
                    symbol_data['token'],
                    symbol_data.get('key', symbol_name.replace(" ", ""))
                )
        else:
            # Fallback to old hard-coded format
            logger.warning("Old config format detected, using hard-coded symbols")
            symbols = {
                "NIFTY 50": ("NSE", "26000", "NIFTY50"),
                "NIFTY BANK": ("NSE", "26009", "BANKNIFTY")
            }
        
        logger.info(f"Loaded {len(symbols)} symbols from config: {list(symbols.keys())}")
        return symbols
    except Exception as e:
        logger.error(f"Error loading symbols from config: {e}")
        # Fallback to default
        return {
            "NIFTY 50": ("NSE", "26000", "NIFTY50"),
            "NIFTY BANK": ("NSE", "26009", "BANKNIFTY")
        }


if __name__ == "__main__":
    # Load symbols from config file
    symbols_config = load_symbols_from_config()
    
    # Run trading based on config
    run_live_trading(symbols_config)
