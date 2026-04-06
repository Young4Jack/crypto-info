"""通知渠道管理 API 路由"""
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from app.config_manager import config_manager
from app.api.deps import get_current_user
from app.models.user import User

router = APIRouter(prefix="/api/settings/notification-channels", tags=["通知渠道管理"])

class NotificationChannelCreate(BaseModel):
    name: str
    api_url: str
    auth_token: str = ""
    is_default: bool = False
    default_group: str = "yes"
    groups: list[str] = ["yes"]

class NotificationChannelUpdate(BaseModel):
    name: Optional[str] = None
    api_url: Optional[str] = None
    auth_token: Optional[str] = None
    is_default: Optional[bool] = None
    default_group: Optional[str] = None
    groups: Optional[list[str]] = None

class NotificationChannelResponse(BaseModel):
    name: str
    api_url: str
    auth_token: str
    is_default: bool
    default_group: str
    groups: list[str]

@router.get("/", response_model=list[NotificationChannelResponse])
async def get_channels(
    current_user: User = Depends(get_current_user)
):
    """获取所有通知渠道（需要认证）"""
    channels = config_manager.get_notification_channels()
    return [
        NotificationChannelResponse(
            name=ch["name"],
            api_url=ch["api_url"],
            auth_token=ch.get("auth_token", ""),
            is_default=ch.get("is_default", False),
            default_group=ch.get("default_group", "yes"),
            groups=ch.get("groups", ["yes"])
        )
        for ch in channels
    ]

@router.post("/", response_model=NotificationChannelResponse)
async def create_channel(
    channel_data: NotificationChannelCreate,
    current_user: User = Depends(get_current_user)
):
    """创建通知渠道（需要认证）"""
    channels = config_manager.get_notification_channels()

    if any(ch["name"] == channel_data.name for ch in channels):
        raise HTTPException(status_code=400, detail=f"渠道名称 '{channel_data.name}' 已存在")

    if channel_data.is_default:
        for ch in channels:
            ch["is_default"] = False

    new_channel = {
        "name": channel_data.name,
        "api_url": channel_data.api_url,
        "auth_token": channel_data.auth_token,
        "is_default": channel_data.is_default,
        "default_group": channel_data.default_group,
        "groups": channel_data.groups
    }
    channels.append(new_channel)

    config_manager.save_notification_channels(channels)
    return NotificationChannelResponse(**new_channel)

@router.put("/{channel_name}", response_model=NotificationChannelResponse)
async def update_channel(
    channel_name: str,
    channel_data: NotificationChannelUpdate,
    current_user: User = Depends(get_current_user)
):
    """更新通知渠道（需要认证）"""
    channels = config_manager.get_notification_channels()

    target = None
    for ch in channels:
        if ch["name"] == channel_name:
            target = ch
            break

    if not target:
        raise HTTPException(status_code=404, detail=f"渠道 '{channel_name}' 不存在")

    if channel_data.name is not None and channel_data.name != channel_name:
        if any(ch["name"] == channel_data.name for ch in channels):
            raise HTTPException(status_code=400, detail=f"渠道名称 '{channel_data.name}' 已存在")
        target["name"] = channel_data.name

    if channel_data.api_url is not None:
        target["api_url"] = channel_data.api_url
    if channel_data.auth_token is not None:
        target["auth_token"] = channel_data.auth_token
    if channel_data.is_default is not None and channel_data.is_default:
        for ch in channels:
            ch["is_default"] = False
        target["is_default"] = True
    if channel_data.default_group is not None:
        target["default_group"] = channel_data.default_group
    if channel_data.groups is not None:
        target["groups"] = channel_data.groups

    config_manager.save_notification_channels(channels)
    return NotificationChannelResponse(**target)

@router.delete("/{channel_name}")
async def delete_channel(
    channel_name: str,
    current_user: User = Depends(get_current_user)
):
    """删除通知渠道（需要认证）"""
    channels = config_manager.get_notification_channels()

    target = None
    for ch in channels:
        if ch["name"] == channel_name:
            target = ch
            break

    if not target:
        raise HTTPException(status_code=404, detail=f"渠道 '{channel_name}' 不存在")

    if target.get("is_default") and len(channels) <= 1:
        raise HTTPException(status_code=400, detail="不能删除唯一的默认渠道")

    channels.remove(target)
    if target.get("is_default") and channels:
        channels[0]["is_default"] = True

    config_manager.save_notification_channels(channels)
    return {"message": f"渠道 '{channel_name}' 已删除"}

@router.get("/default", response_model=NotificationChannelResponse)
async def get_default_channel(
    current_user: User = Depends(get_current_user)
):
    """获取默认通知渠道（需要认证）"""
    channel = config_manager.get_default_channel()
    if not channel:
        raise HTTPException(status_code=404, detail="未配置任何通知渠道")
    return NotificationChannelResponse(
        name=channel["name"],
        api_url=channel["api_url"],
        auth_token=channel.get("auth_token", ""),
        is_default=channel.get("is_default", False),
        default_group=channel.get("default_group", "yes"),
        groups=channel.get("groups", ["yes"])
    )
