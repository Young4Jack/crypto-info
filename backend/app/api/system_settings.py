"""系统设置 API 路由 - 使用配置文件存储"""
from typing import Optional
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
import logging
from app.utils.logger import get_logger
from app.config_manager import config_manager

logger = get_logger(__name__)

router = APIRouter(prefix="/api/system-settings", tags=["系统设置"])

class SystemSettingCreate(BaseModel):
    """创建系统设置请求"""
    refresh_interval: int = 5
    enable_captcha: bool = False
    site_title: str = "Crypto-info"
    site_description: str = "数字货币价格监控和预警系统"
    log_level: str = "INFO"
    enable_logging: bool = True
    default_dark_mode: bool = False
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
    timezone: str

@router.get("/", response_model=SystemSettingResponse)
async def get_system_setting():
    """获取系统设置"""
    system_settings = config_manager.get_system_settings()
    return SystemSettingResponse(
        refresh_interval=system_settings.get("refresh_interval", 5),
        enable_captcha=system_settings.get("enable_captcha", False),
        site_title=system_settings.get("site_title", "Crypto-info"),
        site_description=system_settings.get("site_description", "数字货币价格监控和预警系统"),
        log_level=system_settings.get("log_level", "INFO"),
        enable_logging=system_settings.get("enable_logging", True),
        default_dark_mode=system_settings.get("default_dark_mode", False),
        timezone=system_settings.get("timezone", "Asia/Shanghai")
    )

@router.post("/", response_model=SystemSettingResponse)
async def create_system_setting(setting_data: SystemSettingCreate):
    """创建或更新系统设置"""
    system_settings = {
        "refresh_interval": setting_data.refresh_interval,
        "enable_captcha": setting_data.enable_captcha,
        "site_title": setting_data.site_title,
        "site_description": setting_data.site_description,
        "log_level": setting_data.log_level,
        "enable_logging": setting_data.enable_logging,
        "default_dark_mode": setting_data.default_dark_mode,
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
        timezone=system_settings["timezone"]
    )

@router.put("/", response_model=SystemSettingResponse)
async def update_system_setting(setting_data: SystemSettingUpdate):
    """更新系统设置"""
    # 获取当前设置
    current_settings = config_manager.get_system_settings()
    
    # 更新字段
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
        timezone=current_settings["timezone"]
    )

@router.delete("/")
async def delete_system_setting():
    """删除系统设置（重置为默认值）"""
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
