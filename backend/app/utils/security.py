"""安全工具函数"""
from datetime import datetime, timedelta
from typing import Optional
from jose import JWTError, jwt
import bcrypt
from sqlalchemy.orm import Session
from app.config import settings
from app.models.user import User
from app.models.alert import PriceAlert
from app.models.asset import Asset
from app.models.cryptocurrency import Cryptocurrency
from app.schemas.user import TokenData
from app.config_manager import config_manager

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """验证密码"""
    try:
        return bcrypt.checkpw(plain_password.encode('utf-8'), hashed_password.encode('utf-8'))
    except Exception:
        return False

def get_password_hash(password: str) -> str:
    """获取密码哈希"""
    salt = bcrypt.gensalt()
    return bcrypt.hashpw(password.encode('utf-8'), salt).decode('utf-8')

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """创建访问令牌"""
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.now(config_manager.get_timezone()) + expires_delta
    else:
        expire = datetime.now(config_manager.get_timezone()) + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
    return encoded_jwt

def verify_token(token: str) -> Optional[TokenData]:
    """验证令牌"""
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        user_id: int = payload.get("sub")
        if user_id is None:
            return None
        token_data = TokenData(user_id=user_id)
        return token_data
    except JWTError:
        return None

def authenticate_user(db: Session, email: str, password: str) -> Optional[User]:
    """认证用户（支持邮箱或用户名登录）"""
    # 先尝试通过邮箱查找
    user = db.query(User).filter(User.email == email).first()
    
    # 如果找不到，尝试通过用户名查找
    if not user:
        user = db.query(User).filter(User.username == email).first()
    
    if not user:
        return None
    if not verify_password(password, user.hashed_password):
        return None
    return user
