"""价格获取服务
重构后的版本，支持批量价格获取和严格数据过滤"""
from typing import Dict
from sqlalchemy.orm import Session
from app.services.price_service_refactored import fetch_crypto_prices, get_current_prices

# 重新导出重构后的主要函数
__all__ = ['fetch_crypto_prices', 'get_current_prices']

# 为了保持向后兼容性，直接导入重构后的函数
async def fetch_crypto_prices() -> Dict[str, float]:
    """
    异步获取加密货币价格（主入口函数）
    实现Failover机制和严格数据过滤
    """
    # 直接调用重构后的函数
    from app.services.price_service_refactored import fetch_crypto_prices as refactored_fetch
    return await refactored_fetch()

def get_current_prices(db: Session) -> Dict[str, float]:
    """
    获取当前价格（同步版本，用于 API 调用）
    返回最近存储的价格数据
    """
    # 直接调用重构后的函数
    from app.services.price_service_refactored import get_current_prices as refactored_get
    return refactored_get(db)