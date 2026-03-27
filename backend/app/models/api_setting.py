"""API设置模型"""
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.database import Base

class ApiSetting(Base):
    """API设置表"""
    __tablename__ = "api_settings"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, unique=True)
    primary_api_url = Column(String(500), nullable=True, comment="主API地址")
    backup_api_url = Column(String(500), nullable=True, comment="备用API地址")
    api_key = Column(String(500), nullable=True, comment="API密钥")
    api_secret = Column(String(500), nullable=True, comment="API密钥")
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    # 关系
    user = relationship("User", backref="api_setting")