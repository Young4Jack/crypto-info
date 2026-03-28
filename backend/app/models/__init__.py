# Models package
# 按照正确的导入顺序，避免循环依赖

# 首先导入基础模型
from app.database import Base

# 然后按依赖关系导入各个模型
from app.models.user import User
from app.models.cryptocurrency import Cryptocurrency
from app.models.alert import PriceAlert, AlertType
from app.models.alert_history import AlertHistory, AlertHistoryStatus
from app.models.asset import Asset
from app.models.watchlist import Watchlist

# 导出所有模型
__all__ = [
    "Base",
    "User",
    "Cryptocurrency", 
    "PriceAlert",
    "AlertType",
    "AlertHistory",
    "AlertHistoryStatus",
    "Asset",
    "Watchlist"
]
