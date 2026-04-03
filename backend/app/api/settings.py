"""通知设置 API 路由 - 使用配置文件存储"""
from typing import Optional
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
import httpx
import logging
from app.utils.logger import get_logger
from app.config_manager import config_manager

logger = get_logger(__name__)

router = APIRouter(prefix="/settings", tags=["系统设置"])

class NotificationSettingCreate(BaseModel):
    """创建通知设置请求"""
    api_url: str
    auth_token: str
    channel: str = ""

class NotificationSettingUpdate(BaseModel):
    """更新通知设置请求"""
    api_url: Optional[str] = None
    auth_token: Optional[str] = None
    channel: Optional[str] = None

class NotificationSettingResponse(BaseModel):
    """通知设置响应"""
    api_url: Optional[str] = None
    auth_token: Optional[str] = None
    channel: Optional[str] = None

@router.get("/notification", response_model=NotificationSettingResponse)
async def get_notification_setting():
    """获取通知设置"""
    notification_settings = config_manager.get_notification_settings()
    return NotificationSettingResponse(
        api_url=notification_settings.get("api_url"),
        auth_token=notification_settings.get("auth_token"),
        channel=notification_settings.get("channel")
    )

@router.post("/notification", response_model=NotificationSettingResponse)
async def create_notification_setting(setting_data: NotificationSettingCreate):
    """创建或更新通知设置"""
    notification_settings = {
        "api_url": setting_data.api_url,
        "auth_token": setting_data.auth_token,
        "channel": setting_data.channel or ""
    }
    
    success = config_manager.save_notification_settings(notification_settings)
    if not success:
        raise HTTPException(status_code=500, detail="保存通知设置失败")
    
    return NotificationSettingResponse(
        api_url=notification_settings["api_url"],
        auth_token=notification_settings["auth_token"],
        channel=notification_settings["channel"]
    )

@router.put("/notification", response_model=NotificationSettingResponse)
async def update_notification_setting(setting_data: NotificationSettingUpdate):
    """更新通知设置"""
    # 获取当前设置
    current_settings = config_manager.get_notification_settings()
    
    # 更新字段
    if setting_data.api_url is not None:
        current_settings["api_url"] = setting_data.api_url
    if setting_data.auth_token is not None:
        current_settings["auth_token"] = setting_data.auth_token
    if setting_data.channel is not None:
        current_settings["channel"] = setting_data.channel
    
    success = config_manager.save_notification_settings(current_settings)
    if not success:
        raise HTTPException(status_code=500, detail="更新通知设置失败")
    
    return NotificationSettingResponse(
        api_url=current_settings["api_url"],
        auth_token=current_settings["auth_token"],
        channel=current_settings["channel"]
    )

@router.delete("/notification")
async def delete_notification_setting():
    """删除通知设置（重置为默认值）"""
    default_settings = {
        "api_url": "",
        "auth_token": "",
        "channel": "email"
    }
    
    success = config_manager.save_notification_settings(default_settings)
    if not success:
        raise HTTPException(status_code=500, detail="删除通知设置失败")
    
    return {"message": "通知设置已重置为默认值"}


@router.post("/notification/test")
async def test_notification_setting():
    """测试通知设置连接"""
    notification_settings = config_manager.get_notification_settings()
    api_url = notification_settings.get("api_url")
    
    if not api_url:
        raise HTTPException(status_code=404, detail="未配置通知API地址")
    
    try:
        logger.info(f"测试通知API连接: {api_url}")
        
        # 构建测试请求
        headers = {}
        auth_token = notification_settings.get("auth_token")
        if auth_token:
            headers["Authorization"] = auth_token
        
        # 发送测试通知
        test_data = {
            "title": "测试通知",
            "description": "这是一条测试通知，用于验证通知API连接是否正常",
            "channel": notification_settings.get("channel", "email"),
            "content": "如果您收到此消息，说明通知API配置正确！"
        }
        
        async with httpx.AsyncClient() as client:
            response = await client.post(
                api_url,
                headers=headers,
                data=test_data,
                timeout=10.0
            )
            response.raise_for_status()
            
            logger.info(f"通知API测试成功: {response.status_code}")
            
            return {
                "success": True,
                "message": "通知API连接测试成功",
                "status_code": response.status_code,
                "response_time": response.elapsed.total_seconds()
            }
    except Exception as e:
        logger.error(f"通知API测试失败: {str(e)}")
        return {
            "success": False,
            "message": f"通知API连接测试失败: {str(e)}",
            "error": str(e)
        }
