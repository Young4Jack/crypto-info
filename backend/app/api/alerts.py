"""预警规则 API 路由"""
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel
from app.database import get_db
from app.models.alert import PriceAlert, AlertType
from app.models.cryptocurrency import Cryptocurrency
from app.api.deps import get_current_user
from app.models.user import User
from app.services.alert_service import create_alert, update_alert, delete_alert, get_user_alerts
from app.utils.crypto_utils import extract_coin_name_from_symbol, get_coin_full_name
from datetime import datetime
from app.config_manager import config_manager

router = APIRouter(prefix="/api/alerts", tags=["预警管理"])

class AlertCreate(BaseModel):
    """创建预警规则请求"""
    crypto_symbol: str
    alert_type: str  # "above" 或 "below"
    threshold_price: float
    webhook_url: Optional[str] = None

class AlertUpdate(BaseModel):
    """更新预警规则请求"""
    alert_type: Optional[str] = None
    threshold_price: Optional[float] = None
    webhook_url: Optional[str] = None
    is_active: Optional[bool] = None

class AlertResponse(BaseModel):
    """预警规则响应"""
    id: int
    crypto_id: int
    crypto_symbol: str
    crypto_name: str
    alert_type: str
    threshold_price: float
    is_active: bool
    triggered_at: Optional[str] = None
    created_at: str

@router.get("/", response_model=List[AlertResponse])
async def get_alerts(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """获取当前用户的所有预警规则"""
    alerts = get_user_alerts(db, current_user.id)
    
    result = []
    for alert in alerts:
        # 获取对应的币种信息
        crypto = db.query(Cryptocurrency).filter(
            Cryptocurrency.id == alert.crypto_id
        ).first()
        
        result.append(AlertResponse(
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
        ))
    
    return result

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
    
    # 验证预警类型
    if alert_data.alert_type not in ["above", "below"]:
        raise HTTPException(status_code=400, detail="预警类型必须是 'above' 或 'below'")
    
    # 创建预警规则
    alert_type = AlertType.ABOVE if alert_data.alert_type == "above" else AlertType.BELOW
    
    alert = create_alert(
        db=db,
        user_id=current_user.id,
        crypto_id=crypto.id,
        alert_type=alert_type,
        threshold_price=alert_data.threshold_price,
        webhook_url=alert_data.webhook_url
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
        created_at=alert.created_at.isoformat() if alert.created_at else None
    )

@router.put("/{alert_id}", response_model=AlertResponse)
async def update_alert_rule(
    alert_id: int,
    alert_data: AlertUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """更新预警规则"""
    # 验证预警类型
    if alert_data.alert_type and alert_data.alert_type not in ["above", "below"]:
        raise HTTPException(status_code=400, detail="预警类型必须是 'above' 或 'below'")
    
    # 准备更新数据
    update_data = {}
    if alert_data.alert_type:
        update_data["alert_type"] = AlertType.ABOVE if alert_data.alert_type == "above" else AlertType.BELOW
    if alert_data.threshold_price is not None:
        update_data["threshold_price"] = alert_data.threshold_price
    if alert_data.webhook_url is not None:
        update_data["webhook_url"] = alert_data.webhook_url
    if alert_data.is_active is not None:
        update_data["is_active"] = alert_data.is_active
    
    # 更新预警规则
    alert = update_alert(
        db=db,
        alert_id=alert_id,
        user_id=current_user.id,
        **update_data
    )
    
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

