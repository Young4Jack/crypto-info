"""通知服务"""
import httpx
import logging
from typing import Dict, Any, Optional
from datetime import datetime
from app.config_manager import config_manager

logger = logging.getLogger(__name__)

async def send_webhook_alert(title: str, description: str, content: str, user_id: int = None):
    """
    发送 Webhook 预警通知 (完全从 config.json 读取配置，不再依赖数据库表)
    
    Args:
        title: 预警标题
        description: 预警描述
        content: 预警详细内容
        user_id: 用户ID（保留参数以兼容原有调用，但在此逻辑中不再使用）
    """
    try:
        # 1. 直接通过 config_manager 获取字典配置
        setting = config_manager.get_notification_settings()
        
        api_url = setting.get("api_url")
        if not api_url:
            logger.warning("配置文件中未设置 api_url，中止推送")
            raise ValueError("未配置通知 API 地址")
        
        # 2. 组装请求头
        headers = {}
        auth_token = setting.get("auth_token")
        if auth_token:
            headers["Authorization"] = auth_token
        
        # 3. 组装请求体
        data = {
            "title": title,
            "description": description,
            "channel": setting.get("channel", "yes"),  # 默认使用你配置中的 channel
            "content": content
        }
        
        # 4. 执行异步推送 (使用 json=data 确保是 Application/JSON 格式)
        async with httpx.AsyncClient() as client:
            response = await client.post(api_url, headers=headers, json=data, timeout=10.0)
            response.raise_for_status()
            logger.info(f"预警推送成功: {response.status_code}")
            
    except Exception as e:
        logger.error(f"预警推送失败: {str(e)}")
        # 必须抛出异常让 alert_service 捕获，确保 success = False
        # 这样如果推送失败，数据库里就不会错误地将预警标记为“已触发”
        raise e

def create_alert_payload(
    crypto_symbol: str,
    crypto_name: str,
    alert_type: str,
    threshold_price: float,
    current_price: float,
    triggered_at: datetime
) -> Dict[str, Any]:
    """创建预警通知数据"""
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
    """发送价格预警通知"""
    direction = "高于" if alert_type == "above" else "低于"
    
    title = f"【价格预警】{crypto_name} 触发阈值"
    description = "当前价格已达到设定的预警条件"
    content = f"您监控的 {crypto_name} 当前价格为 {current_price}，已{direction}设定的阈值 {threshold_price}。"
    
    try:
        await send_webhook_alert(title, description, content, user_id=user_id)
        return True
    except Exception as e:
        logger.error(f"发送价格预警逻辑失败: {str(e)}")
        return False