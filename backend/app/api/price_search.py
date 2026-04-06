"""价格搜索 API - 按交易对查询实时价格"""
import httpx
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel

from app.database import get_db
from app.api.deps import get_current_user
from app.models.user import User
from app.models.cryptocurrency import Cryptocurrency
from app.config_manager import config_manager
from app.utils.crypto_utils import extract_coin_name_from_symbol, get_coin_full_name

router = APIRouter(prefix="/api/price-search", tags=["价格搜索"])


class PriceSearchResponse(BaseModel):
    """价格搜索响应"""
    symbol: str
    name: str
    display_name: str
    price: Optional[float] = None
    source: str = ""


async def _fetch_single_price_from_binance(symbol: str, base_url: str) -> Optional[float]:
    url = f"{base_url}/api/v3/ticker/price"
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
    }
    async with httpx.AsyncClient(timeout=10.0) as client:
        response = await client.get(url, params={"symbol": symbol}, headers=headers)
        if response.status_code == 200:
            data = response.json()
            if data.get("symbol") == symbol and data.get("price"):
                return float(data["price"])
    return None


async def _fetch_single_price_from_okx(symbol: str, base_url: str) -> Optional[float]:
    inst_id = symbol
    for quote in ['USDT', 'USDC', 'BTC', 'ETH']:
        if symbol.endswith(quote):
            base = symbol[:-len(quote)]
            inst_id = f"{base}-{quote}"
            break

    url = f"{base_url}/api/v5/market/ticker"
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
    }
    async with httpx.AsyncClient(timeout=10.0) as client:
        response = await client.get(url, params={"instId": inst_id}, headers=headers)
        if response.status_code == 200:
            data = response.json()
            if data.get("code") == "0" and data.get("data"):
                ticker = data["data"][0]
                if ticker.get("last"):
                    return float(ticker["last"])
    return None


async def _fetch_single_price(symbol: str, api_url: str) -> Optional[float]:
    if not api_url:
        return None

    if 'binance' in api_url.lower():
        return await _fetch_single_price_from_binance(symbol, api_url)
    elif 'okx' in api_url.lower():
        return await _fetch_single_price_from_okx(symbol, api_url)
    else:
        return await _fetch_single_price_from_binance(symbol, api_url)


@router.get("/", response_model=PriceSearchResponse)
async def search_price(
    symbol: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    搜索指定交易对的实时价格（需要登录）

    - 从 config.json 读取主/备 API 地址
    - 主 API 失败时自动切换到备用 API
    - 如果币种不在数据库中，会自动创建
    """
    symbol = symbol.strip().upper()
    if not symbol:
        raise HTTPException(status_code=400, detail="交易对符号不能为空")

    quote_currencies = ['USDT', 'USDC', 'BTC', 'ETH', 'FDUSD']
    has_quote = any(symbol.endswith(q) for q in quote_currencies)
    if not has_quote:
        symbol += 'USDT'

    api_settings = config_manager.get_api_settings()
    primary_api_url = api_settings.get("primary_api_url", "")
    backup_api_url = api_settings.get("backup_api_url", "")

    price = None
    source = ""

    if primary_api_url:
        try:
            price = await _fetch_single_price(symbol, primary_api_url)
            if price and price > 0:
                source = primary_api_url
        except Exception:
            pass

    if not price and backup_api_url:
        try:
            price = await _fetch_single_price(symbol, backup_api_url)
            if price and price > 0:
                source = backup_api_url
        except Exception:
            pass

    if not price:
        default_urls = ["https://www.okx.com", "https://api.binance.com"]
        for default_url in default_urls:
            try:
                price = await _fetch_single_price(symbol, default_url)
                if price and price > 0:
                    source = default_url
                    break
            except Exception:
                continue

    if not price:
        raise HTTPException(status_code=502, detail=f"无法获取 {symbol} 的价格，请检查网络或 API 配置")

    crypto = db.query(Cryptocurrency).filter(Cryptocurrency.symbol == symbol).first()
    if not crypto:
        coin_name = extract_coin_name_from_symbol(symbol)
        display_name = get_coin_full_name(coin_name)
        crypto = Cryptocurrency(
            symbol=symbol,
            name=coin_name,
            display_name=display_name,
            is_active=True
        )
        db.add(crypto)
        db.commit()
        db.refresh(crypto)

    return PriceSearchResponse(
        symbol=crypto.symbol,
        name=crypto.name,
        display_name=crypto.display_name or "",
        price=price,
        source=source
    )
