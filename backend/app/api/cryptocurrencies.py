"""币种 API 路由"""
from typing import List
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.database import get_db
from app.models.cryptocurrency import Cryptocurrency
from app.api.deps import get_current_user
from app.models.user import User

router = APIRouter(prefix="/api/cryptocurrencies", tags=["币种管理"])

@router.get("/", response_model=List[dict])
async def get_cryptocurrencies(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """获取所有激活的币种列表"""
    cryptos = db.query(Cryptocurrency).filter(
        Cryptocurrency.is_active == True
    ).all()
    
    return [
        {
            "id": crypto.id,
            "symbol": crypto.symbol,
            "name": crypto.name,
            "logo_url": crypto.logo_url,
            "is_active": crypto.is_active,
            "created_at": crypto.created_at.isoformat() if crypto.created_at else None
        }
        for crypto in cryptos
    ]

@router.get("/all", response_model=List[dict])
async def get_all_cryptocurrencies(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """获取所有币种列表（包括非激活状态）"""
    cryptos = db.query(Cryptocurrency).all()
    
    return [
        {
            "id": crypto.id,
            "symbol": crypto.symbol,
            "name": crypto.name,
            "logo_url": crypto.logo_url,
            "is_active": crypto.is_active,
            "created_at": crypto.created_at.isoformat() if crypto.created_at else None
        }
        for crypto in cryptos
    ]

@router.get("/{crypto_id}", response_model=dict)
async def get_cryptocurrency(
    crypto_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """根据 ID 获取币种信息"""
    crypto = db.query(Cryptocurrency).filter(
        Cryptocurrency.id == crypto_id
    ).first()
    
    if not crypto:
        raise HTTPException(status_code=404, detail="币种不存在")
    
    return {
        "id": crypto.id,
        "symbol": crypto.symbol,
        "name": crypto.name,
        "logo_url": crypto.logo_url,
        "is_active": crypto.is_active,
        "created_at": crypto.created_at.isoformat() if crypto.created_at else None
    }

@router.post("/", response_model=dict)
async def create_cryptocurrency(
    symbol: str,
    name: str,
    logo_url: str = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """创建新币种"""
    # 检查币种是否已存在
    existing = db.query(Cryptocurrency).filter(
        Cryptocurrency.symbol == symbol
    ).first()
    
    if existing:
        raise HTTPException(status_code=400, detail="币种符号已存在")
    
    crypto = Cryptocurrency(
        symbol=symbol,
        name=name,
        logo_url=logo_url,
        is_active=True
    )
    
    db.add(crypto)
    db.commit()
    db.refresh(crypto)
    
    return {
        "id": crypto.id,
        "symbol": crypto.symbol,
        "name": crypto.name,
        "logo_url": crypto.logo_url,
        "is_active": crypto.is_active,
        "created_at": crypto.created_at.isoformat() if crypto.created_at else None
    }

@router.put("/{crypto_id}", response_model=dict)
async def update_cryptocurrency(
    crypto_id: int,
    symbol: str = None,
    name: str = None,
    logo_url: str = None,
    is_active: bool = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """更新币种信息"""
    crypto = db.query(Cryptocurrency).filter(
        Cryptocurrency.id == crypto_id
    ).first()
    
    if not crypto:
        raise HTTPException(status_code=404, detail="币种不存在")
    
    if symbol is not None:
        crypto.symbol = symbol
    if name is not None:
        crypto.name = name
    if logo_url is not None:
        crypto.logo_url = logo_url
    if is_active is not None:
        crypto.is_active = is_active
    
    db.commit()
    db.refresh(crypto)
    
    return {
        "id": crypto.id,
        "symbol": crypto.symbol,
        "name": crypto.name,
        "logo_url": crypto.logo_url,
        "is_active": crypto.is_active,
        "created_at": crypto.created_at.isoformat() if crypto.created_at else None
    }

@router.delete("/{crypto_id}")
async def delete_cryptocurrency(
    crypto_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """删除币种"""
    crypto = db.query(Cryptocurrency).filter(
        Cryptocurrency.id == crypto_id
    ).first()
    
    if not crypto:
        raise HTTPException(status_code=404, detail="币种不存在")
    
    db.delete(crypto)
    db.commit()
    
    return {"message": "币种已删除"}