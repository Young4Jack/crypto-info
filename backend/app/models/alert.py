"""价格预警模型"""
from sqlalchemy import Column, Integer, String, Float, Boolean, DateTime, ForeignKey, Enum
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
import enum
from app.database import Base

class AlertType(enum.Enum):
    """预警类型枚举"""
    ABOVE = "above"  # 价格高于阈值
    BELOW = "below"  # 价格低于阈值

class PriceAlert(Base):
    """价格预警规则表"""
    __tablename__ = "price_alerts"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    crypto_id = Column(Integer, ForeignKey("cryptocurrencies.id"), nullable=False)
    alert_type = Column(Enum(AlertType), nullable=False)
    threshold_price = Column(Float, nullable=False)
    webhook_url = Column(String(500), nullable=True)
    is_active = Column(Boolean, default=True)
    triggered_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # 关系
    user = relationship("User", back_populates="alerts")
    cryptocurrency = relationship("Cryptocurrency", back_populates="alerts")
    histories = relationship("AlertHistory", back_populates="alert")
