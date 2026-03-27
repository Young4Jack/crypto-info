"""通知服务"""
import httpx
import logging
from typing import Dict, Any, Optional
from datetime import datetime
from sqlalchemy.orm import Session
from app.database import SessionLocal
from app.models.system_setting import NotificationSetting
from app.config_manager import config_manager

logger = logging.getLogger(__name__)

async def send_webhook_alert(title: str, description: str, content: str, user_id: int = None):
    """
    发送 Webhook 预警通知
    
    Args:
        title: 预警标题
        description: 预警描述
        content: 预警详细内容
        user_id: 用户ID（用于获取通知配置）
    """
    # 如果没有指定用户ID，记录警告并中止
    if user_id is None:
        logger.warning("未指定用户ID，无法发送预警通知")
        return
    
    # 查询用户的通知设置
    db = SessionLocal()
    try:
        setting = db.query(NotificationSetting).filter(
            NotificationSetting.user_id == user_id
        ).first()
        
        if not setting or not setting.api_url:
            logger.warning(f"用户 {user_id} 未配置通知设置，中止推送")
            return
        
        # 使用数据库中的配置构建请求
        url = setting.api_url
        headers = {}
        if setting.auth_token:
            headers["Authorization"] = setting.auth_token
        
        data = {
            "title": title,
            "description": description,
            "channel": setting.channel or "email",
            "content": content
        }
        
        async with httpx.AsyncClient() as client:
            response = await client.post(url, headers=headers, data=data, timeout=10.0)
            response.raise_for_status()
            logger.info(f"预警推送成功: {response.status_code}")
    except Exception as e:
        logger.error(f"预警推送失败: {str(e)}")
    finally:
        db.close()

def create_alert_payload(
    crypto_symbol: str,
    crypto_name: str,
    alert_type: str,
    threshold_price: float,
    current_price: float,
    triggered_at: datetime
) -> Dict[str, Any]:
    """
    创建预警通知数据
    
    Args:
        crypto_symbol: 币种符号
        crypto_name: 币种名称
        alert_type: 预警类型 (above/below)
        threshold_price: 阈值价格
        current_price: 当前价格
        triggered_at: 触发时间
    
    Returns:
        Dict: 通知数据
    """
    direction = "高于" if alert_type == "above" else "低于"
    
    return {
        "event": "price_alert",
        "crypto": {
            "symbol": crypto_symbol,
            "name": crypto_name
        },
        "alert": {
            "type": alert_type,
            "threshold_price": threshold_price,
            "current_price": current_price,
            "direction": direction,
            "triggered_at": triggered_at.isoformat()
        },
        "message": f"{crypto_name} ({crypto_symbol}) 价格 {direction} 阈值 {threshold_price}，当前价格 {current_price}",
        "timestamp": datetime.now(config_manager.get_timezone()).isoformat()
    }

async def send_price_alert(
    webhook_url: str,
    crypto_symbol: str,
    crypto_name: str,
    alert_type: str,
    threshold_price: float,
    current_price: float,
    user_id: int = None
) -> bool:
    """
    发送价格预警通知
    
    Args:
        webhook_url: Webhook URL（此参数保留但不使用）
        crypto_symbol: 币种符号
        crypto_name: 币种名称
        alert_type: 预警类型
        threshold_price: 阈值价格
        current_price: 当前价格
        user_id: 用户ID
    
    Returns:
        bool: 发送是否成功
    """
    direction = "高于" if alert_type == "above" else "低于"
    
    title = f"【价格预警】{crypto_name} 触发阈值"
    description = "当前价格已达到设定的预警条件"
    content = f"您监控的 {crypto_name} 当前价格为 {current_price}，已{direction}设定的阈值 {threshold_price}。"
    
    try:
        await send_webhook_alert(title, description, content, user_id=user_id)
        return True
    except Exception as e:
        logger.error(f"发送价格预警失败: {str(e)}")
        return False
