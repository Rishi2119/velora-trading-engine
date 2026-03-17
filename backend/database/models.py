"""
Velora Database Models — SQLAlchemy ORM
"""
from datetime import datetime, timezone
from sqlalchemy import (
    Column, Integer, String, Float, Boolean, DateTime, Text, ForeignKey
)
from sqlalchemy.orm import DeclarativeBase, relationship


def _utcnow():
    return datetime.now(timezone.utc)


class Base(DeclarativeBase):
    pass


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String(255), unique=True, index=True, nullable=False)
    hashed_password = Column(String(255), nullable=False)
    full_name = Column(String(255), nullable=True)
    is_active = Column(Boolean, default=True)
    is_admin = Column(Boolean, default=False)
    created_at = Column(DateTime, default=_utcnow)
    updated_at = Column(DateTime, default=_utcnow, onupdate=_utcnow)

    trades = relationship("Trade", back_populates="user", lazy="select")
    portfolio_snapshots = relationship("PortfolioSnapshot", back_populates="user", lazy="select")


class Trade(Base):
    __tablename__ = "trades"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    trade_id = Column(String(50), unique=True, index=True)
    symbol = Column(String(20), nullable=False)
    direction = Column(String(10), nullable=False)  # BUY / SELL
    strategy = Column(String(100), nullable=True)
    entry_price = Column(Float, nullable=True)
    stop_loss = Column(Float, nullable=True)
    take_profit = Column(Float, nullable=True)
    lots = Column(Float, nullable=True)
    pnl = Column(Float, default=0.0)
    status = Column(String(20), default="OPEN")  # OPEN / CLOSED
    rr_ratio = Column(Float, nullable=True)
    mt5_ticket = Column(Integer, nullable=True)
    comment = Column(String(255), nullable=True)
    opened_at = Column(DateTime, default=_utcnow)
    closed_at = Column(DateTime, nullable=True)

    user = relationship("User", back_populates="trades")


class Strategy(Base):
    __tablename__ = "strategies"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), unique=True, nullable=False)
    display_name = Column(String(200), nullable=True)
    enabled = Column(Boolean, default=True)
    config_json = Column(Text, default="{}")
    description = Column(Text, nullable=True)
    created_at = Column(DateTime, default=_utcnow)
    updated_at = Column(DateTime, default=_utcnow, onupdate=_utcnow)


class PortfolioSnapshot(Base):
    __tablename__ = "portfolio_snapshots"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    balance = Column(Float, nullable=False)
    equity = Column(Float, nullable=False)
    profit = Column(Float, default=0.0)
    currency = Column(String(10), default="USD")
    snapshot_at = Column(DateTime, default=_utcnow)

    user = relationship("User", back_populates="portfolio_snapshots")


class MarketSnapshot(Base):
    __tablename__ = "market_snapshots"

    id = Column(Integer, primary_key=True, index=True)
    symbol = Column(String(20), nullable=False, index=True)
    bid = Column(Float, nullable=True)
    ask = Column(Float, nullable=True)
    spread = Column(Float, nullable=True)
    timestamp = Column(DateTime, default=_utcnow, index=True)


class LogEntry(Base):
    __tablename__ = "log_entries"

    id = Column(Integer, primary_key=True, index=True)
    level = Column(String(20), nullable=False)  # INFO / WARNING / ERROR
    source = Column(String(100), nullable=True)
    message = Column(Text, nullable=False)
    extra_json = Column(Text, nullable=True)
    created_at = Column(DateTime, default=_utcnow, index=True)
