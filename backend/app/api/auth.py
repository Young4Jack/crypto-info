"""认证 API"""
from datetime import timedelta
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from pydantic import BaseModel
from sqlalchemy.orm import Session
from app.database import SessionLocal, get_db
from app.models.user import User
from app.config_manager import config_manager
from app.schemas.user import Token, UserResponse
from app.utils.security import authenticate_user, create_access_token, get_password_hash, verify_password
from app.utils.captcha import generate_captcha
from app.api.deps import get_current_user
from app.config import settings

router = APIRouter(prefix="/api/auth", tags=["认证"])

class LoginForm(BaseModel):
    email: str
    password: str
    captchaAnswer: int | None = None
    captchaId: str | None = None
    login_type: str = "email"  # "email" 或 "username"


class CaptchaResponse(BaseModel):
    captcha_id: str
    captcha_image: str
    enabled: bool

@router.get("/captcha", response_model=CaptchaResponse)
async def get_captcha():
    """获取验证码"""
    # 检查是否启用了验证码
    system_settings = config_manager.get_system_settings()
    captcha_enabled = system_settings.get('enable_captcha', False)
    
    if not captcha_enabled:
        return CaptchaResponse(
            captcha_id="",
            captcha_image="",
            enabled=False
        )
    
    # 生成验证码
    image_base64, expression, answer = generate_captcha()
    
    # 生成一个简单的captcha_id（实际项目中应该使用Redis存储）
    import uuid
    captcha_id = str(uuid.uuid4())
    
    # 这里应该将captcha_id和答案存储到Redis或数据库中
    # 为了简化，我们使用内存存储（实际项目中应该使用Redis）
    if not hasattr(get_captcha, 'captcha_store'):
        get_captcha.captcha_store = {}
    get_captcha.captcha_store[captcha_id] = answer
    
    return CaptchaResponse(
        captcha_id=captcha_id,
        captcha_image=image_base64,
        enabled=True
    )


@router.post("/verify-captcha")
async def verify_captcha(captcha_id: str, answer: int):
    """验证验证码"""
    if not hasattr(get_captcha, 'captcha_store'):
        return {"valid": False}
    
    stored_answer = get_captcha.captcha_store.get(captcha_id)
    if stored_answer is None:
        return {"valid": False}
    
    # 验证后删除验证码
    del get_captcha.captcha_store[captcha_id]
    
    return {"valid": stored_answer == answer}


@router.post("/login", response_model=Token)
async def login(form_data: LoginForm):
    """用户登录"""
    db = SessionLocal()
    try:
        # 检查是否启用了验证码
        system_settings = config_manager.get_system_settings()
        captcha_enabled = system_settings.get('enable_captcha', False)
        
        # 如果启用了验证码，验证验证码
        if captcha_enabled:
            if not form_data.captchaId or form_data.captchaAnswer is None:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="验证码不能为空"
                )
            
            # 验证验证码
            if not hasattr(get_captcha, 'captcha_store'):
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="验证码已过期，请重新获取"
                )
            
            stored_answer = get_captcha.captcha_store.get(form_data.captchaId)
            if stored_answer is None:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="验证码已过期，请重新获取"
                )
            
            if stored_answer != form_data.captchaAnswer:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="验证码错误"
                )
            
            # 验证成功后删除验证码
            del get_captcha.captcha_store[form_data.captchaId]
        
        # 验证用户（支持邮箱或用户名登录）
        user = authenticate_user(db, form_data.email, form_data.password)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="邮箱/用户名或密码错误",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
        access_token = create_access_token(
            data={"sub": str(user.id)}, expires_delta=access_token_expires
        )
        
        return {"access_token": access_token, "token_type": "bearer"}
    finally:
        db.close()

@router.get("/me", response_model=UserResponse)
async def get_current_user_info(current_user: User = Depends(get_current_user)):
    """获取当前用户信息"""
    return current_user

class AccountUpdate(BaseModel):
    username: str | None = None
    email: str | None = None
    current_password: str
    new_password: str | None = None
    confirm_new_password: str | None = None

@router.put("/account")
async def update_account(
    account_data: AccountUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """更新账户信息"""
    try:
        # 验证当前密码
        if not verify_password(account_data.current_password, current_user.hashed_password):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="当前密码错误"
            )
        
        # 重新查库获取用户对象，避免Session脱离问题
        db_user = db.query(User).filter(User.id == current_user.id).first()
        if not db_user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="用户不存在"
            )
        
        # 更新用户名（如果提供且不为空）
        if account_data.username and account_data.username.strip() and account_data.username != db_user.username:
            # 检查用户名是否已存在
            existing_user = db.query(User).filter(
                User.username == account_data.username,
                User.id != db_user.id
            ).first()
            if existing_user:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="用户名已被使用"
                )
            db_user.username = account_data.username
        
        # 更新邮箱（如果提供且不为空）
        if account_data.email and account_data.email.strip() and account_data.email != db_user.email:
            # 检查邮箱是否已存在
            existing_email = db.query(User).filter(
                User.email == account_data.email,
                User.id != db_user.id
            ).first()
            if existing_email:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="邮箱已被使用"
                )
            db_user.email = account_data.email
        
        # 更新密码（如果提供且不为空）
        if account_data.new_password and account_data.new_password.strip():
            # 检查密码一致性
            if account_data.confirm_new_password != account_data.new_password:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="新密码与确认密码不一致"
                )
            db_user.hashed_password = get_password_hash(account_data.new_password)
        
        db.commit()
        db.refresh(db_user)
        
        return {
            "success": True,
            "message": "账户信息更新成功",
            "user": {
                "id": db_user.id,
                "username": db_user.username,
                "email": db_user.email
            }
        }
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"更新账户信息失败: {str(e)}"
        )
