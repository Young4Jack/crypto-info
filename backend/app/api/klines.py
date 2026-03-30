"""K线数据API"""
from fastapi import APIRouter, Query
from typing import Optional
from app.services.price_service_refactored import fetch_kline_data
from app.models.watchlist import Watchlist
from app.database import SessionLocal
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/klines", tags=["K线数据"])

@router.get("/{symbol}")
async def get_kline_data(
    symbol: str,
    interval: str = Query(default="1h", description="K线周期: 1m, 5m, 15m, 30m, 1h, 4h, 1d, 1w, 1M"),
    limit: int = Query(default=100, ge=1, le=1000, description="返回数量，最大1000")
):
    """
    获取指定交易对的K线数据
    """
    try:
        klines = await fetch_kline_data(symbol.upper(), interval, limit)
        return {
            "success": True,
            "data": {
                "symbol": symbol.upper(),
                "interval": interval,
                "klines": klines
            }
        }
    except Exception as e:
        logger.error(f"获取K线数据失败: {e}")
        return {
            "success": False,
            "error": str(e)
        }

@router.get("/watchlist/all")
async def get_watchlist_klines(
    interval: str = Query(default="1h", description="K线周期"),
    limit: int = Query(default=50, ge=1, le=500, description="每个币种返回数量")
):
    """
    获取关注列表中所有币种的K线数据
    """
    db = SessionLocal()
    try:
        # 获取关注列表
        watchlist = db.query(Watchlist).all()
        
        result = {}
        for item in watchlist:
            symbol = item.crypto_symbol
            try:
                klines = await fetch_kline_data(symbol, interval, limit)
                result[symbol] = {
                    "name": item.crypto_name,
                    "klines": klines
                }
            except Exception as e:
                logger.error(f"获取 {symbol} K线数据失败: {e}")
                result[symbol] = {
                    "name": item.crypto_name,
                    "klines": [],
                    "error": str(e)
                }
        
        return {
            "success": True,
            "data": result
        }
    except Exception as e:
        logger.error(f"获取关注列表K线数据失败: {e}")
        return {
            "success": False,
            "error": str(e)
        }
    finally:
        db.close()