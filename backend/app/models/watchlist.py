"""关注列表模型"""
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Boolean
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.database import Base

class Watchlist(Base):
    """关注列表表"""
    __tablename__ = "watchlist"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    crypto_id = Column(Integer, ForeignKey("cryptocurrencies.id"), nullable=False)
    notes = Column(String(500), nullable=True)
    sort_order = Column(Integer, default=0, index=True)
    is_public = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # 关系
    user = relationship("User", back_populates="watchlist")
    cryptocurrency = relationship("Cryptocurrency", back_populates="watchlist")