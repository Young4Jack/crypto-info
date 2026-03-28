"""预警引擎服务"""
from typing import Dict, List
from sqlalchemy.orm import Session
from app.database import SessionLocal
from app.models.alert import PriceAlert, AlertType
from app.models.cryptocurrency import Cryptocurrency
from app.services.notification_service import send_price_alert
from app.config_manager import config_manager
from datetime import datetime, timedelta

async def check_price_alerts(prices: Dict[str, float], user_id: int = None):
    """
    检查价格预警并触发通知
    
    Args:
        prices: 价格字典 {symbol: price}
        user_id: 用户ID（可选，如果提供则只检查该用户的预警）
    """
    if not prices:
        return
    
    db = SessionLocal()
    try:
        # 获取所有激活的预警规则（只检查指定用户的预警）
        query = db.query(PriceAlert).filter(
            PriceAlert.is_active == True
        )
        
        # 如果提供了用户ID，则只检查该用户的预警
        if user_id:
            query = query.filter(PriceAlert.user_id == user_id)
        
        active_alerts = query.all()
        
        if not active_alerts:
            return
        
        triggered_count = 0
        now = datetime.now(config_manager.get_timezone())
        
        for alert in active_alerts:
            try:
                # 获取对应的币种信息
                crypto = db.query(Cryptocurrency).filter(
                    Cryptocurrency.id == alert.crypto_id
                ).first()
                
                if not crypto:
                    continue
                
                # 获取当前价格
                current_price = prices.get(crypto.symbol)
                if current_price is None:
                    continue
                
                # 检查通知次数限制
                if alert.notified_count >= alert.max_notifications:
                    # 达到最大通知次数，标记为完成
                    alert.is_active = False
                    db.commit()
                    continue
                
                # 检查时间间隔
                time_since_last = None
                if alert.last_triggered_at is not None:
                    time_since_last = (now - alert.last_triggered_at).total_seconds() / 60
                
                # 处理空值陷阱：last_triggered_at 为 NULL 时，视为立即触发
                should_notify = False
                if alert.last_triggered_at is None:
                    should_notify = True
                elif time_since_last is not None and time_since_last >= alert.interval_minutes:
                    should_notify = True
                
                if should_notify:
                    # 根据 is_continuous 区分模式1和模式2
                    if alert.is_continuous:
                        # 模式2：持续条件预警 - 每次达到时间间隔后，必须重新比对最新价格
                        # 检查价格条件是否仍然满足
                        should_trigger = False
                        if alert.alert_type == AlertType.ABOVE and current_price > alert.threshold_price:
                            should_trigger = True
                        elif alert.alert_type == AlertType.BELOW and current_price < alert.threshold_price:
                            should_trigger = True
                        elif alert.alert_type == AlertType.AMPLITUDE:
                            # 振幅预警
                            if alert.base_price and alert.threshold_value:
                                amplitude = abs(current_price - alert.base_price) / alert.base_price * 100
                                should_trigger = amplitude >= alert.threshold_value
                        elif alert.alert_type == AlertType.PERCENT_UP:
                            # 单向涨幅百分比
                            if alert.base_price and alert.threshold_value:
                                percent_change = (current_price - alert.base_price) / alert.base_price * 100
                                should_trigger = percent_change >= alert.threshold_value
                        elif alert.alert_type == AlertType.PERCENT_DOWN:
                            # 单向跌幅百分比
                            if alert.base_price and alert.threshold_value:
                                percent_change = (alert.base_price - current_price) / alert.base_price * 100
                                should_trigger = percent_change >= alert.threshold_value
                        
                        if not should_trigger:
                            should_notify = False
                    else:
                        # 模式1：普通预警带重复提醒 - 第一次触发后，后续的重复通知绝对不请求 API 检查最新价格
                        # 仅凭时间间隔无脑发
                        should_notify = True
                
                if should_notify:
                    # 构造预警参数
                    direction = "高于" if alert.alert_type == AlertType.ABOVE else "低于"
                    title = f"【价格预警】{crypto.name} 触发阈值"
                    description = "当前价格已达到设定的预警条件"
                    content = f"您监控的 {crypto.name} 当前价格为 {current_price}，已{direction}设定的阈值 {alert.threshold_price}。"
                    
                    # 发送 Webhook 通知
                    from app.services.notification_service import send_webhook_alert
                    try:
                        await send_webhook_alert(title, description, content, user_id=alert.user_id)
                        success = True
                    except Exception:
                        success = False
                    
                    if success:
                        # 更新预警记录
                        alert.notified_count += 1
                        alert.last_triggered_at = now
                        
                        # 检查是否达到最大通知次数
                        if alert.notified_count >= alert.max_notifications:
                            alert.is_active = False
                        
                        db.commit()
                        triggered_count += 1
                
            except Exception:
                continue
        
    finally:
        db.close()

def get_user_alerts(db: Session, user_id: int) -> List[PriceAlert]:
    """
    获取用户的预警规则
    
    Args:
        db: 数据库会话
        user_id: 用户ID
    
    Returns:
        List[PriceAlert]: 预警规则列表
    """
    return db.query(PriceAlert).filter(
        PriceAlert.user_id == user_id
    ).all()

def create_alert(
    db: Session,
    user_id: int,
    crypto_id: int,
    alert_type: AlertType,
    threshold_price: float,
    webhook_url: str = None,
    base_price: float = None,
    threshold_value: float = None,
    is_continuous: bool = False,
    interval_minutes: int = 5,
    max_notifications: int = 1
) -> PriceAlert:
    """
    创建新的预警规则
    
    Args:
        db: 数据库会话
        user_id: 用户ID
        crypto_id: 币种ID
        alert_type: 预警类型
        threshold_price: 阈值价格
        webhook_url: Webhook URL
        base_price: 基础价格（用于百分比和振幅预警）
        threshold_value: 阈值数值（用于百分比和振幅预警）
        is_continuous: 是否为持续预警模式
        interval_minutes: 两次通知之间的间隔时间(分钟)
        max_notifications: 最大通知次数限制
    
    Returns:
        PriceAlert: 创建的预警规则
    """
    tz = config_manager.get_timezone()

    alert = PriceAlert(
        user_id=user_id,
        crypto_id=crypto_id,
        alert_type=alert_type,
        threshold_price=threshold_price,
        webhook_url=webhook_url,
        is_active=True,
        base_price=base_price,
        threshold_value=threshold_value,
        is_continuous=is_continuous,
        interval_minutes=interval_minutes,
        max_notifications=max_notifications,
        notified_count=0,
        created_at=datetime.now(tz)
    )
    
    db.add(alert)
    db.commit()
    db.refresh(alert)
    
    return alert

def update_alert(
    db: Session,
    alert_id: int,
    user_id: int,
    **kwargs
) -> PriceAlert:
    """
    更新预警规则
    
    Args:
        db: 数据库会话
        alert_id: 预警ID
        user_id: 用户ID
        **kwargs: 要更新的字段
    
    Returns:
        PriceAlert: 更新后的预警规则
    """
    alert = db.query(PriceAlert).filter(
        PriceAlert.id == alert_id,
        PriceAlert.user_id == user_id
    ).first()
    
    if not alert:
        raise ValueError("预警规则不存在")
    
    for key, value in kwargs.items():
        if hasattr(alert, key):
            setattr(alert, key, value)
    
    db.commit()
    db.refresh(alert)
    
    return alert

def delete_alert(db: Session, alert_id: int, user_id: int) -> bool:
    """
    删除预警规则
    
    Args:
        db: 数据库会话
        alert_id: 预警ID
        user_id: 用户ID
    
    Returns:
        bool: 是否删除成功
    """
    alert = db.query(PriceAlert).filter(
        PriceAlert.id == alert_id,
        PriceAlert.user_id == user_id
    ).first()
    
    if not alert:
        return False
    
    db.delete(alert)
    db.commit()
    
    return True