"""预警规则 API 路由"""
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import func
from pydantic import BaseModel
from app.database import get_db
from app.models.alert import PriceAlert, AlertType
from app.models.cryptocurrency import Cryptocurrency
from app.api.deps import get_current_user
from app.models.user import User
from app.services.alert_service import create_alert, update_alert, delete_alert, get_user_alerts
from app.services.price_service_refactored import fetch_crypto_prices
from app.utils.crypto_utils import extract_coin_name_from_symbol, get_coin_full_name
from datetime import datetime
from app.config_manager import config_manager

router = APIRouter(prefix="/api/alerts", tags=["预警管理"])

class AlertCreate(BaseModel):
    """创建预警规则请求"""
    crypto_symbol: str
    alert_type: str  # "above", "below", "amplitude", "percent_up", "percent_down"
    threshold_price: float
    webhook_url: Optional[str] = None
    # 新增字段
    base_price: Optional[float] = None
    threshold_value: Optional[float] = None
    is_continuous: Optional[bool] = False
    interval_minutes: Optional[int] = 5
    max_notifications: Optional[int] = 1

class AlertUpdate(BaseModel):
    """更新预警规则请求"""
    alert_type: Optional[str] = None
    threshold_price: Optional[float] = None
    webhook_url: Optional[str] = None
    is_active: Optional[bool] = None
    # 新增字段
    base_price: Optional[float] = None
    threshold_value: Optional[float] = None
    is_continuous: Optional[bool] = None
    interval_minutes: Optional[int] = None
    max_notifications: Optional[int] = None

class AlertResponse(BaseModel):
    """预警规则响应"""
    id: int
    crypto_id: int
    crypto_symbol: str
    crypto_name: str
    alert_type: str
    threshold_price: float
    current_price: Optional[float] = None
    is_active: bool
    triggered_at: Optional[str] = None
    created_at: str
    sort_order: int = 0
    # 新增字段
    base_price: Optional[float] = None
    threshold_value: Optional[float] = None
    is_continuous: bool = False
    interval_minutes: int = 5
    max_notifications: int = 1
    notified_count: int = 0
    last_triggered_at: Optional[str] = None

@router.get("/", response_model=List[AlertResponse])
async def get_alerts(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """获取当前用户的所有预警规则"""
    alerts = get_user_alerts(db, current_user.id)
    
    # 获取所有币种的当前价格
    try:
        current_prices = await fetch_crypto_prices()
    except Exception as e:
        current_prices = {}
    
    result = []
    for alert in alerts:
        # 获取对应的币种信息
        crypto = db.query(Cryptocurrency).filter(
            Cryptocurrency.id == alert.crypto_id
        ).first()
        
        # 获取当前价格
        current_price = current_prices.get(crypto.symbol, 0) if crypto else 0
        
        result.append(AlertResponse(
            id=alert.id,
            crypto_id=alert.crypto_id,
            crypto_symbol=crypto.symbol if crypto else "Unknown",
            crypto_name=crypto.name if crypto else "Unknown",
            alert_type=alert.alert_type.value,
            threshold_price=alert.threshold_price,
            current_price=current_price,
            webhook_url=alert.webhook_url,
            is_active=alert.is_active,
            triggered_at=alert.triggered_at.isoformat() if alert.triggered_at else None,
            created_at=alert.created_at.isoformat() if alert.created_at else None,
            sort_order=alert.sort_order or 0,
            # 新增字段
            base_price=alert.base_price,
            threshold_value=alert.threshold_value,
            is_continuous=alert.is_continuous,
            interval_minutes=alert.interval_minutes,
            max_notifications=alert.max_notifications,
            notified_count=alert.notified_count,
            last_triggered_at=alert.last_triggered_at.isoformat() if alert.last_triggered_at else None
        ))
    
    return result

class SortOrderItem(BaseModel):
    id: int
    sort_order: int

class SortOrderUpdate(BaseModel):
    items: List[SortOrderItem]

@router.put("/sort-order")
async def update_alerts_sort_order(
    update_data: SortOrderUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """批量更新预警规则排序"""
    for item in update_data.items:
        alert = db.query(PriceAlert).filter(
            PriceAlert.id == item.id,
            PriceAlert.user_id == current_user.id
        ).first()
        if alert:
            alert.sort_order = item.sort_order
    db.commit()
    return {"message": "排序已更新"}

@router.get("/{alert_id}", response_model=AlertResponse)
async def get_alert(
    alert_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """根据 ID 获取预警规则"""
    alert = db.query(PriceAlert).filter(
        PriceAlert.id == alert_id,
        PriceAlert.user_id == current_user.id
    ).first()
    
    if not alert:
        raise HTTPException(status_code=404, detail="预警规则不存在")
    
    # 获取对应的币种信息
    crypto = db.query(Cryptocurrency).filter(
        Cryptocurrency.id == alert.crypto_id
    ).first()
    
    return AlertResponse(
        id=alert.id,
        crypto_id=alert.crypto_id,
        crypto_symbol=crypto.symbol if crypto else "Unknown",
        crypto_name=crypto.name if crypto else "Unknown",
        alert_type=alert.alert_type.value,
        threshold_price=alert.threshold_price,
        webhook_url=alert.webhook_url,
        is_active=alert.is_active,
        triggered_at=alert.triggered_at.isoformat() if alert.triggered_at else None,
        created_at=alert.created_at.isoformat() if alert.created_at else None
    )

@router.post("/", response_model=AlertResponse)
async def create_alert_rule(
    alert_data: AlertCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """创建新的预警规则"""
    # 查找币种，如果不存在则自动创建
    crypto = db.query(Cryptocurrency).filter(
        Cryptocurrency.symbol == alert_data.crypto_symbol
    ).first()
    
    if not crypto:
        # 如果币种不存在，自动创建一个
        coin_name = extract_coin_name_from_symbol(alert_data.crypto_symbol)
        full_name = get_coin_full_name(coin_name)
        crypto = Cryptocurrency(
            symbol=alert_data.crypto_symbol,
            name=coin_name,
            display_name=full_name,
            is_active=True
        )
        db.add(crypto)
        db.commit()
        db.refresh(crypto)
    elif not crypto.is_active:
        # 如果币种存在但未激活，激活它
        crypto.is_active = True
        db.commit()
        db.refresh(crypto)
    
    # 验证预警类型（支持新类型）
    valid_alert_types = ["above", "below", "amplitude", "percent_up", "percent_down"]
    if alert_data.alert_type not in valid_alert_types:
        raise HTTPException(status_code=400, detail=f"预警类型必须是以下之一: {', '.join(valid_alert_types)}")
    
    # 创建预警规则
    alert_type = AlertType(alert_data.alert_type)
    
    # 获取当前价格作为base_price（如果未指定）
    base_price = alert_data.base_price
    if base_price is None and alert_data.alert_type in ["amplitude", "percent_up", "percent_down"]:
        try:
            current_prices = await fetch_crypto_prices()
            base_price = current_prices.get(crypto.symbol, 0)
        except Exception:
            base_price = 0
    
    # 计算threshold_value（如果未指定）
    threshold_value = alert_data.threshold_value
    if threshold_value is None:
        threshold_value = alert_data.threshold_price
    
    # 获取最大排序值+1，确保新项目排在最后
    max_sort = db.query(func.coalesce(func.max(PriceAlert.sort_order), 0)).filter(
        PriceAlert.user_id == current_user.id
    ).scalar()
    
    alert = create_alert(
        db=db,
        user_id=current_user.id,
        crypto_id=crypto.id,
        alert_type=alert_type,
        threshold_price=alert_data.threshold_price,
        webhook_url=alert_data.webhook_url,
        base_price=base_price,
        threshold_value=threshold_value,
        is_continuous=alert_data.is_continuous,
        interval_minutes=alert_data.interval_minutes,
        max_notifications=alert_data.max_notifications,
        sort_order=max_sort + 1
    )
    
    return AlertResponse(
        id=alert.id,
        crypto_id=alert.crypto_id,
        crypto_symbol=crypto.symbol,
        crypto_name=crypto.name,
        alert_type=alert.alert_type.value,
        threshold_price=alert.threshold_price,
        webhook_url=alert.webhook_url,
        is_active=alert.is_active,
        triggered_at=alert.triggered_at.isoformat() if alert.triggered_at else None,
        created_at=alert.created_at.isoformat() if alert.created_at else None,
        # 新增字段
        base_price=alert.base_price,
        threshold_value=alert.threshold_value,
        is_continuous=alert.is_continuous,
        interval_minutes=alert.interval_minutes,
        max_notifications=alert.max_notifications,
        notified_count=alert.notified_count,
        last_triggered_at=alert.last_triggered_at.isoformat() if alert.last_triggered_at else None
    )

@router.put("/{alert_id}", response_model=AlertResponse)
async def update_alert_rule(
    alert_id: int,
    alert_data: AlertUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """更新预警规则（支持全字段编辑与状态重置）"""
    valid_types = ["above", "below", "amplitude", "percent_up", "percent_down"]
    if alert_data.alert_type and alert_data.alert_type not in valid_types:
        raise HTTPException(status_code=400, detail="预警类型不合法")
    
    alert = db.query(PriceAlert).filter(
        PriceAlert.id == alert_id,
        PriceAlert.user_id == current_user.id
    ).first()
    
    if not alert:
        raise HTTPException(status_code=404, detail="预警规则不存在")
    
    update_data = {}
    if alert_data.alert_type:
        update_data["alert_type"] = AlertType(alert_data.alert_type)
    if alert_data.webhook_url is not None:
        update_data["webhook_url"] = alert_data.webhook_url
        
    # 【核心修改1】：同步更新阈值。防止用户修改了百分比，但后台还在用旧的百分比计算
    if alert_data.threshold_price is not None:
        update_data["threshold_price"] = alert_data.threshold_price
        update_data["threshold_value"] = alert_data.threshold_price
        
    # 【核心修改2】：开放编辑权限，允许更新模式、次数和间隔
    if alert_data.is_continuous is not None:
        update_data["is_continuous"] = alert_data.is_continuous
    if alert_data.interval_minutes is not None:
        update_data["interval_minutes"] = alert_data.interval_minutes
    if alert_data.max_notifications is not None:
        update_data["max_notifications"] = alert_data.max_notifications
    
    # 状态更新与重置逻辑
    if alert_data.is_active is not None:
        update_data["is_active"] = alert_data.is_active
        
        # 当被重新激活时，执行重置
        if alert_data.is_active is True and alert.is_active is False:
            tz = config_manager.get_timezone()
            update_data["notified_count"] = 0
            update_data["last_triggered_at"] = None
            update_data["created_at"] = datetime.now(tz)
            
            if alert_data.alert_type:
                current_type = AlertType(alert_data.alert_type)
            else:
                current_type = alert.alert_type
                
            if current_type in [AlertType.AMPLITUDE, AlertType.PERCENT_UP, AlertType.PERCENT_DOWN]:
                crypto = db.query(Cryptocurrency).filter(Cryptocurrency.id == alert.crypto_id).first()
                if crypto:
                    try:
                        current_prices = await fetch_crypto_prices()
                        current_price = current_prices.get(crypto.symbol, 0)
                        if current_price > 0:
                            update_data["base_price"] = current_price
                    except Exception:
                        pass
    
    alert = update_alert(
        db=db,
        alert_id=alert_id,
        user_id=current_user.id,
        **update_data
    )
    
    crypto = db.query(Cryptocurrency).filter(Cryptocurrency.id == alert.crypto_id).first()
    
    return AlertResponse(
        id=alert.id,
        crypto_id=alert.crypto_id,
        crypto_symbol=crypto.symbol if crypto else "Unknown",
        crypto_name=crypto.name if crypto else "Unknown",
        alert_type=alert.alert_type.value,
        threshold_price=alert.threshold_price,
        webhook_url=alert.webhook_url,
        is_active=alert.is_active,
        triggered_at=alert.triggered_at.isoformat() if alert.triggered_at else None,
        created_at=alert.created_at.isoformat() if alert.created_at else None
    )

@router.delete("/all")
async def delete_all_alerts(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """删除当前用户的所有预警规则"""
    count = db.query(PriceAlert).filter(
        PriceAlert.user_id == current_user.id
    ).delete()
    db.commit()
    return {"message": f"已删除 {count} 条预警规则"}

@router.delete("/{alert_id}")
async def delete_alert_rule(
    alert_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """删除预警规则"""
    # 获取预警规则
    alert = db.query(PriceAlert).filter(
        PriceAlert.id == alert_id,
        PriceAlert.user_id == current_user.id
    ).first()
    
    if not alert:
        raise HTTPException(status_code=404, detail="预警规则不存在")
    
    # 获取币种信息
    crypto = db.query(Cryptocurrency).filter(
        Cryptocurrency.id == alert.crypto_id
    ).first()
    
    # 删除预警规则
    db.delete(alert)
    db.commit()
    
    # 检查资产管理中是否还有该交易对，如果没有则删除币种
    if crypto:
        from app.models.asset import Asset
        from app.models.watchlist import Watchlist
        
        has_asset = db.query(Asset).filter(Asset.crypto_id == crypto.id).first()
        has_watchlist = db.query(Watchlist).filter(Watchlist.crypto_id == crypto.id).first()
        
        # 只有在三个表都彻底无人使用时，才安全删除币种字典
        if not has_asset and not has_watchlist:
            db.delete(crypto)
            db.commit()
            return {"message": "记录及冗余币种已删除"}
    
    return {"message": "记录已删除"}

