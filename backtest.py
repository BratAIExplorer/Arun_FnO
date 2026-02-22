"""
Backtesting Module for F&O Trading Bot
Test strategy on historical data
"""

import pandas as pd
import logging
from datetime import datetime
from typing import Dict

from src.fno_trading_bot import FnOTradingBot
from src.trading_models import TradeType
from src.indicators import TechnicalIndicators
from src.trading_config import TradingConfig
from src.utils import setup_logging


logger = logging.getLogger(__name__)


def prepare_data_with_indicators(
    daily_data: pd.DataFrame,
    intraday_data: pd.DataFrame,
    config: TradingConfig
) -> tuple:
    """
    Add technical indicators to daily and intraday data
    
    Parameters:
    -----------
    daily_data : pd.DataFrame
        Daily OHLC data
    intraday_data : pd.DataFrame
        15-minute OHLC data
    config : TradingConfig
        Trading configuration
        
    Returns:
    --------
    tuple
        (daily_data_with_indicators, intraday_data_with_indicators)
    """
    # Calculate indicators for daily data
    daily = daily_data.copy()
    daily['MACD'], daily['MACD_Signal'], daily['MACD_Hist'] = \
        TechnicalIndicators.calculate_macd(daily['close'], config.macd_fast, config.macd_slow, config.macd_signal)
    daily['RSI'] = TechnicalIndicators.calculate_rsi(daily['close'], config.rsi_period)
    daily['ADX'], daily['+DI'], daily['-DI'] = \
        TechnicalIndicators.calculate_adx(daily['high'], daily['low'], daily['close'], config.adx_period)
    
    # Calculate indicators for intraday data
    intraday = intraday_data.copy()
    intraday['MACD'], intraday['MACD_Signal'], intraday['MACD_Hist'] = \
        TechnicalIndicators.calculate_macd(intraday['close'], config.macd_fast, config.macd_slow, config.macd_signal)
    intraday['RSI'] = TechnicalIndicators.calculate_rsi(intraday['close'], config.rsi_period)
    intraday['ADX'], intraday['+DI'], intraday['-DI'] = \
        TechnicalIndicators.calculate_adx(intraday['high'], intraday['low'], intraday['close'], config.adx_period)
    
    # Drop NaN values
    daily = daily.dropna()
    intraday = intraday.dropna()
    
    return daily, intraday


def run_backtest(
    daily_data_dict: Dict[str, pd.DataFrame],
    intraday_data_dict: Dict[str, pd.DataFrame],
    vix_data: pd.Series,
    config: TradingConfig,
    output_file: str = "backtest_results.csv"
):
    """
    Run backtest on historical data
    
    Parameters:
    -----------
    daily_data_dict : Dict[str, pd.DataFrame]
        Dictionary mapping underlying to daily OHLC
        Example: {"NIFTY50": daily_nifty, "BANKNIFTY": daily_banknifty}
    intraday_data_dict : Dict[str, pd.DataFrame]
        Dictionary mapping underlying to 15-min OHLC
    vix_data : pd.Series
        VIX data aligned with intraday timestamps
    config : TradingConfig
        Trading configuration
    output_file : str
        Path to save results CSV
    """
    logger.info("="*60)
    logger.info("STARTING BACKTEST")
    logger.info("="*60)
    
    # Initialize bot
    bot = FnOTradingBot(config)
    
    # Prepare data with indicators
    prepared_daily = {}
    prepared_intraday = {}
    
    for underlying in daily_data_dict:
        logger.info(f"Preparing data for {underlying}...")
        daily, intraday = prepare_data_with_indicators(
            daily_data_dict[underlying],
            intraday_data_dict[underlying],
            config
        )
        prepared_daily[underlying] = daily
        prepared_intraday[underlying] = intraday
        logger.info(f"  Daily: {len(daily)} candles | Intraday: {len(intraday)} candles")
    
    # Get common intraday timestamps across all underlyings
    all_timestamps = set(prepared_intraday[list(prepared_intraday.keys())[0]].index)
    for underlying in prepared_intraday:
        all_timestamps &= set(prepared_intraday[underlying].index)
    
    all_timestamps = sorted(list(all_timestamps))
    logger.info(f"\nSimulating {len(all_timestamps)} time periods...")
    
    # Main backtest loop
    for idx, timestamp in enumerate(all_timestamps):
        # Get VIX for this timestamp
        try:
            vix = vix_data.loc[timestamp]
        except KeyError:
            # Use nearest VIX value
            vix = vix_data.asof(timestamp)
            if pd.isna(vix):
                vix = 15.0  # Default VIX
        
        # Process each underlying
        for underlying in prepared_intraday:
            intraday = prepared_intraday[underlying]
            daily = prepared_daily[underlying]
            
            # Get current row index in intraday data
            current_row_idx = intraday.index.get_loc(timestamp)
            current_row = intraday.iloc[current_row_idx]
            
            # Use close price as "premium" for simulation
            # In reality, you'd have actual option premium data
            current_premium_ce = current_row['close'] * 0.015  # Approx 1.5% of spot as premium
            current_premium_pe = current_row['close'] * 0.015
            current_spot = current_row['close']
            
            # Check exits for active positions
            if underlying in bot.positions:
                position = bot.positions[underlying]
                current_premium = current_premium_ce if position.trade_type == TradeType.CE else current_premium_pe
                
                exit_reason = bot.check_exit_conditions(
                    position,
                    current_premium,
                    current_spot,
                    current_row_idx,
                    intraday
                )
                
                if exit_reason:
                    bot.exit_trade(underlying, current_premium, current_spot, exit_reason)
            
            # Check entry conditions (only if no active position)
            if underlying not in bot.positions:
                # Get matching daily candle
                daily_row_date = timestamp.date()
                matching_daily = daily[daily.index.date <= daily_row_date]
                if len(matching_daily) == 0:
                    continue
                daily_subset = matching_daily
                
                # Check CE entry
                if bot.check_entry_conditions_ce(underlying, daily_subset, intraday, current_row_idx, vix):
                    bot.enter_trade(
                        underlying,
                        TradeType.CE,
                        current_premium_ce,
                        current_spot,
                        vix,
                        current_row_idx
                    )
                
                # Check PE entry
                elif bot.check_entry_conditions_pe(underlying, daily_subset, intraday, current_row_idx, vix):
                    bot.enter_trade(
                        underlying,
                        TradeType.PE,
                        current_premium_pe,
                        current_spot,
                        vix,
                        current_row_idx
                    )
        
        # Print progress every 100 iterations
        if (idx + 1) % 100 == 0:
            logger.info(f"  Processed {idx + 1}/{len(all_timestamps)} periods...")
    
    # Force close any remaining positions at end
    logger.info("\nClosing remaining positions...")
    for underlying in list(bot.positions.keys()):
        position = bot.positions[underlying]
        final_premium = intraday_data_dict[underlying].iloc[-1]['close'] * 0.015
        final_spot = intraday_data_dict[underlying].iloc[-1]['close']
        bot.exit_trade(underlying, final_premium, final_spot, bot.ExitReason.EOD_CLOSE)
    
    # Print summary
    logger.info("\n" + "="*60)
    logger.info("BACKTEST COMPLETE")
    logger.info("="*60)
    bot.print_account_summary()
    
    # Save trades to CSV
    bot.save_trades_to_csv(output_file)
    
    return bot


if __name__ == "__main__":
    # Example usage
    setup_logging("logs/backtest.log")
    
    # Load your historical data here
    # This is just an example structure
    print("To run backtest, load your historical data and call:")
    print("  run_backtest(daily_data_dict, intraday_data_dict, vix_data, config)")
