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
    AMPLITUDE = "amplitude"  # 振幅预警
    PERCENT_UP = "percent_up"  # 单向涨幅百分比
    PERCENT_DOWN = "percent_down"  # 单向跌幅百分比

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
    sort_order = Column(Integer, default=0, index=True)
    triggered_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # 新增字段
    base_price = Column(Float, nullable=True, comment="创建预警时的基础价格")
    threshold_value = Column(Float, nullable=True, comment="设定的阈值或百分比数值")
    is_continuous = Column(Boolean, default=False, comment="是否为持续预警模式")
    interval_minutes = Column(Integer, default=5, comment="两次通知之间的间隔时间(分钟)")
    max_notifications = Column(Integer, default=1, comment="最大通知次数限制")
    notified_count = Column(Integer, default=0, comment="已通知次数")
    last_triggered_at = Column(DateTime(timezone=True), nullable=True, comment="上次触发/通知的时间")
    notification_channel = Column(String(100), nullable=True, comment="通知渠道名称")
    notification_group = Column(String(100), nullable=True, comment="通知频道名称")
    
    # 关系
    user = relationship("User", back_populates="alerts")
    cryptocurrency = relationship("Cryptocurrency", back_populates="alerts")
    histories = relationship("AlertHistory", back_populates="alert")
