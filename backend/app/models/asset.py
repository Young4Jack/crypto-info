"""资产模型"""
from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey, Text
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.database import Base

class Asset(Base):
    """用户资产记录表"""
    __tablename__ = "assets"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    crypto_id = Column(Integer, ForeignKey("cryptocurrencies.id"), nullable=False)
    buy_price = Column(Float, nullable=False)
    quantity = Column(Float, nullable=False)
    notes = Column(Text, nullable=True)
    sort_order = Column(Integer, default=0, index=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # 关系
    user = relationship("User", back_populates="assets")
    cryptocurrency = relationship("Cryptocurrency", back_populates="assets")