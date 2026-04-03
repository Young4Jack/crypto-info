"""资产 API 路由"""
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import func
from pydantic import BaseModel
from app.database import get_db
from app.models.asset import Asset
from app.models.cryptocurrency import Cryptocurrency
from app.api.deps import get_current_user
from app.models.user import User
from app.services.price_service_refactored import fetch_crypto_prices
from app.utils.crypto_utils import extract_coin_name_from_symbol, get_coin_full_name
from datetime import datetime
from app.config_manager import config_manager

router = APIRouter(prefix="/api/assets", tags=["资产管理"])

class AssetCreate(BaseModel):
    """创建资产请求"""
    crypto_symbol: str
    buy_price: float
    quantity: float
    notes: Optional[str] = None

class AssetUpdate(BaseModel):
    """更新资产请求"""
    buy_price: Optional[float] = None
    quantity: Optional[float] = None
    notes: Optional[str] = None

class AssetResponse(BaseModel):
    """资产响应"""
    id: int
    crypto_id: int
    crypto_symbol: str
    crypto_name: str
    buy_price: float
    quantity: float
    notes: Optional[str] = None
    total_value: float
    current_price: float = 0.0
    sort_order: int = 0
    created_at: str

@router.get("/", response_model=List[AssetResponse])
async def get_assets(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """获取当前用户的所有资产"""
    assets = db.query(Asset).filter(
        Asset.user_id == current_user.id
    ).order_by(Asset.sort_order.asc()).all()
    
    # 获取所有币种的当前价格
    try:
        current_prices = await fetch_crypto_prices()
    except Exception as e:
        current_prices = {}
    
    result = []
    for asset in assets:
        # 获取对应的币种信息
        crypto = db.query(Cryptocurrency).filter(
            Cryptocurrency.id == asset.crypto_id
        ).first()
        
        # 获取当前价格
        current_price = current_prices.get(crypto.symbol, 0) if crypto else 0
        
        result.append(AssetResponse(
            id=asset.id,
            crypto_id=asset.crypto_id,
            crypto_symbol=crypto.symbol if crypto else "Unknown",
            crypto_name=crypto.name if crypto else "Unknown",
            buy_price=asset.buy_price,
            quantity=asset.quantity,
            notes=asset.notes,
            total_value=asset.buy_price * asset.quantity,
            current_price=current_price,
            sort_order=asset.sort_order or 0,
            created_at=asset.created_at.isoformat() if asset.created_at else None
        ))
    
    return result

class SortOrderItem(BaseModel):
    id: int
    sort_order: int

class SortOrderUpdate(BaseModel):
    items: List[SortOrderItem]

@router.put("/sort-order")
async def update_assets_sort_order(
    update_data: SortOrderUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """批量更新资产排序"""
    for item in update_data.items:
        asset = db.query(Asset).filter(
            Asset.id == item.id,
            Asset.user_id == current_user.id
        ).first()
        if asset:
            asset.sort_order = item.sort_order
    db.commit()
    return {"message": "排序已更新"}

@router.get("/{asset_id}", response_model=AssetResponse)
async def get_asset(
    asset_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """根据 ID 获取资产"""
    asset = db.query(Asset).filter(
        Asset.id == asset_id,
        Asset.user_id == current_user.id
    ).first()
    
    if not asset:
        raise HTTPException(status_code=404, detail="资产不存在")
    
    # 获取对应的币种信息
    crypto = db.query(Cryptocurrency).filter(
        Cryptocurrency.id == asset.crypto_id
    ).first()
    
    return AssetResponse(
        id=asset.id,
        crypto_id=asset.crypto_id,
        crypto_symbol=crypto.symbol if crypto else "Unknown",
        crypto_name=crypto.name if crypto else "Unknown",
        buy_price=asset.buy_price,
        quantity=asset.quantity,
        notes=asset.notes,
        total_value=asset.buy_price * asset.quantity,
        created_at=asset.created_at.isoformat() if asset.created_at else None
    )

@router.post("/", response_model=AssetResponse)
async def create_asset(
    asset_data: AssetCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """创建新资产"""
    # 查找或创建币种
    crypto = db.query(Cryptocurrency).filter(
        Cryptocurrency.symbol == asset_data.crypto_symbol
    ).first()
    
    if not crypto:
        # 自动创建新币种，使用正确的币种名称提取逻辑
        coin_name = extract_coin_name_from_symbol(asset_data.crypto_symbol)
        full_name = get_coin_full_name(coin_name)
        crypto = Cryptocurrency(
            symbol=asset_data.crypto_symbol,
            name=coin_name,
            display_name=full_name,
            is_active=True
        )
        db.add(crypto)
        db.commit()
        db.refresh(crypto)
    
    # 获取配置中的时区 (Asia/Shanghai)
    tz = config_manager.get_timezone()
    
    # 获取最大排序值+1，确保新项目排在最后
    max_sort = db.query(func.coalesce(func.max(Asset.sort_order), 0)).filter(
        Asset.user_id == current_user.id
    ).scalar()
    
    # 补充 created_at 字段
    asset = Asset(
        user_id=current_user.id,
        crypto_id=crypto.id,
        buy_price=asset_data.buy_price,
        quantity=asset_data.quantity,
        notes=asset_data.notes,
        sort_order=max_sort + 1,
        created_at=datetime.now(tz)  # 强制写入当前时区时间
    )
    
    db.add(asset)
    db.commit()
    db.refresh(asset)
    
    return AssetResponse(
        id=asset.id,
        crypto_id=asset.crypto_id,
        crypto_symbol=crypto.symbol,
        crypto_name=crypto.name,
        buy_price=asset.buy_price,
        quantity=asset.quantity,
        notes=asset.notes,
        total_value=asset.buy_price * asset.quantity,
        created_at=asset.created_at.isoformat() if asset.created_at else None
    )

@router.put("/{asset_id}", response_model=AssetResponse)
async def update_asset(
    asset_id: int,
    asset_data: AssetUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """更新资产"""
    asset = db.query(Asset).filter(
        Asset.id == asset_id,
        Asset.user_id == current_user.id
    ).first()
    
    if not asset:
        raise HTTPException(status_code=404, detail="资产不存在")
    
    if asset_data.buy_price is not None:
        asset.buy_price = asset_data.buy_price
    if asset_data.quantity is not None:
        asset.quantity = asset_data.quantity
    if asset_data.notes is not None:
        asset.notes = asset_data.notes
    
    db.commit()
    db.refresh(asset)
    
    # 获取对应的币种信息
    crypto = db.query(Cryptocurrency).filter(
        Cryptocurrency.id == asset.crypto_id
    ).first()
    
    return AssetResponse(
        id=asset.id,
        crypto_id=asset.crypto_id,
        crypto_symbol=crypto.symbol if crypto else "Unknown",
        crypto_name=crypto.name if crypto else "Unknown",
        buy_price=asset.buy_price,
        quantity=asset.quantity,
        notes=asset.notes,
        total_value=asset.buy_price * asset.quantity,
        created_at=asset.created_at.isoformat() if asset.created_at else None
    )

@router.delete("/all")
async def delete_all_assets(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """删除当前用户的所有资产记录"""
    count = db.query(Asset).filter(
        Asset.user_id == current_user.id
    ).delete()
    db.commit()
    return {"message": f"已删除 {count} 条资产记录"}

@router.delete("/{asset_id}")
async def delete_asset(
    asset_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """删除资产"""
    asset = db.query(Asset).filter(
        Asset.id == asset_id,
        Asset.user_id == current_user.id
    ).first()
    
    if not asset:
        raise HTTPException(status_code=404, detail="资产不存在")
    
    # 获取币种信息
    crypto = db.query(Cryptocurrency).filter(
        Cryptocurrency.id == asset.crypto_id
    ).first()
    
    # 删除资产
    db.delete(asset)
    db.commit()
    
    # 检查是否还有其他资产使用该币种，如果没有且没有预警使用，则删除币种
    # 检查是否还有任何表、任何用户使用该币种
    if crypto:
        from app.models.alert import PriceAlert
        from app.models.watchlist import Watchlist
        
        has_alert = db.query(PriceAlert).filter(PriceAlert.crypto_id == crypto.id).first()
        has_watchlist = db.query(Watchlist).filter(Watchlist.crypto_id == crypto.id).first()
        
        # 只有在三个表都彻底无人使用时，才安全删除币种字典
        if not has_alert and not has_watchlist:
            db.delete(crypto)
            db.commit()
            return {"message": "记录及冗余币种已删除"}
    
    return {"message": "记录已删除"}
