"""用户相关的 Pydantic schemas"""
from pydantic import BaseModel
from typing import Optional
from datetime import datetime

class Token(BaseModel):
    """JWT Token 响应"""
    access_token: str
    token_type: str

class TokenData(BaseModel):
    """Token 数据"""
    user_id: Optional[int] = None

class UserBase(BaseModel):
    """用户基础信息"""
    username: str
    email: str

class UserCreate(UserBase):
    """创建用户"""
    password: str

class UserResponse(UserBase):
    """用户响应"""
    id: int
    is_active: bool
    created_at: datetime
    
    class Config:
        from_attributes = True

class UserLogin(BaseModel):
    """用户登录"""
    email: str
    password: str
