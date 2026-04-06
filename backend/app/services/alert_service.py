"""预警引擎服务"""
from typing import Dict, List
from sqlalchemy.orm import Session
from app.models.alert import PriceAlert, AlertType
from app.config_manager import config_manager
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

def get_user_alerts(db: Session, user_id: int) -> List[PriceAlert]:
    return db.query(PriceAlert).filter(PriceAlert.user_id == user_id).order_by(PriceAlert.sort_order.asc()).all()

def create_alert(
    db: Session, user_id: int, crypto_id: int, alert_type: AlertType,
    threshold_price: float, webhook_url: str = None, base_price: float = None,
    threshold_value: float = None, is_continuous: bool = False,
    interval_minutes: int = 5, max_notifications: int = 1,
    sort_order: int = 0, notification_channel: str = None,
    notification_group: str = None
) -> PriceAlert:
    tz = config_manager.get_timezone()
    alert = PriceAlert(
        user_id=user_id, crypto_id=crypto_id, alert_type=alert_type,
        threshold_price=threshold_price, webhook_url=webhook_url,
        is_active=True, base_price=base_price, threshold_value=threshold_value,
        is_continuous=is_continuous, interval_minutes=interval_minutes,
        max_notifications=max_notifications, notified_count=0,
        sort_order=sort_order,
        notification_channel=notification_channel,
        notification_group=notification_group,
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