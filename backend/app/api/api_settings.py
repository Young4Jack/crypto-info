"""API设置 API 路由 - 使用配置文件存储"""
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
import httpx
import logging
from app.utils.logger import get_logger
from app.config_manager import config_manager

logger = get_logger(__name__)

router = APIRouter(prefix="/api/api-settings", tags=["API设置"])

class ApiSettingCreate(BaseModel):
    """创建API设置请求"""
    primary_api_url: str
    backup_api_url: Optional[str] = None
    api_key: Optional[str] = None
    api_secret: Optional[str] = None

class ApiSettingUpdate(BaseModel):
    """更新API设置请求"""
    primary_api_url: Optional[str] = None
    backup_api_url: Optional[str] = None
    api_key: Optional[str] = None
    api_secret: Optional[str] = None

class ApiSettingResponse(BaseModel):
    """API设置响应"""
    primary_api_url: Optional[str] = None
    backup_api_url: Optional[str] = None
    api_key: Optional[str] = None
    api_secret: Optional[str] = None

@router.get("/", response_model=ApiSettingResponse)
async def get_api_setting():
    """获取API设置"""
    api_settings = config_manager.get_api_settings()
    return ApiSettingResponse(
        primary_api_url=api_settings.get("primary_api_url"),
        backup_api_url=api_settings.get("backup_api_url"),
        api_key=api_settings.get("api_key"),
        api_secret=api_settings.get("api_secret")
    )

@router.post("/", response_model=ApiSettingResponse)
async def create_api_setting(setting_data: ApiSettingCreate):
    """创建或更新API设置"""
    api_settings = {
        "primary_api_url": setting_data.primary_api_url,
        "backup_api_url": setting_data.backup_api_url or "",
        "api_key": setting_data.api_key or "",
        "api_secret": setting_data.api_secret or ""
    }
    
    success = config_manager.save_api_settings(api_settings)
    if not success:
        raise HTTPException(status_code=500, detail="保存API设置失败")
    
    return ApiSettingResponse(
        primary_api_url=api_settings["primary_api_url"],
        backup_api_url=api_settings["backup_api_url"],
        api_key=api_settings["api_key"],
        api_secret=api_settings["api_secret"]
    )

@router.put("/", response_model=ApiSettingResponse)
async def update_api_setting(setting_data: ApiSettingUpdate):
    """更新API设置"""
    # 获取当前设置
    current_settings = config_manager.get_api_settings()
    
    # 更新字段
    if setting_data.primary_api_url is not None:
        current_settings["primary_api_url"] = setting_data.primary_api_url
    if setting_data.backup_api_url is not None:
        current_settings["backup_api_url"] = setting_data.backup_api_url
    if setting_data.api_key is not None:
        current_settings["api_key"] = setting_data.api_key
    if setting_data.api_secret is not None:
        current_settings["api_secret"] = setting_data.api_secret
    
    success = config_manager.save_api_settings(current_settings)
    if not success:
        raise HTTPException(status_code=500, detail="更新API设置失败")
    
    return ApiSettingResponse(
        primary_api_url=current_settings["primary_api_url"],
        backup_api_url=current_settings["backup_api_url"],
        api_key=current_settings["api_key"],
        api_secret=current_settings["api_secret"]
    )

@router.delete("/")
async def delete_api_setting():
    """删除API设置（重置为默认值）"""
    default_settings = {
        "primary_api_url": "https://api.binance.com/api/v3/ticker/price",
        "backup_api_url": "",
        "api_key": "",
        "api_secret": ""
    }
    
    success = config_manager.save_api_settings(default_settings)
    if not success:
        raise HTTPException(status_code=500, detail="删除API设置失败")
    
    return {"message": "API设置已重置为默认值"}


@router.post("/test-primary")
async def test_primary_api():
    """测试主API连接"""
    api_settings = config_manager.get_api_settings()
    primary_api_url = api_settings.get("primary_api_url")
    
    if not primary_api_url:
        raise HTTPException(status_code=404, detail="未配置主API地址")
    
    try:
        logger.info(f"测试主API连接: {primary_api_url}")
        
        # 构建测试请求
        headers = {}
        api_key = api_settings.get("api_key")
        if api_key:
            headers["X-API-Key"] = api_key
        
        async with httpx.AsyncClient() as client:
            response = await client.get(
                primary_api_url,
                headers=headers,
                timeout=10.0
            )
            response.raise_for_status()
            
            logger.info(f"主API测试成功: {response.status_code}")
            
            return {
                "success": True,
                "message": "主API连接测试成功",
                "status_code": response.status_code,
                "response_time": response.elapsed.total_seconds()
            }
    except Exception as e:
        logger.error(f"主API测试失败: {str(e)}")
        return {
            "success": False,
            "message": f"主API连接测试失败: {str(e)}",
            "error": str(e)
        }


@router.post("/test-backup")
async def test_backup_api():
    """测试备用API连接"""
    api_settings = config_manager.get_api_settings()
    backup_api_url = api_settings.get("backup_api_url")
    
    if not backup_api_url:
        raise HTTPException(status_code=404, detail="未配置备用API地址")
    
    try:
        logger.info(f"测试备用API连接: {backup_api_url}")
        
        # 构建测试请求
        headers = {}
        api_key = api_settings.get("api_key")
        if api_key:
            headers["X-API-Key"] = api_key
        
        async with httpx.AsyncClient() as client:
            response = await client.get(
                backup_api_url,
                headers=headers,
                timeout=10.0
            )
            response.raise_for_status()
            
            logger.info(f"备用API测试成功: {response.status_code}")
            
            return {
                "success": True,
                "message": "备用API连接测试成功",
                "status_code": response.status_code,
                "response_time": response.elapsed.total_seconds()
            }
    except Exception as e:
        logger.error(f"备用API测试失败: {str(e)}")
        return {
            "success": False,
            "message": f"备用API连接测试失败: {str(e)}",
            "error": str(e)
        }
