"""预警历史模型"""
from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey, Enum
from sqlalchemy.orm import relationship
import enum
from datetime import datetime
from app.database import Base
from app.config_manager import config_manager

class AlertHistoryStatus(enum.Enum):
    """预警历史状态枚举"""
    TRIGGERED = "triggered"  # 已触发
    NOTIFIED = "notified"    # 已通知
    FAILED = "failed"        # 通知失败

class AlertHistory(Base):
    """预警历史表"""
    __tablename__ = "alert_histories"
    
    id = Column(Integer, primary_key=True, index=True)
    alert_id = Column(Integer, ForeignKey("price_alerts.id"), nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    crypto_id = Column(Integer, ForeignKey("cryptocurrencies.id"), nullable=False)
    alert_type = Column(String(20), nullable=False)  # above/below
    threshold_price = Column(Float, nullable=False)
    trigger_price = Column(Float, nullable=False)  # 触发时的实际价格
    status = Column(Enum(AlertHistoryStatus), default=AlertHistoryStatus.TRIGGERED)
    notification_sent = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(config_manager.get_timezone()))
    
    # 关系
    alert = relationship("PriceAlert", back_populates="histories")
    user = relationship("User")
    cryptocurrency = relationship("Cryptocurrency")