"""通知服务"""
import httpx
import logging
from typing import Dict, Any, Optional
from datetime import datetime
from app.config_manager import config_manager

logger = logging.getLogger(__name__)

MAX_RETRY_COUNT = 3

async def send_webhook_alert(title: str, description: str, content: str, user_id: int = None, channel_config: Dict[str, Any] = None):
    """
    发送 Webhook 预警通知
    
    Args:
        title: 预警标题
        description: 预警描述
        content: 预警详细内容
        user_id: 用户ID（保留参数以兼容原有调用）
        channel_config: 渠道配置字典 {api_url, auth_token, group}，不传则使用默认渠道
    
    Raises:
        Exception: 所有重试均失败时抛出异常
    """
    if channel_config:
        api_url = channel_config.get("api_url", "")
        auth_token = channel_config.get("auth_token", "")
        group = channel_config.get("group", "yes")
    else:
        default = config_manager.get_default_channel()
        if not default:
            logger.warning("未配置任何通知渠道，中止推送")
            raise ValueError("未配置任何通知渠道")
        api_url = default.get("api_url", "")
        auth_token = default.get("auth_token", "")
        group = default.get("default_group", "yes")

    if not api_url:
        logger.warning("渠道 api_url 为空，中止推送")
        raise ValueError("通知渠道未配置 API 地址")

    headers = {}
    if auth_token:
        headers["Authorization"] = auth_token

    data = {
        "title": title,
        "description": description,
        "channel": group,
        "content": content
    }

    last_error = None
    for attempt in range(1, MAX_RETRY_COUNT + 1):
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(api_url, headers=headers, json=data, timeout=10.0)
                response.raise_for_status()
                logger.info(f"预警推送成功 (第{attempt}次尝试): {response.status_code}")
                return
        except Exception as e:
            last_error = e
            if attempt < MAX_RETRY_COUNT:
                logger.warning(f"预警推送失败 (第{attempt}/{MAX_RETRY_COUNT}次): {e}")
            else:
                logger.error(f"预警推送彻底失败 (已重试{MAX_RETRY_COUNT}次): {e}")

    raise last_error

async def send_failure_alert(crypto_name: str, error_msg: str):
    """发送通知失败的系统告警（复用同一个 webhook 接口）"""
    default = config_manager.get_default_channel()
    if not default:
        return

    api_url = default.get("api_url", "")
    if not api_url:
        return

    headers = {}
    auth_token = default.get("auth_token", "")
    if auth_token:
        headers["Authorization"] = auth_token

    data = {
        "title": "【系统告警】预警通知推送失败",
        "description": "预警通知推送失败，已自动停用相关预警规则",
        "channel": default.get("default_group", "yes"),
        "content": f"监控的 {crypto_name} 触发预警后，通知推送连续失败（已重试{MAX_RETRY_COUNT}次）。错误信息：{error_msg}。该预警已被自动停用，请检查通知配置。"
    }

    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(api_url, headers=headers, json=data, timeout=10.0)
            response.raise_for_status()
            logger.info("系统告警发送成功")
    except Exception as e:
        logger.error(f"系统告警也发送失败: {e}")

def create_alert_payload(
    crypto_symbol: str,
    crypto_name: str,
    alert_type: str,
    threshold_price: float,
    current_price: float,
    triggered_at: datetime
) -> Dict[str, Any]:
    """创建预警通知数据"""
    direction_map = {
        "above": "高于",
        "below": "低于",
        "amplitude": "振幅达到",
        "percent_up": "涨幅达到",
        "percent_down": "跌幅达到",
    }
    direction = direction_map.get(alert_type, "触发")

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
    """发送价格预警通知（兼容旧接口）"""
    direction_map = {
        "above": "高于",
        "below": "低于",
        "amplitude": "振幅达到",
        "percent_up": "涨幅达到",
        "percent_down": "跌幅达到",
    }
    direction = direction_map.get(alert_type, "触发")

    title = f"【价格预警】{crypto_name} 触发阈值"
    description = "当前价格已达到设定的预警条件"
    content = f"您监控的 {crypto_name} 当前价格为 {current_price}，已{direction}设定的阈值 {threshold_price}。"

    try:
        await send_webhook_alert(title, description, content, user_id=user_id)
        return True
    except Exception as e:
        logger.error(f"发送价格预警失败: {str(e)}")
        return False
