"""
Settings API - Full in-UI configuration of all strategy conditions and credentials
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Optional

from app.models.database import get_db, User, UserSettings
from app.api.auth import get_current_user
from app.core.security import encrypt_value, decrypt_value

router = APIRouter(prefix="/settings", tags=["settings"])


class SettingsResponse(BaseModel):
    # mStock (masked)
    mstock_api_key_set: bool
    mstock_api_secret_set: bool
    mstock_client_code_set: bool
    mstock_access_token_set: bool

    # Trading mode
    trading_mode: str

    # Capital & Risk
    initial_capital: float
    daily_loss_limit_pct: float
    daily_profit_cap: float

    # Strategy
    rsi_min: float
    rsi_max: float
    adx_min_daily: float
    vix_min_threshold: float
    profit_target_amount: float
    strike_depth: int

    # Hours
    market_open_time: str
    entry_cutoff_time: str

    # Stop Loss bands
    nifty_sl_low: float
    nifty_sl_mid: float
    nifty_sl_high: float
    banknifty_sl_low: float
    banknifty_sl_mid: float
    banknifty_sl_high: float
    finnifty_sl_low: float
    finnifty_sl_mid: float
    finnifty_sl_high: float
    sensex_sl_low: float
    sensex_sl_mid: float
    sensex_sl_high: float

    # Lot sizes
    nifty_lots: int
    banknifty_lots: int
    finnifty_lots: int
    sensex_lots: int

    # Active indices
    trade_nifty: bool
    trade_banknifty: bool
    trade_finnifty: bool
    trade_sensex: bool

    # Notifications
    email_enabled: bool
    email_address: str
    email_smtp_host: str
    email_smtp_port: int
    email_smtp_user_set: bool

    telegram_enabled: bool
    telegram_bot_token_set: bool
    telegram_chat_id: str

    class Config:
        from_attributes = True


class SettingsUpdate(BaseModel):
    # mStock credentials (optional — only set if provided)
    mstock_api_key: Optional[str] = None
    mstock_api_secret: Optional[str] = None
    mstock_client_code: Optional[str] = None
    mstock_password: Optional[str] = None

    # Trading mode
    trading_mode: Optional[str] = None

    # Capital & Risk
    initial_capital: Optional[float] = None
    daily_loss_limit_pct: Optional[float] = None
    daily_profit_cap: Optional[float] = None

    # Strategy
    rsi_min: Optional[float] = None
    rsi_max: Optional[float] = None
    adx_min_daily: Optional[float] = None
    vix_min_threshold: Optional[float] = None
    profit_target_amount: Optional[float] = None
    strike_depth: Optional[int] = None

    # Hours
    market_open_time: Optional[str] = None
    entry_cutoff_time: Optional[str] = None

    # Stop loss bands
    nifty_sl_low: Optional[float] = None
    nifty_sl_mid: Optional[float] = None
    nifty_sl_high: Optional[float] = None
    banknifty_sl_low: Optional[float] = None
    banknifty_sl_mid: Optional[float] = None
    banknifty_sl_high: Optional[float] = None
    finnifty_sl_low: Optional[float] = None
    finnifty_sl_mid: Optional[float] = None
    finnifty_sl_high: Optional[float] = None
    sensex_sl_low: Optional[float] = None
    sensex_sl_mid: Optional[float] = None
    sensex_sl_high: Optional[float] = None

    # Lot sizes
    nifty_lots: Optional[int] = None
    banknifty_lots: Optional[int] = None
    finnifty_lots: Optional[int] = None
    sensex_lots: Optional[int] = None

    # Active indices
    trade_nifty: Optional[bool] = None
    trade_banknifty: Optional[bool] = None
    trade_finnifty: Optional[bool] = None
    trade_sensex: Optional[bool] = None

    # Notifications
    email_enabled: Optional[bool] = None
    email_address: Optional[str] = None
    email_smtp_host: Optional[str] = None
    email_smtp_port: Optional[int] = None
    email_smtp_user: Optional[str] = None
    email_smtp_pass: Optional[str] = None

    telegram_enabled: Optional[bool] = None
    telegram_bot_token: Optional[str] = None
    telegram_chat_id: Optional[str] = None


def _settings_to_response(s: UserSettings) -> dict:
    return {
        "mstock_api_key_set": bool(s.mstock_api_key_enc),
        "mstock_api_secret_set": bool(s.mstock_api_secret_enc),
        "mstock_client_code_set": bool(s.mstock_client_code_enc),
        "mstock_access_token_set": bool(s.mstock_access_token_enc),
        "trading_mode": s.trading_mode,
        "initial_capital": s.initial_capital,
        "daily_loss_limit_pct": s.daily_loss_limit_pct,
        "daily_profit_cap": s.daily_profit_cap,
        "rsi_min": s.rsi_min,
        "rsi_max": s.rsi_max,
        "adx_min_daily": s.adx_min_daily,
        "vix_min_threshold": s.vix_min_threshold,
        "profit_target_amount": s.profit_target_amount,
        "strike_depth": s.strike_depth,
        "market_open_time": s.market_open_time,
        "entry_cutoff_time": s.entry_cutoff_time,
        "nifty_sl_low": s.nifty_sl_low,
        "nifty_sl_mid": s.nifty_sl_mid,
        "nifty_sl_high": s.nifty_sl_high,
        "banknifty_sl_low": s.banknifty_sl_low,
        "banknifty_sl_mid": s.banknifty_sl_mid,
        "banknifty_sl_high": s.banknifty_sl_high,
        "finnifty_sl_low": s.finnifty_sl_low,
        "finnifty_sl_mid": s.finnifty_sl_mid,
        "finnifty_sl_high": s.finnifty_sl_high,
        "sensex_sl_low": s.sensex_sl_low,
        "sensex_sl_mid": s.sensex_sl_mid,
        "sensex_sl_high": s.sensex_sl_high,
        "nifty_lots": s.nifty_lots,
        "banknifty_lots": s.banknifty_lots,
        "finnifty_lots": s.finnifty_lots,
        "sensex_lots": s.sensex_lots,
        "trade_nifty": s.trade_nifty,
        "trade_banknifty": s.trade_banknifty,
        "trade_finnifty": s.trade_finnifty,
        "trade_sensex": s.trade_sensex,
        "email_enabled": s.email_enabled,
        "email_address": s.email_address,
        "email_smtp_host": s.email_smtp_host,
        "email_smtp_port": s.email_smtp_port,
        "email_smtp_user_set": bool(s.email_smtp_user_enc),
        "telegram_enabled": s.telegram_enabled,
        "telegram_bot_token_set": bool(s.telegram_bot_token_enc),
        "telegram_chat_id": s.telegram_chat_id,
    }


@router.get("/")
def get_settings(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    """Get current user's settings (credentials masked)"""
    s = db.query(UserSettings).filter(UserSettings.user_id == current_user.id).first()
    if not s:
        s = UserSettings(user_id=current_user.id)
        db.add(s)
        db.commit()
        db.refresh(s)
    return _settings_to_response(s)


@router.post("/")
def update_settings(
    update: SettingsUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Update user settings — all fields optional, only changed fields updated"""
    s = db.query(UserSettings).filter(UserSettings.user_id == current_user.id).first()
    if not s:
        s = UserSettings(user_id=current_user.id)
        db.add(s)

    # Encrypted credentials
    if update.mstock_api_key is not None:
        s.mstock_api_key_enc = encrypt_value(update.mstock_api_key)
    if update.mstock_api_secret is not None:
        s.mstock_api_secret_enc = encrypt_value(update.mstock_api_secret)
    if update.mstock_client_code is not None:
        s.mstock_client_code_enc = encrypt_value(update.mstock_client_code)
    if update.mstock_password is not None:
        s.mstock_password_enc = encrypt_value(update.mstock_password)
    if update.email_smtp_user is not None:
        s.email_smtp_user_enc = encrypt_value(update.email_smtp_user)
    if update.email_smtp_pass is not None:
        s.email_smtp_pass_enc = encrypt_value(update.email_smtp_pass)
    if update.telegram_bot_token is not None:
        s.telegram_bot_token_enc = encrypt_value(update.telegram_bot_token)

    # All other plain fields — update if provided
    plain_fields = [
        "trading_mode", "initial_capital", "daily_loss_limit_pct", "daily_profit_cap",
        "rsi_min", "rsi_max", "adx_min_daily", "vix_min_threshold", "profit_target_amount",
        "strike_depth", "market_open_time", "entry_cutoff_time",
        "nifty_sl_low", "nifty_sl_mid", "nifty_sl_high",
        "banknifty_sl_low", "banknifty_sl_mid", "banknifty_sl_high",
        "finnifty_sl_low", "finnifty_sl_mid", "finnifty_sl_high",
        "sensex_sl_low", "sensex_sl_mid", "sensex_sl_high",
        "nifty_lots", "banknifty_lots", "finnifty_lots", "sensex_lots",
        "trade_nifty", "trade_banknifty", "trade_finnifty", "trade_sensex",
        "email_enabled", "email_address", "email_smtp_host", "email_smtp_port",
        "telegram_enabled", "telegram_chat_id",
    ]
    for field in plain_fields:
        val = getattr(update, field, None)
        if val is not None:
            setattr(s, field, val)

    db.commit()
    db.refresh(s)
    return {"message": "Settings saved successfully", "settings": _settings_to_response(s)}


@router.post("/test-connection")
def test_mstock_connection(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Test mStock API connection with stored credentials"""
    s = db.query(UserSettings).filter(UserSettings.user_id == current_user.id).first()
    if not s or not s.mstock_api_key_enc:
        raise HTTPException(status_code=400, detail="No mStock credentials configured. Please save credentials first.")

    try:
        import sys, os
        sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../../../.."))
        from src.market_data import MStockAPI

        api = MStockAPI()
        api.api_key = decrypt_value(s.mstock_api_key_enc)
        api.api_secret = decrypt_value(s.mstock_api_secret_enc)
        api.client_code = decrypt_value(s.mstock_client_code_enc)

        if s.mstock_access_token_enc:
            api.access_token = decrypt_value(s.mstock_access_token_enc)
            quote = api.get_quote("NIFTY 50", "NSE")
            if quote:
                return {"status": "connected", "message": "✅ mStock API connected successfully. Token is valid."}

        return {"status": "needs_auth", "message": "⚠️ Credentials found but not authenticated yet. Please trigger mStock login."}
    except Exception as e:
        return {"status": "error", "message": f"❌ Connection failed: {str(e)}"}
