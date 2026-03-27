"""账户设置 API 路由"""
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel, EmailStr
from app.database import get_db
from app.models.user import User
from app.api.deps import get_current_user
from app.utils.security import verify_password, get_password_hash

router = APIRouter(prefix="/api/auth", tags=["账户设置"])

class AccountUpdate(BaseModel):
    """更新账户信息请求"""
    email: Optional[EmailStr] = None
    current_password: Optional[str] = None
    new_password: Optional[str] = None

class AccountResponse(BaseModel):
    """账户信息响应"""
    id: int
    username: str
    email: str
    is_active: bool
    created_at: str

@router.get("/account", response_model=AccountResponse)
async def get_account_info(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """获取当前用户的账户信息"""
    return AccountResponse(
        id=current_user.id,
        username=current_user.username,
        email=current_user.email,
        is_active=current_user.is_active,
        created_at=current_user.created_at.isoformat() if current_user.created_at else None
    )

@router.put("/account", response_model=AccountResponse)
async def update_account_info(
    account_data: AccountUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """更新当前用户的账户信息"""
    # 如果要修改密码，需要验证当前密码
    if account_data.new_password:
        if not account_data.current_password:
            raise HTTPException(status_code=400, detail="修改密码需要提供当前密码")
        
        if not verify_password(account_data.current_password, current_user.hashed_password):
            raise HTTPException(status_code=400, detail="当前密码错误")
        
        # 更新密码
        current_user.hashed_password = get_password_hash(account_data.new_password)
    
    # 如果要修改邮箱
    if account_data.email:
        # 检查邮箱是否已被其他用户使用
        existing_user = db.query(User).filter(
            User.email == account_data.email,
            User.id != current_user.id
        ).first()
        
        if existing_user:
            raise HTTPException(status_code=400, detail="该邮箱已被其他用户使用")
        
        current_user.email = account_data.email
    
    db.commit()
    db.refresh(current_user)
    
    return AccountResponse(
        id=current_user.id,
        username=current_user.username,
        email=current_user.email,
        is_active=current_user.is_active,
        created_at=current_user.created_at.isoformat() if current_user.created_at else None
    )