"""系统设置模型"""
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Boolean
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.database import Base

class NotificationSetting(Base):
    """通知设置表"""
    __tablename__ = "notification_settings"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, unique=True)
    api_url = Column(String(500), nullable=True, comment="推送API地址")
    auth_token = Column(String(500), nullable=True, comment="鉴权Token")
    channel = Column(String(50), default="email", comment="推送渠道")
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    # 关系
    user = relationship("User", backref="notification_setting")

class SystemSetting(Base):
    """系统设置表"""
    __tablename__ = "system_settings"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, unique=True)
    refresh_interval = Column(Integer, default=5, comment="价格刷新间隔（秒）")
    enable_captcha = Column(Boolean, default=False, comment="是否启用登录验证码")
    site_title = Column(String(100), default="Crypto-info", comment="网站标题")
    site_description = Column(String(500), default="数字货币价格监控和预警系统", comment="网站描述")
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    # 关系
    user = relationship("User", backref="system_setting")
