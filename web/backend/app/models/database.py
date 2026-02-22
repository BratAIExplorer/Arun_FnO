"""
Database models for F&O Trading Web Platform
"""
from sqlalchemy import create_engine, Column, Integer, String, Boolean, Float, DateTime, Text, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
from datetime import datetime
import os

DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./data/trading.db")

# Handle PostgreSQL URL prefix for SQLAlchemy
if DATABASE_URL.startswith("postgres://"):
    DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)

engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False} if "sqlite" in DATABASE_URL else {}
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    full_name = Column(String, default="")
    is_active = Column(Boolean, default=True)
    is_admin = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    # Email confirmation
    email_confirmed = Column(Boolean, default=False)
    confirmation_token = Column(String, nullable=True)
    
    # Password reset
    reset_token = Column(String, nullable=True)
    reset_token_expiry = Column(DateTime, nullable=True)

    settings = relationship("UserSettings", back_populates="user", uselist=False, cascade="all, delete-orphan")
    trades = relationship("TradeRecord", back_populates="user", cascade="all, delete-orphan")


class UserSettings(Base):
    """All strategy settings, credentials, and notification config per user"""
    __tablename__ = "user_settings"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), unique=True, nullable=False)

    # mStock Credentials (encrypted)
    mstock_api_key_enc = Column(Text, default="")
    mstock_api_secret_enc = Column(Text, default="")
    mstock_client_code_enc = Column(Text, default="")
    mstock_password_enc = Column(Text, default="")
    mstock_access_token_enc = Column(Text, default="")
    mstock_token_expiry = Column(DateTime, nullable=True)

    # Trading Mode
    trading_mode = Column(String, default="PAPER")  # PAPER or LIVE

    # Capital & Risk
    initial_capital = Column(Float, default=100000.0)
    daily_loss_limit_pct = Column(Float, default=5.0)
    daily_profit_cap = Column(Float, default=1200.0)

    # Strategy Conditions
    rsi_min = Column(Float, default=30.0)
    rsi_max = Column(Float, default=65.0)
    adx_min_daily = Column(Float, default=25.0)
    vix_min_threshold = Column(Float, default=10.0)
    profit_target_amount = Column(Float, default=250.0)
    strike_depth = Column(Integer, default=0)  # 0=ATM, 1=ITM1, 2=ITM2

    # Trading Hours
    market_open_time = Column(String, default="09:15")
    entry_cutoff_time = Column(String, default="15:15")

    # Stop Loss per index (base VIX band 12-15)
    nifty_sl_low = Column(Float, default=0.70)
    nifty_sl_mid = Column(Float, default=0.75)
    nifty_sl_high = Column(Float, default=0.80)
    banknifty_sl_low = Column(Float, default=1.20)
    banknifty_sl_mid = Column(Float, default=1.25)
    banknifty_sl_high = Column(Float, default=1.50)
    finnifty_sl_low = Column(Float, default=1.00)
    finnifty_sl_mid = Column(Float, default=1.25)
    finnifty_sl_high = Column(Float, default=1.50)
    sensex_sl_low = Column(Float, default=1.00)
    sensex_sl_mid = Column(Float, default=1.25)
    sensex_sl_high = Column(Float, default=1.50)

    # Lot Sizes
    nifty_lots = Column(Integer, default=1)
    banknifty_lots = Column(Integer, default=1)
    finnifty_lots = Column(Integer, default=1)
    sensex_lots = Column(Integer, default=1)

    # Active Indices
    trade_nifty = Column(Boolean, default=True)
    trade_banknifty = Column(Boolean, default=True)
    trade_finnifty = Column(Boolean, default=False)
    trade_sensex = Column(Boolean, default=False)

    # Notifications
    email_enabled = Column(Boolean, default=False)
    email_address = Column(String, default="")
    email_smtp_host = Column(String, default="smtp.gmail.com")
    email_smtp_port = Column(Integer, default=587)
    email_smtp_user_enc = Column(Text, default="")
    email_smtp_pass_enc = Column(Text, default="")

    telegram_enabled = Column(Boolean, default=False)
    telegram_bot_token_enc = Column(Text, default="")
    telegram_chat_id = Column(String, default="")

    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    user = relationship("User", back_populates="settings")


class TradeRecord(Base):
    """Persisted trade history per user"""
    __tablename__ = "trade_records"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)

    position_id = Column(String, index=True)  # From broker/mStock
    underlying = Column(String)               # NIFTY, BANKNIFTY, etc.
    trade_type = Column(String)               # CE or PE
    option_symbol = Column(String, nullable=True)
    strike_price = Column(Float, nullable=True)
    trading_mode = Column(String, default="PAPER") # PAPER or LIVE

    # Entry data
    entry_time = Column(DateTime)
    entry_price = Column(Float)
    entry_spot = Column(Float)
    lot_size = Column(Integer)
    vix_at_entry = Column(Float)
    
    # Technical Indicators at Entry (for Deep Analysis)
    rsi_at_entry = Column(Float, nullable=True)
    adx_at_entry = Column(Float, nullable=True)
    macd_at_entry = Column(Float, nullable=True)
    macd_signal_at_entry = Column(Float, nullable=True)
    supertrend_at_entry = Column(Float, nullable=True)
    
    # Capture all 8 trade signals as a JSON string
    signals_json = Column(Text, nullable=True) 

    # Exit data
    exit_time = Column(DateTime, nullable=True)
    exit_price = Column(Float, nullable=True)
    exit_spot = Column(Float, nullable=True)
    exit_reason = Column(String, nullable=True) # Target, SL, Time, Manual
    sl_percentage = Column(Float)
    
    # Financials
    pnl = Column(Float, nullable=True)
    pnl_percentage = Column(Float, nullable=True)
    charges = Column(Float, default=0.0)

    created_at = Column(DateTime, default=datetime.utcnow)

    user = relationship("User", back_populates="trades")


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def create_tables():
    os.makedirs("data", exist_ok=True)
    Base.metadata.create_all(bind=engine)
