"""币种模型"""
from sqlalchemy import Column, Integer, String, Boolean, DateTime
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.database import Base

class Cryptocurrency(Base):
    """支持的币种表"""
    __tablename__ = "cryptocurrencies"
    
    id = Column(Integer, primary_key=True, index=True)
    symbol = Column(String(20), unique=True, index=True, nullable=False, comment="交易对符号，如BTCUSDT")
    name = Column(String(100), nullable=False, comment="币种名称，如BTC")
    display_name = Column(String(100), nullable=True, comment="显示名称，如Bitcoin")
    logo_url = Column(String(500), nullable=True)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # 关系
    alerts = relationship("PriceAlert", back_populates="cryptocurrency")
    assets = relationship("Asset", back_populates="cryptocurrency")
    watchlist = relationship("Watchlist", back_populates="cryptocurrency")
