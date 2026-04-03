"""API 依赖项"""
from typing import Generator
from fastapi import Depends, HTTPException, Header, Request, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session
from app.database import SessionLocal
from app.models.user import User
from app.utils.security import verify_token
from app.schemas.user import TokenData
from app.config_manager import config_manager

# OAuth2 密码承载令牌
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login", auto_error=False)

def get_db() -> Generator:
    """获取数据库会话"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def get_current_user(
    request: Request,
    db: Session = Depends(get_db),
    token: str = Depends(oauth2_scheme),
    x_shared_secret: str | None = Header(None, alias="X-Shared-Secret"),
) -> User:
    """获取当前用户（支持 Bearer Token 或共享密钥）"""
    # 1. 优先检查共享密钥
    system_settings = config_manager.get_system_settings()
    shared_secret = system_settings.get("api_shared_secret", "")
    if shared_secret and x_shared_secret and x_shared_secret == shared_secret:
        # 返回一个系统用户对象
        system_user = User()
        system_user.id = 0
        system_user.username = "system"
        system_user.email = "system@local"
        return system_user
    
    # 2. 尝试验证 Bearer Token
    if token:
        token_data = verify_token(token)
        if token_data:
            user = db.query(User).filter(User.id == token_data.user_id).first()
            if user:
                return user
    
    # 3. 认证失败
    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="未授权。请配置 X-Shared-Secret 请求头，或使用登录获取 Bearer Token",
        headers={"WWW-Authenticate": "Bearer"},
    )