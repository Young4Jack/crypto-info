"""系统设置 API 路由 - 使用配置文件存储"""
from typing import Optional
from fastapi import APIRouter, HTTPException, Header, Request, Depends
from pydantic import BaseModel
import logging
from app.utils.logger import get_logger
from app.config_manager import config_manager
from app.utils.security import verify_token

logger = get_logger(__name__)

router = APIRouter(prefix="/system-settings", tags=["系统设置"])

def _mask_secret(secret: str) -> str:
    """掩码处理：显示前3位 + ... + 后3位"""
    if not secret:
        return ""
    if len(secret) <= 6:
        return "***"
    return secret[:3] + "..." + secret[-3:]

async def verify_system_write_access(
    request: Request,
    x_shared_secret: str | None = Header(None, alias="X-Shared-Secret"),
) -> None:
    """验证系统设置写权限：共享密钥 或 登录 Token"""
    system_settings = config_manager.get_system_settings()
    shared_secret = system_settings.get("api_shared_secret", "")
    
    # 1. 优先检查共享密钥
    if shared_secret and x_shared_secret and x_shared_secret == shared_secret:
        return
    
    # 2. 共享密钥无效，尝试验证 Bearer Token
    auth_header = request.headers.get("authorization", "")
    if auth_header.startswith("Bearer "):
        token = auth_header[7:]
        token_data = verify_token(token)
        if token_data is not None:
            return
    
    raise HTTPException(
        status_code=401,
        detail="未授权。请配置 X-Shared-Secret 请求头，或使用登录获取 Bearer Token"
    )

class SystemSettingCreate(BaseModel):
    """创建系统设置请求"""
    refresh_interval: int = 5
    enable_captcha: bool = False
    site_title: str = "Crypto-info"
    site_description: str = "数字货币价格监控和预警系统"
    log_level: str = "INFO"
    enable_logging: bool = True
    default_dark_mode: bool = False
    api_shared_secret: str = ""
    timezone: str = "Asia/Shanghai"

class SystemSettingUpdate(BaseModel):
    """更新系统设置请求"""
    refresh_interval: Optional[int] = None
    enable_captcha: Optional[bool] = None
    site_title: Optional[str] = None
    site_description: Optional[str] = None
    log_level: Optional[str] = None
    enable_logging: Optional[bool] = None
    default_dark_mode: Optional[bool] = None
    api_shared_secret: Optional[str] = None
    timezone: Optional[str] = None

class SystemSettingResponse(BaseModel):
    """系统设置响应"""
    refresh_interval: int
    enable_captcha: bool
    site_title: str
    site_description: str
    log_level: str
    enable_logging: bool
    default_dark_mode: bool
    api_shared_secret: str
    timezone: str

@router.get("/", response_model=SystemSettingResponse)
async def get_system_setting():
    """获取系统设置（公开只读）"""
    system_settings = config_manager.get_system_settings()
    return SystemSettingResponse(
        refresh_interval=system_settings.get("refresh_interval", 5),
        enable_captcha=system_settings.get("enable_captcha", False),
        site_title=system_settings.get("site_title", "Crypto-info"),
        site_description=system_settings.get("site_description", "数字货币价格监控和预警系统"),
        log_level=system_settings.get("log_level", "INFO"),
        enable_logging=system_settings.get("enable_logging", True),
        default_dark_mode=system_settings.get("default_dark_mode", False),
        api_shared_secret=_mask_secret(system_settings.get("api_shared_secret", "")),
        timezone=system_settings.get("timezone", "Asia/Shanghai")
    )

@router.post("/", response_model=SystemSettingResponse)
async def create_system_setting(
    setting_data: SystemSettingCreate,
    _: None = Depends(verify_system_write_access)
):
    """创建或更新系统设置（需要认证）"""
    current_settings = config_manager.get_system_settings()
    system_settings = {
        "refresh_interval": setting_data.refresh_interval,
        "enable_captcha": setting_data.enable_captcha,
        "site_title": setting_data.site_title,
        "site_description": setting_data.site_description,
        "log_level": setting_data.log_level,
        "enable_logging": setting_data.enable_logging,
        "default_dark_mode": setting_data.default_dark_mode,
        "api_shared_secret": setting_data.api_shared_secret or current_settings.get("api_shared_secret", ""),
        "timezone": setting_data.timezone
    }
    
    success = config_manager.save_system_settings(system_settings)
    if not success:
        raise HTTPException(status_code=500, detail="保存系统设置失败")
    
    logger.info(f"更新系统设置: refresh_interval={system_settings['refresh_interval']}, enable_captcha={system_settings['enable_captcha']}, site_title={system_settings['site_title']}, log_level={system_settings['log_level']}, enable_logging={system_settings['enable_logging']}, timezone={system_settings['timezone']}")
    
    return SystemSettingResponse(
        refresh_interval=system_settings["refresh_interval"],
        enable_captcha=system_settings["enable_captcha"],
        site_title=system_settings["site_title"],
        site_description=system_settings["site_description"],
        log_level=system_settings["log_level"],
        enable_logging=system_settings["enable_logging"],
        default_dark_mode=system_settings["default_dark_mode"],
        api_shared_secret=system_settings["api_shared_secret"],
        timezone=system_settings["timezone"]
    )

@router.put("/", response_model=SystemSettingResponse)
async def update_system_setting(
    setting_data: SystemSettingUpdate,
    _: None = Depends(verify_system_write_access)
):
    """更新系统设置（需要认证）"""
    current_settings = config_manager.get_system_settings()
    
    if setting_data.refresh_interval is not None:
        current_settings["refresh_interval"] = setting_data.refresh_interval
    if setting_data.enable_captcha is not None:
        current_settings["enable_captcha"] = setting_data.enable_captcha
    if setting_data.site_title is not None:
        current_settings["site_title"] = setting_data.site_title
    if setting_data.site_description is not None:
        current_settings["site_description"] = setting_data.site_description
    if setting_data.log_level is not None:
        current_settings["log_level"] = setting_data.log_level
    if setting_data.enable_logging is not None:
        current_settings["enable_logging"] = setting_data.enable_logging
    if setting_data.default_dark_mode is not None:
        current_settings["default_dark_mode"] = setting_data.default_dark_mode
    if setting_data.api_shared_secret is not None:
        current_settings["api_shared_secret"] = setting_data.api_shared_secret
    if setting_data.timezone is not None:
        current_settings["timezone"] = setting_data.timezone
    
    success = config_manager.save_system_settings(current_settings)
    if not success:
        raise HTTPException(status_code=500, detail="更新系统设置失败")
    
    logger.info(f"更新系统设置: refresh_interval={current_settings['refresh_interval']}, enable_captcha={current_settings['enable_captcha']}, site_title={current_settings['site_title']}, log_level={current_settings['log_level']}, enable_logging={current_settings['enable_logging']}, timezone={current_settings['timezone']}")
    
    return SystemSettingResponse(
        refresh_interval=current_settings["refresh_interval"],
        enable_captcha=current_settings["enable_captcha"],
        site_title=current_settings["site_title"],
        site_description=current_settings["site_description"],
        log_level=current_settings["log_level"],
        enable_logging=current_settings["enable_logging"],
        default_dark_mode=current_settings["default_dark_mode"],
        api_shared_secret=current_settings.get("api_shared_secret", ""),
        timezone=current_settings["timezone"]
    )

@router.delete("/")
async def delete_system_setting(
    _: None = Depends(verify_system_write_access)
):
    """删除系统设置（重置为默认值）（需要认证）"""
    default_settings = {
        "refresh_interval": 5,
        "enable_captcha": False,
        "site_title": "Crypto-info",
        "site_description": "数字货币价格监控和预警系统"
    }
    
    success = config_manager.save_system_settings(default_settings)
    if not success:
        raise HTTPException(status_code=500, detail="删除系统设置失败")
    
    logger.info("删除系统设置，重置为默认值")
    
    return {"message": "系统设置已重置为默认值"}


@router.get("/public", response_model=dict)
async def get_public_system_settings():
    """获取公开的系统设置（无需认证）"""
    system_settings = config_manager.get_system_settings()
    
    return {
        "site_title": system_settings.get("site_title", "Crypto-info"),
        "site_description": system_settings.get("site_description", "数字货币价格监控和预警系统"),
        "refresh_interval": system_settings.get("refresh_interval", 1),
        "default_dark_mode": system_settings.get("default_dark_mode", False)
    }
