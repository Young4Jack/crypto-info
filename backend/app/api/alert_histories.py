"""预警历史 API 路由"""
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from pydantic import BaseModel
from app.database import get_db
from app.models.alert_history import AlertHistory, AlertHistoryStatus
from app.models.alert import PriceAlert
from app.models.cryptocurrency import Cryptocurrency
from app.api.deps import get_current_user
from app.models.user import User

router = APIRouter(prefix="/api/alert-histories", tags=["预警历史"])

class AlertHistoryResponse(BaseModel):
    """预警历史响应"""
    id: int
    alert_id: int
    crypto_symbol: str
    crypto_name: str
    alert_type: str
    threshold_price: float
    trigger_price: float
    status: str
    notification_sent: Optional[str] = None
    created_at: str

@router.get("/", response_model=List[AlertHistoryResponse])
async def get_alert_histories(
    skip: int = Query(0, description="跳过记录数"),
    limit: int = Query(50, description="返回记录数"),
    alert_id: Optional[int] = Query(None, description="预警规则ID"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """获取当前用户的预警历史"""
    query = db.query(AlertHistory).filter(
        AlertHistory.user_id == current_user.id
    )
    
    if alert_id:
        query = query.filter(AlertHistory.alert_id == alert_id)
    
    histories = query.order_by(AlertHistory.created_at.desc()).offset(skip).limit(limit).all()
    
    result = []
    for history in histories:
        # 获取币种信息
        crypto = db.query(Cryptocurrency).filter(
            Cryptocurrency.id == history.crypto_id
        ).first()
        
        result.append(AlertHistoryResponse(
            id=history.id,
            alert_id=history.alert_id,
            crypto_symbol=crypto.symbol if crypto else "Unknown",
            crypto_name=crypto.name if crypto else "Unknown",
            alert_type=history.alert_type,
            threshold_price=history.threshold_price,
            trigger_price=history.trigger_price,
            status=history.status.value,
            notification_sent=history.notification_sent.isoformat() if history.notification_sent else None,
            created_at=history.created_at.isoformat() if history.created_at else None
        ))
    
    return result

@router.get("/{history_id}", response_model=AlertHistoryResponse)
async def get_alert_history(
    history_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """根据ID获取预警历史"""
    history = db.query(AlertHistory).filter(
        AlertHistory.id == history_id,
        AlertHistory.user_id == current_user.id
    ).first()
    
    if not history:
        raise HTTPException(status_code=404, detail="预警历史不存在")
    
    # 获取币种信息
    crypto = db.query(Cryptocurrency).filter(
        Cryptocurrency.id == history.crypto_id
    ).first()
    
    return AlertHistoryResponse(
        id=history.id,
        alert_id=history.alert_id,
        crypto_symbol=crypto.symbol if crypto else "Unknown",
        crypto_name=crypto.name if crypto else "Unknown",
        alert_type=history.alert_type,
        threshold_price=history.threshold_price,
        trigger_price=history.trigger_price,
        status=history.status.value,
        notification_sent=history.notification_sent.isoformat() if history.notification_sent else None,
        created_at=history.created_at.isoformat() if history.created_at else None
    )

@router.delete("/{history_id}")
async def delete_alert_history(
    history_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """删除预警历史"""
    history = db.query(AlertHistory).filter(
        AlertHistory.id == history_id,
        AlertHistory.user_id == current_user.id
    ).first()
    
    if not history:
        raise HTTPException(status_code=404, detail="预警历史不存在")
    
    db.delete(history)
    db.commit()
    
    return {"message": "预警历史已删除"}

@router.delete("/")
async def clear_alert_histories(
    alert_id: Optional[int] = Query(None, description="预警规则ID"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """清空预警历史"""
    query = db.query(AlertHistory).filter(
        AlertHistory.user_id == current_user.id
    )
    
    if alert_id:
        query = query.filter(AlertHistory.alert_id == alert_id)
    
    deleted_count = query.delete()
    db.commit()
    
    return {"message": f"已删除 {deleted_count} 条预警历史记录"}