"""预警引擎服务"""
from typing import Dict, List
from sqlalchemy.orm import Session
from app.database import SessionLocal
from app.models.alert import PriceAlert, AlertType
from app.models.cryptocurrency import Cryptocurrency
from app.services.notification_service import send_price_alert
from app.config_manager import config_manager
from datetime import datetime, timedelta
import logging

logger = logging.getLogger(__name__)

async def check_price_alerts(prices: Dict[str, float], user_id: int = None):
    if not prices:
        return
    
    db = SessionLocal()
    try:
        query = db.query(PriceAlert).filter(PriceAlert.is_active == True)
        if user_id:
            query = query.filter(PriceAlert.user_id == user_id)
        
        active_alerts = query.all()
        if not active_alerts:
            return
        
        triggered_count = 0
        now_aware = datetime.now(config_manager.get_timezone())
        now_naive = now_aware.replace(tzinfo=None)
        
        for alert in active_alerts:
            try:
                crypto = db.query(Cryptocurrency).filter(Cryptocurrency.id == alert.crypto_id).first()
                if not crypto:
                    continue
                
                current_price = prices.get(crypto.symbol)
                if current_price is None:
                    continue
                
                if alert.notified_count >= alert.max_notifications:
                    alert.is_active = False
                    db.commit()
                    continue
                
                # 安全计算时间差
                time_since_last = None
                if alert.last_triggered_at is not None:
                    last_triggered_naive = alert.last_triggered_at.replace(tzinfo=None)
                    time_since_last = (now_naive - last_triggered_naive).total_seconds() / 60
                
                should_notify = False
                
                if not alert.is_continuous and alert.notified_count > 0:
                    if time_since_last is not None and time_since_last >= alert.interval_minutes:
                        should_notify = True
                else:
                    time_condition_met = False
                    if alert.last_triggered_at is None:
                        time_condition_met = True
                    elif time_since_last is not None and time_since_last >= alert.interval_minutes:
                        time_condition_met = True
                        
                    if time_condition_met:
                        if alert.alert_type == AlertType.ABOVE:
                            should_notify = current_price > alert.threshold_price
                        elif alert.alert_type == AlertType.BELOW:
                            should_notify = current_price < alert.threshold_price
                        elif alert.alert_type == AlertType.AMPLITUDE:
                            if alert.base_price and alert.threshold_value:
                                amplitude = abs(current_price - alert.base_price) / alert.base_price * 100
                                should_notify = amplitude >= alert.threshold_value
                        elif alert.alert_type == AlertType.PERCENT_UP:
                            if alert.base_price and alert.threshold_value:
                                percent_change = (current_price - alert.base_price) / alert.base_price * 100
                                should_notify = percent_change >= alert.threshold_value
                        elif alert.alert_type == AlertType.PERCENT_DOWN:
                            if alert.base_price and alert.threshold_value:
                                percent_change = (alert.base_price - current_price) / alert.base_price * 100
                                should_notify = percent_change >= alert.threshold_value
                
                if should_notify:
                    direction = "高于" if alert.alert_type == AlertType.ABOVE else "低于"
                    title = f"【价格预警】{crypto.name} 触发阈值"
                    description = "当前价格已达到设定的预警条件"
                    content = f"您监控的 {crypto.name} 当前价格为 {current_price}，已{direction}设定的阈值 {alert.threshold_price}。"
                    
                    from app.services.notification_service import send_webhook_alert
                    try:
                        await send_webhook_alert(title, description, content, user_id=alert.user_id)
                        success = True
                    except Exception as e:
                        logger.error(f"主动检查发送通知失败: {e}")
                        success = False
                    
                    if success:
                        alert.notified_count += 1
                        alert.last_triggered_at = now_aware
                        if alert.notified_count >= alert.max_notifications:
                            alert.is_active = False
                        db.commit()
                        triggered_count += 1
                
            except Exception as e:
                logger.error(f"单条预警规则检查异常: {e}")
                continue
        
    finally:
        db.close()

def get_user_alerts(db: Session, user_id: int) -> List[PriceAlert]:
    return db.query(PriceAlert).filter(PriceAlert.user_id == user_id).all()

def create_alert(
    db: Session, user_id: int, crypto_id: int, alert_type: AlertType,
    threshold_price: float, webhook_url: str = None, base_price: float = None,
    threshold_value: float = None, is_continuous: bool = False,
    interval_minutes: int = 5, max_notifications: int = 1
) -> PriceAlert:
    tz = config_manager.get_timezone()
    alert = PriceAlert(
        user_id=user_id, crypto_id=crypto_id, alert_type=alert_type,
        threshold_price=threshold_price, webhook_url=webhook_url,
        is_active=True, base_price=base_price, threshold_value=threshold_value,
        is_continuous=is_continuous, interval_minutes=interval_minutes,
        max_notifications=max_notifications, notified_count=0,
        created_at=datetime.now(tz)
    )
    db.add(alert)
    db.commit()
    db.refresh(alert)
    return alert

def update_alert(db: Session, alert_id: int, user_id: int, **kwargs) -> PriceAlert:
    alert = db.query(PriceAlert).filter(
        PriceAlert.id == alert_id, PriceAlert.user_id == user_id
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
    alert = db.query(PriceAlert).filter(
        PriceAlert.id == alert_id, PriceAlert.user_id == user_id
    ).first()
    if not alert:
        return False
    db.delete(alert)
    db.commit()
    return True