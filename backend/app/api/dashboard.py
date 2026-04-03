"""仪表盘 API 路由"""
from typing import Dict, Any, List
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import func
from app.database import get_db
from app.models.asset import Asset
from app.models.alert import PriceAlert
from app.models.cryptocurrency import Cryptocurrency
from app.models.watchlist import Watchlist
from app.api.deps import get_current_user
from app.models.user import User
from app.services.price_service_refactored import fetch_crypto_prices

router = APIRouter(prefix="/dashboard", tags=["仪表盘"])

@router.get("/summary", response_model=Dict[str, Any])
async def get_dashboard_summary(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    获取仪表盘综合数据
    - 资产总值（基于最新价格估算）
    - 资产配置占比（各币种持有价值）
    - 激活状态下的预警规则数量
    - 最新的 5 条中文新闻摘要
    """
    
    # 1. 优化查询：一次性获取所有资产和币种信息
    assets_with_crypto = db.query(
        Asset, Cryptocurrency
    ).join(
        Cryptocurrency, Asset.crypto_id == Cryptocurrency.id
    ).filter(
        Asset.user_id == current_user.id
    ).all()
    
    # 2. 获取最新价格数据
    try:
        current_prices = await fetch_crypto_prices()
    except Exception as e:
        print(f"获取价格失败: {e}")
        current_prices = {}
    
    # 3. 计算资产总值和各币种配置
    total_value = 0.0
    asset_allocation = []
    
    for asset, crypto in assets_with_crypto:
        # 获取当前价格
        current_price = current_prices.get(crypto.symbol, 0)
        
        # 计算持有价值
        holding_value = asset.quantity * current_price
        total_value += holding_value
        
        # 计算买入价值
        buy_value = asset.quantity * asset.buy_price
        
        # 计算盈亏
        profit_loss = holding_value - buy_value
        profit_loss_percentage = (profit_loss / buy_value * 100) if buy_value > 0 else 0
        
        asset_allocation.append({
            "crypto_symbol": crypto.symbol,
            "crypto_name": crypto.name,
            "quantity": asset.quantity,
            "buy_price": asset.buy_price,
            "current_price": current_price,
            "holding_value": round(holding_value, 2),
            "buy_value": round(buy_value, 2),
            "profit_loss": round(profit_loss, 2),
            "profit_loss_percentage": round(profit_loss_percentage, 2),
            "sort_order": asset.sort_order or 0,
            "created_at": asset.created_at.isoformat() if asset.created_at else None
        })
    
    # 按 sort_order 排序
    asset_allocation.sort(key=lambda x: x["sort_order"])
    
    # 4. 计算总盈亏
    total_buy_value = sum(item["buy_value"] for item in asset_allocation)
    total_profit_loss = total_value - total_buy_value
    total_profit_loss_percentage = (total_profit_loss / total_buy_value * 100) if total_buy_value > 0 else 0
    
    # 5. 获取激活状态下的预警规则数量
    active_alerts_count = db.query(PriceAlert).filter(
        PriceAlert.user_id == current_user.id,
        PriceAlert.is_active == True
    ).count()
    
    # 6. 获取关注列表(按sort_order排序)
    watchlist_items = db.query(Watchlist, Cryptocurrency).join(
        Cryptocurrency, Watchlist.crypto_id == Cryptocurrency.id
    ).filter(
        Watchlist.user_id == current_user.id
    ).order_by(Watchlist.sort_order.asc()).all()
    
    watchlist_data = []
    for item, crypto in watchlist_items:
        current_price = current_prices.get(crypto.symbol, 0)
        watchlist_data.append({
            "id": item.id,
            "crypto_symbol": crypto.symbol,
            "crypto_name": crypto.name,
            "current_price": current_price,
            "sort_order": item.sort_order or 0
        })
    
    # 7. 获取预警规则(按sort_order排序)
    alerts = db.query(PriceAlert, Cryptocurrency).join(
        Cryptocurrency, PriceAlert.crypto_id == Cryptocurrency.id
    ).filter(
        PriceAlert.user_id == current_user.id
    ).order_by(PriceAlert.sort_order.asc()).all()
    
    alerts_data = []
    for alert, crypto in alerts:
        current_price = current_prices.get(crypto.symbol, 0)
        alerts_data.append({
            "id": alert.id,
            "crypto_symbol": crypto.symbol,
            "crypto_name": crypto.name,
            "alert_type": alert.alert_type.value,
            "threshold_price": alert.threshold_price,
            "current_price": current_price,
            "is_active": alert.is_active,
            "sort_order": alert.sort_order or 0
        })
    
    # 8. 返回仪表盘数据（新闻功能已移除）
    return {
        "total_value": round(total_value, 2),
        "total_profit_loss": round(total_profit_loss, 2),
        "total_profit_loss_percentage": round(total_profit_loss_percentage, 2),
        "active_alerts_count": active_alerts_count,
        "asset_allocation": asset_allocation,
        "watchlist": watchlist_data,
        "alerts": alerts_data,
        "latest_news": [],  # 新闻功能已移除
        "summary": {
            "total_assets": len(assets_with_crypto),
            "total_cryptocurrencies": len(set(item["crypto_symbol"] for item in asset_allocation))
        }
    }

@router.get("/allocation", response_model=List[Dict[str, Any]])
async def get_asset_allocation(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    获取资产配置占比数据（用于图表）
    """
    # 获取当前用户的所有资产
    assets = db.query(Asset).filter(
        Asset.user_id == current_user.id
    ).all()
    
    # 获取最新价格数据
    try:
        current_prices = await fetch_crypto_prices()
    except Exception as e:
        print(f"获取价格失败: {e}")
        current_prices = {}
    
    allocation = []
    
    for asset in assets:
        # 获取币种信息
        crypto = db.query(Cryptocurrency).filter(
            Cryptocurrency.id == asset.crypto_id
        ).first()
        
        if not crypto:
            continue
        
        # 获取当前价格
        current_price = current_prices.get(crypto.symbol, 0)
        
        # 计算持有价值
        holding_value = asset.quantity * current_price
        
        allocation.append({
            "name": crypto.name,
            "symbol": crypto.symbol,
            "value": round(holding_value, 2),
            "quantity": asset.quantity
        })
    
    # 按价值排序
    allocation.sort(key=lambda x: x["value"], reverse=True)
    
    return allocation