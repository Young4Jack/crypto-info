"""系统设置 API 路由 - 使用配置文件存储"""
from typing import Optional, Dict, Any
from fastapi import APIRouter, HTTPException, Header, Request, Depends
from pydantic import BaseModel
import logging
import requests
import json
from datetime import datetime
from app.utils.logger import get_logger
from app.config_manager import config_manager
from app.utils.security import verify_token

logger = get_logger(__name__)

router = APIRouter(prefix="/api/system-settings", tags=["系统设置"])

EXCHANGE_API_URL = "https://cdn.jsdelivr.net/npm/@fawazahmed0/currency-api@latest/v1/currencies/usd.json"


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


def _update_exchange_rates() -> Dict[str, float]:
    """从免费 API 获取汇率，返回 USD 为基准的汇率字典"""
    try:
        response = requests.get(EXCHANGE_API_URL, timeout=10)
        if response.status_code == 200:
            data = response.json()
            # API 返回结构: { "date": "2026-04-08", "usd": { "cny": 6.83, ... } }
            usd_rates = data.get("usd", {})
            # 只提取我们需要的货币（小写键）
            target_currencies = ["cny", "eur", "jpy"]
            result = {}
            for curr in target_currencies:
                if curr in usd_rates:
                    # 转换为大写键存储
                    result[curr.upper()] = usd_rates[curr]
            if result:
                return result
    except Exception as e:
        logger.error(f"获取汇率失败: {e}")
    return {"CNY": 1, "EUR": 1, "JPY": 1}


def check_and_update_exchange_rates() -> None:
    """检查并更新汇率（每天一次）"""
    system_settings = config_manager.get_system_settings()
    today = datetime.now().strftime("%Y-%m-%d")
    stored_date = system_settings.get("exchange_rates_date", "")
    
    # 如果日期不同或没有汇率数据，则更新
    if stored_date != today or not system_settings.get("exchange_rates"):
        logger.info("开始更新汇率数据...")
        new_rates = _update_exchange_rates()
        system_settings["exchange_rates"] = new_rates
        system_settings["exchange_rates_date"] = today
        config_manager.save_system_settings(system_settings)
        logger.info(f"汇率已更新: {new_rates}")


class SystemSettingCreate(BaseModel):
    """创建系统设置请求"""
    refresh_interval: int = 5
    enable_captcha: bool = False
    site_title: str = "Crypto-info"
    site_description: str = "数字货币价格监控和预警系统"
    base_url: str = ""
    log_level: str = "INFO"
    enable_logging: bool = True
    default_dark_mode: bool = False
    api_shared_secret: str = ""
    timezone: str = "Asia/Shanghai"
    current_pricing_currency: str = "USD"
    available_currencies: list = ["USD", "CNY", "EUR", "JPY"]


class SystemSettingUpdate(BaseModel):
    """更新系统设置请求"""
    refresh_interval: Optional[int] = None
    enable_captcha: Optional[bool] = None
    site_title: Optional[str] = None
    site_description: Optional[str] = None
    base_url: Optional[str] = None
    log_level: Optional[str] = None
    enable_logging: Optional[bool] = None
    default_dark_mode: Optional[bool] = None
    api_shared_secret: Optional[str] = None
    timezone: Optional[str] = None
    current_pricing_currency: Optional[str] = None
    available_currencies: Optional[list] = None


class SystemSettingResponse(BaseModel):
    """系统设置响应"""
    refresh_interval: int
    enable_captcha: bool
    site_title: str
    site_description: str
    base_url: str
    log_level: str
    enable_logging: bool
    default_dark_mode: bool
    api_shared_secret: str
    timezone: str
    current_pricing_currency: str
    available_currencies: list
    exchange_rates: dict
    exchange_rates_date: str


@router.get("/", response_model=SystemSettingResponse)
async def get_system_setting(
    _: None = Depends(verify_system_write_access)
):
    """获取系统设置（需要认证）"""
    # 检查并可能更新汇率
    check_and_update_exchange_rates()
    
    system_settings = config_manager.get_system_settings()
    return SystemSettingResponse(
        refresh_interval=system_settings.get("refresh_interval", 5),
        enable_captcha=system_settings.get("enable_captcha", False),
        site_title=system_settings.get("site_title", "Crypto-info"),
        site_description=system_settings.get("site_description", "数字货币价格监控和预警系统"),
        base_url=system_settings.get("base_url", ""),
        log_level=system_settings.get("log_level", "INFO"),
        enable_logging=system_settings.get("enable_logging", True),
        default_dark_mode=system_settings.get("default_dark_mode", False),
        api_shared_secret=system_settings.get("api_shared_secret", ""),
        timezone=system_settings.get("timezone", "Asia/Shanghai"),
        current_pricing_currency=system_settings.get("current_pricing_currency", "USD"),
        available_currencies=system_settings.get("available_currencies", ["USD", "CNY", "EUR", "JPY"]),
        exchange_rates=system_settings.get("exchange_rates", {"CNY": 1, "EUR": 1, "JPY": 1}),
        exchange_rates_date=system_settings.get("exchange_rates_date", "")
    )


@router.post("/", response_model=SystemSettingResponse)
async def create_system_setting(
    setting_data: SystemSettingCreate,
    _: None = Depends(verify_system_write_access)
):
    """创建或更新系统设置（需要认证）"""
    current_settings = config_manager.get_system_settings()
    
    # 检查汇率
    check_and_update_exchange_rates()
    
    system_settings = {
        "refresh_interval": setting_data.refresh_interval,
        "enable_captcha": setting_data.enable_captcha,
        "site_title": setting_data.site_title,
        "site_description": setting_data.site_description,
        "base_url": setting_data.base_url,
        "log_level": setting_data.log_level,
        "enable_logging": setting_data.enable_logging,
        "default_dark_mode": setting_data.default_dark_mode,
        "api_shared_secret": setting_data.api_shared_secret or current_settings.get("api_shared_secret", ""),
        "timezone": setting_data.timezone,
        "current_pricing_currency": setting_data.current_pricing_currency,
        "available_currencies": setting_data.available_currencies,
    }
    
    # 保留现有的汇率数据
    system_settings["exchange_rates"] = current_settings.get("exchange_rates", {"CNY": 1, "EUR": 1, "JPY": 1})
    system_settings["exchange_rates_date"] = current_settings.get("exchange_rates_date", "")
    
    success = config_manager.save_system_settings(system_settings)
    if not success:
        raise HTTPException(status_code=500, detail="保存系统设置失败")
    
    logger.info(f"更新系统设置: currency={system_settings['current_pricing_currency']}, refresh_interval={system_settings['refresh_interval']}")
    
    return SystemSettingResponse(
        refresh_interval=system_settings["refresh_interval"],
        enable_captcha=system_settings["enable_captcha"],
        site_title=system_settings["site_title"],
        site_description=system_settings["site_description"],
        base_url=system_settings["base_url"],
        log_level=system_settings["log_level"],
        enable_logging=system_settings["enable_logging"],
        default_dark_mode=system_settings["default_dark_mode"],
        api_shared_secret=system_settings["api_shared_secret"],
        timezone=system_settings["timezone"],
        current_pricing_currency=system_settings["current_pricing_currency"],
        available_currencies=system_settings["available_currencies"],
        exchange_rates=system_settings["exchange_rates"],
        exchange_rates_date=system_settings["exchange_rates_date"]
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
    if setting_data.base_url is not None:
        current_settings["base_url"] = setting_data.base_url
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
    if setting_data.current_pricing_currency is not None:
        current_settings["current_pricing_currency"] = setting_data.current_pricing_currency
    if setting_data.available_currencies is not None:
        current_settings["available_currencies"] = setting_data.available_currencies
    
    success = config_manager.save_system_settings(current_settings)
    if not success:
        raise HTTPException(status_code=500, detail="更新系统设置失败")
    
    logger.info(f"更新系统设置: current_pricing_currency={current_settings.get('current_pricing_currency')}, refresh_interval={current_settings.get('refresh_interval')}")
    
    return SystemSettingResponse(
        refresh_interval=current_settings.get("refresh_interval", 5),
        enable_captcha=current_settings.get("enable_captcha", False),
        site_title=current_settings.get("site_title", "Crypto-info"),
        site_description=current_settings.get("site_description", ""),
        base_url=current_settings.get("base_url", ""),
        log_level=current_settings.get("log_level", "INFO"),
        enable_logging=current_settings.get("enable_logging", True),
        default_dark_mode=current_settings.get("default_dark_mode", False),
        api_shared_secret=current_settings.get("api_shared_secret", ""),
        timezone=current_settings.get("timezone", "Asia/Shanghai"),
        current_pricing_currency=current_settings.get("current_pricing_currency", "USD"),
        available_currencies=current_settings.get("available_currencies", ["USD", "CNY", "EUR", "JPY"]),
        exchange_rates=current_settings.get("exchange_rates", {"CNY": 1, "EUR": 1, "JPY": 1}),
        exchange_rates_date=current_settings.get("exchange_rates_date", "")
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
    # 检查并可能更新汇率（公开接口也需要检查，因为前端会用到汇率数据）
    check_and_update_exchange_rates()
    
    system_settings = config_manager.get_system_settings()
    
    return {
        "site_title": system_settings.get("site_title", "Crypto-info"),
        "site_description": system_settings.get("site_description", "数字货币价格监控和预警系统"),
        "base_url": system_settings.get("base_url", ""),
        "refresh_interval": system_settings.get("refresh_interval", 1),
        "default_dark_mode": system_settings.get("default_dark_mode", False),
        "backend_port": system_settings.get("backend_port", 8000),
        "frontend_port": system_settings.get("frontend_port", 5173),
        "timezone": system_settings.get("timezone", "Asia/Shanghai"),
        "current_pricing_currency": system_settings.get("current_pricing_currency", "USD"),
        "available_currencies": system_settings.get("available_currencies", ["USD", "CNY", "EUR", "JPY"]),
        "exchange_rates": system_settings.get("exchange_rates", {"CNY": 1, "EUR": 1, "JPY": 1}),
        "exchange_rates_date": system_settings.get("exchange_rates_date", "")
    }


@router.post("/refresh-exchange-rates")
async def refresh_exchange_rates(
    _: None = Depends(verify_system_write_access)
):
    """手动刷新汇率（需要认证）"""
    check_and_update_exchange_rates()
    system_settings = config_manager.get_system_settings()
    return {
        "exchange_rates": system_settings.get("exchange_rates", {}),
        "exchange_rates_date": system_settings.get("exchange_rates_date", "")
    }