"""关注列表 API 路由"""
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel
from app.database import get_db
from app.models.watchlist import Watchlist
from app.models.cryptocurrency import Cryptocurrency
from app.api.deps import get_current_user
from app.models.user import User
from app.utils.crypto_utils import extract_coin_name_from_symbol, get_coin_full_name
from app.services.price_service_refactored import fetch_crypto_prices
from datetime import datetime
from app.config_manager import config_manager

router = APIRouter(prefix="/api/watchlist", tags=["关注列表"])

class WatchlistCreate(BaseModel):
    """创建关注项请求"""
    crypto_symbol: str
    notes: Optional[str] = None

class WatchlistUpdate(BaseModel):
    """更新关注项请求"""
    notes: Optional[str] = None

class WatchlistResponse(BaseModel):
    """关注项响应"""
    id: int
    crypto_id: int
    crypto_symbol: str
    crypto_name: str
    notes: Optional[str] = None
    created_at: str
    current_price: Optional[float] = None

@router.get("/", response_model=List[WatchlistResponse])
async def get_watchlist(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """获取当前用户的所有关注项"""
    watchlist_items = db.query(Watchlist).filter(
        Watchlist.user_id == current_user.id
    ).all()
    
    # 获取当前价格数据
    try:
        current_prices = await fetch_crypto_prices()
    except Exception as e:
        print(f"获取价格失败: {e}")
        current_prices = {}
    
    result = []
    for item in watchlist_items:
        # 获取对应的币种信息
        crypto = db.query(Cryptocurrency).filter(
            Cryptocurrency.id == item.crypto_id
        ).first()
        
        # 获取当前价格
        current_price = current_prices.get(crypto.symbol, 0) if crypto else 0
        
        result.append(WatchlistResponse(
            id=item.id,
            crypto_id=item.crypto_id,
            crypto_symbol=crypto.symbol if crypto else "Unknown",
            crypto_name=crypto.name if crypto else "Unknown",
            notes=item.notes,
            created_at=item.created_at.isoformat() if item.created_at else None,
            current_price=current_price
        ))
    
    return result

@router.get("/public", response_model=List[WatchlistResponse])
async def get_public_watchlist(db: Session = Depends(get_db)):
    """获取公开的关注列表（无需认证）"""
    # 获取所有用户的关注项，去重
    watchlist_items = db.query(Watchlist).all()
    
    # 获取当前价格数据
    try:
        current_prices = await fetch_crypto_prices()
    except Exception as e:
        print(f"获取价格失败: {e}")
        current_prices = {}
    
    # 按币种去重
    seen_symbols = set()
    result = []
    
    for item in watchlist_items:
        crypto = db.query(Cryptocurrency).filter(
            Cryptocurrency.id == item.crypto_id
        ).first()
        
        if crypto and crypto.symbol not in seen_symbols:
            seen_symbols.add(crypto.symbol)
            # 获取当前价格
            current_price = current_prices.get(crypto.symbol, 0)
            
            result.append(WatchlistResponse(
                id=item.id,
                crypto_id=item.crypto_id,
                crypto_symbol=crypto.symbol,
                crypto_name=crypto.name,
                notes=item.notes,
                created_at=item.created_at.isoformat() if item.created_at else None,
                current_price=current_price
            ))
    
    return result

@router.post("/", response_model=WatchlistResponse)
async def create_watchlist_item(
    watchlist_data: WatchlistCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """创建新的关注项"""
    # 查找币种，如果不存在则自动创建
    crypto = db.query(Cryptocurrency).filter(
        Cryptocurrency.symbol == watchlist_data.crypto_symbol
    ).first()
    
    if not crypto:
        # 自动创建新币种
        coin_name = extract_coin_name_from_symbol(watchlist_data.crypto_symbol)
        full_name = get_coin_full_name(coin_name)
        crypto = Cryptocurrency(
            symbol=watchlist_data.crypto_symbol,
            name=coin_name,
            display_name=full_name,
            is_active=True
        )
        db.add(crypto)
        db.commit()
        db.refresh(crypto)
    
    # 检查是否已存在相同的关注项
    existing = db.query(Watchlist).filter(
        Watchlist.user_id == current_user.id,
        Watchlist.crypto_id == crypto.id
    ).first()
    
    if existing:
        raise HTTPException(status_code=400, detail="该币种已在关注列表中")
    
    tz = config_manager.get_timezone()

    # 创建关注项
    watchlist_item = Watchlist(
        user_id=current_user.id,
        crypto_id=crypto.id,
        notes=watchlist_data.notes,
        created_at=datetime.now(tz)
    )
    
    db.add(watchlist_item)
    db.commit()
    db.refresh(watchlist_item)
    
    return WatchlistResponse(
        id=watchlist_item.id,
        crypto_id=watchlist_item.crypto_id,
        crypto_symbol=crypto.symbol,
        crypto_name=crypto.name,
        notes=watchlist_item.notes,
        created_at=watchlist_item.created_at.isoformat() if watchlist_item.created_at else None
    )

@router.put("/{watchlist_id}", response_model=WatchlistResponse)
async def update_watchlist_item(
    watchlist_id: int,
    watchlist_data: WatchlistUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """更新关注项"""
    watchlist_item = db.query(Watchlist).filter(
        Watchlist.id == watchlist_id,
        Watchlist.user_id == current_user.id
    ).first()
    
    if not watchlist_item:
        raise HTTPException(status_code=404, detail="关注项不存在")
    
    # 更新字段
    if watchlist_data.notes is not None:
        watchlist_item.notes = watchlist_data.notes
    
    db.commit()
    db.refresh(watchlist_item)
    
    # 获取币种信息
    crypto = db.query(Cryptocurrency).filter(
        Cryptocurrency.id == watchlist_item.crypto_id
    ).first()
    
    return WatchlistResponse(
        id=watchlist_item.id,
        crypto_id=watchlist_item.crypto_id,
        crypto_symbol=crypto.symbol if crypto else "Unknown",
        crypto_name=crypto.name if crypto else "Unknown",
        notes=watchlist_item.notes,
        created_at=watchlist_item.created_at.isoformat() if watchlist_item.created_at else None
    )

@router.delete("/{watchlist_id}")
async def delete_watchlist_item(
    watchlist_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """删除关注项"""
    # 获取关注项
    watchlist_item = db.query(Watchlist).filter(
        Watchlist.id == watchlist_id,
        Watchlist.user_id == current_user.id
    ).first()
    
    if not watchlist_item:
        raise HTTPException(status_code=404, detail="关注项不存在")
    
    # 获取币种信息
    crypto = db.query(Cryptocurrency).filter(
        Cryptocurrency.id == watchlist_item.crypto_id
    ).first()
    
    # 删除关注项
    db.delete(watchlist_item)
    db.commit()
    
    # 检查资产管理中是否还有该交易对，如果没有则删除币种
    if crypto:
        from app.models.asset import Asset
        from app.models.alert import PriceAlert
        
        has_asset = db.query(Asset).filter(Asset.crypto_id == crypto.id).first()
        has_alert = db.query(PriceAlert).filter(PriceAlert.crypto_id == crypto.id).first()
        
        # 只有在三个表都彻底无人使用时，才安全删除币种字典
        if not has_asset and not has_alert:
            db.delete(crypto)
            db.commit()
            return {"message": "记录及冗余币种已删除"}
    
    return {"message": "记录已删除"}
