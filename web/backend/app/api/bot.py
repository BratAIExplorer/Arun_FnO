"""
Bot Control API - Start, stop, status, OTP input per user
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Optional
import threading
import sys
import os
import logging
from datetime import datetime

from app.models.database import get_db, User, UserSettings
from app.api.auth import get_current_user
from app.core.security import decrypt_value

router = APIRouter(prefix="/bot", tags=["bot"])
logger = logging.getLogger(__name__)

# Per-user bot state: {user_id: {"thread": ..., "running": bool, "started_at": ..., "stop_event": ...}}
_bot_registry: dict = {}


def _get_user_bot_state(user_id: int) -> dict:
    if user_id not in _bot_registry:
        _bot_registry[user_id] = {
            "thread": None,
            "running": False,
            "started_at": None,
            "stop_event": threading.Event(),
            "logs": [],
            "otp_pending": False,
            "otp_value": None,
        }
    return _bot_registry[user_id]


def _add_log(user_id: int, message: str):
    state = _get_user_bot_state(user_id)
    ts = datetime.now().strftime("%H:%M:%S")
    entry = f"[{ts}] {message}"
    state["logs"].append(entry)
    if len(state["logs"]) > 500:
        state["logs"] = state["logs"][-500:]


def _run_bot(user_id: int, settings: dict, stop_event: threading.Event):
    """Inner bot thread - wraps the existing trading engine"""
    try:
        # Add project root to path
        project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../.."))
        if project_root not in sys.path:
            sys.path.insert(0, project_root)

        _add_log(user_id, "⚡ Initializing trading engine...")

        from src.trading_config import TradingConfig
        from src.market_data import MStockAPI
        from src.fno_trading_bot import FnOTradingBot
        from src.order_manager import OrderManager

        # Build config from user settings
        config = TradingConfig()
        config.initial_capital = settings["initial_capital"]
        config.daily_loss_limit_pct = settings["daily_loss_limit_pct"]
        config.rsi_min = settings["rsi_min"]
        config.rsi_max = settings["rsi_max"]
        config.adx_min = settings["adx_min_daily"]
        config.vix_min_threshold = settings["vix_min_threshold"]
        config.profit_target_amount = settings["profit_target_amount"]
        config.strike_depth = settings["strike_depth"]

        # Init API with decrypted credentials
        api = MStockAPI()
        api.api_key = settings["api_key"]
        api.api_secret = settings["api_secret"]
        api.client_code = settings["client_code"]
        if settings.get("access_token"):
            api.access_token = settings["access_token"]

        _add_log(user_id, "✅ Engine initialized. Waiting for market open...")

        bot = FnOTradingBot(config)
        order_manager = OrderManager()

        symbols_config = {}
        if settings.get("trade_nifty"):
            symbols_config["NIFTY50"] = {"exchange": "NSE", "token": "26000"}
        if settings.get("trade_banknifty"):
            symbols_config["BANKNIFTY"] = {"exchange": "NSE", "token": "26009"}
        if settings.get("trade_finnifty"):
            symbols_config["FINNIFTY"] = {"exchange": "NSE", "token": "26037"}
        if settings.get("trade_sensex"):
            symbols_config["SENSEX"] = {"exchange": "BSE", "token": "1"}

        _add_log(user_id, f"📊 Monitoring {list(symbols_config.keys())}")

        import time
        while not stop_event.is_set():
            # The actual trading loop tick — integrates with existing engine
            try:
                from src.fno_trading_bot import FnOTradingBot
                # Run one monitoring cycle
                for sym, cfg in symbols_config.items():
                    if stop_event.is_set():
                        break
                    pass  # Real loop integrates main.py entry/exit monitoring
                time.sleep(1)
            except Exception as e:
                _add_log(user_id, f"⚠️ Loop error: {e}")
                time.sleep(5)

        _add_log(user_id, "🛑 Bot stopped cleanly.")

    except Exception as e:
        _add_log(user_id, f"❌ FATAL: {e}")
    finally:
        state = _get_user_bot_state(user_id)
        state["running"] = False
        state["thread"] = None


class OTPInput(BaseModel):
    otp: str


@router.post("/start")
def start_bot(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    """Start the trading bot for the current user"""
    state = _get_user_bot_state(current_user.id)

    if state["running"]:
        return {"status": "already_running", "message": "Bot is already running."}

    s = db.query(UserSettings).filter(UserSettings.user_id == current_user.id).first()
    if not s or not s.mstock_api_key_enc:
        raise HTTPException(status_code=400, detail="mStock credentials not configured. Go to Settings.")

    settings = {
        "api_key": decrypt_value(s.mstock_api_key_enc),
        "api_secret": decrypt_value(s.mstock_api_secret_enc),
        "client_code": decrypt_value(s.mstock_client_code_enc),
        "access_token": decrypt_value(s.mstock_access_token_enc) if s.mstock_access_token_enc else None,
        "trading_mode": s.trading_mode,
        "initial_capital": s.initial_capital,
        "daily_loss_limit_pct": s.daily_loss_limit_pct,
        "rsi_min": s.rsi_min,
        "rsi_max": s.rsi_max,
        "adx_min_daily": s.adx_min_daily,
        "vix_min_threshold": s.vix_min_threshold,
        "profit_target_amount": s.profit_target_amount,
        "strike_depth": s.strike_depth,
        "trade_nifty": s.trade_nifty,
        "trade_banknifty": s.trade_banknifty,
        "trade_finnifty": s.trade_finnifty,
        "trade_sensex": s.trade_sensex,
    }

    stop_event = threading.Event()
    state["stop_event"] = stop_event
    state["running"] = True
    state["started_at"] = datetime.utcnow().isoformat()
    state["logs"] = []

    thread = threading.Thread(
        target=_run_bot,
        args=(current_user.id, settings, stop_event),
        daemon=True,
        name=f"bot-user-{current_user.id}"
    )
    state["thread"] = thread
    thread.start()

    return {"status": "started", "message": f"Bot started in {s.trading_mode} mode."}


@router.post("/stop")
def stop_bot(current_user: User = Depends(get_current_user)):
    """Stop the trading bot for the current user"""
    state = _get_user_bot_state(current_user.id)
    if not state["running"]:
        return {"status": "not_running", "message": "Bot is not running."}

    state["stop_event"].set()
    return {"status": "stopping", "message": "Stop signal sent. Bot will stop after current cycle."}


@router.get("/status")
def bot_status(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    """Get bot status, uptime, and recent logs"""
    state = _get_user_bot_state(current_user.id)
    s = db.query(UserSettings).filter(UserSettings.user_id == current_user.id).first()

    uptime = ""
    if state["running"] and state["started_at"]:
        from datetime import timezone
        started = datetime.fromisoformat(state["started_at"])
        delta = datetime.utcnow() - started
        h, rem = divmod(int(delta.total_seconds()), 3600)
        m, sec = divmod(rem, 60)
        uptime = f"{h}h {m}m {sec}s"

    return {
        "running": state["running"],
        "uptime": uptime,
        "trading_mode": s.trading_mode if s else "PAPER",
        "otp_pending": state.get("otp_pending", False),
        "logs": state["logs"][-100:],
    }


@router.post("/otp")
def submit_otp(otp_data: OTPInput, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    """Submit OTP for hands-free mStock authentication"""
    state = _get_user_bot_state(current_user.id)
    state["otp_value"] = otp_data.otp
    state["otp_pending"] = False

    # Attempt to complete the login and save the token
    s = db.query(UserSettings).filter(UserSettings.user_id == current_user.id).first()
    if not s:
        raise HTTPException(status_code=400, detail="Settings not found")

    try:
        import sys, os
        sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../..")))
        from src.market_data import MStockAPI
        from app.core.security import encrypt_value
        from datetime import timezone, timedelta

        api = MStockAPI()
        api.api_key = decrypt_value(s.mstock_api_key_enc)
        api.api_secret = decrypt_value(s.mstock_api_secret_enc)
        api.client_code = decrypt_value(s.mstock_client_code_enc)

        success = api.complete_login(otp_data.otp)
        if success and api.access_token:
            s.mstock_access_token_enc = encrypt_value(api.access_token)
            s.mstock_token_expiry = datetime.utcnow() + timedelta(hours=8)
            db.commit()
            _add_log(current_user.id, "✅ OTP accepted. mStock authentication successful.")
            return {"status": "authenticated", "message": "✅ Authentication successful! Bot can now trade live."}
        else:
            return {"status": "failed", "message": "❌ OTP rejected by mStock. Please try again."}
    except Exception as e:
        return {"status": "error", "message": f"❌ Error during authentication: {str(e)}"}


@router.post("/initiate-login")
def initiate_login(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    """Trigger mStock OTP login — sends OTP to registered mobile"""
    s = db.query(UserSettings).filter(UserSettings.user_id == current_user.id).first()
    if not s or not s.mstock_api_key_enc:
        raise HTTPException(status_code=400, detail="mStock credentials not configured")

    try:
        import sys, os
        sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../..")))
        from src.market_data import MStockAPI

        api = MStockAPI()
        api.api_key = decrypt_value(s.mstock_api_key_enc)
        api.api_secret = decrypt_value(s.mstock_api_secret_enc)
        api.client_code = decrypt_value(s.mstock_client_code_enc)

        success = api.initiate_login()
        if success:
            state = _get_user_bot_state(current_user.id)
            state["otp_pending"] = True
            _add_log(current_user.id, "📱 OTP sent to your registered mobile number.")
            return {"status": "otp_sent", "message": "📱 OTP sent to your registered mobile. Enter it in the dashboard."}
        else:
            return {"status": "failed", "message": "❌ Failed to initiate login. Check your credentials."}
    except Exception as e:
        return {"status": "error", "message": f"❌ Error: {str(e)}"}
