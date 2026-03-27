"""预警引擎服务"""
from typing import Dict, List
from sqlalchemy.orm import Session
from app.database import SessionLocal
from app.models.alert import PriceAlert, AlertType
from app.models.cryptocurrency import Cryptocurrency
from app.services.notification_service import send_price_alert
from app.config_manager import config_manager

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
        # 注意：这里应该根据用户ID来过滤，避免检查所有用户的预警
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
                
                # 检查是否触发预警
                should_trigger = False
                
                if alert.alert_type == AlertType.ABOVE and current_price > alert.threshold_price:
                    should_trigger = True
                elif alert.alert_type == AlertType.BELOW and current_price < alert.threshold_price:
                    should_trigger = True
                
                if should_trigger:
                    
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
                        # 标记预警为已触发（设置 triggered_at 或禁用）
                        from datetime import datetime
                        alert.triggered_at = datetime.now(config_manager.get_timezone())
                        alert.is_active = False  # 避免重复触发
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
    webhook_url: str
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
    
    Returns:
        PriceAlert: 创建的预警规则
    """
    alert = PriceAlert(
        user_id=user_id,
        crypto_id=crypto_id,
        alert_type=alert_type,
        threshold_price=threshold_price,
        webhook_url=webhook_url,
        is_active=True
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