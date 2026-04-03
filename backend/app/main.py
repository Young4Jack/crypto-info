"""FastAPI 主应用"""
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from app.config import settings
from app.api import auth, cryptocurrencies, alerts, assets, dashboard
from app.api import settings as settings_router
from app.api import api_settings
from app.api import alert_histories
from app.api import system_settings
from app.api import account
from app.api import watchlist
from app.api import klines
from app.tasks.scheduler import start_scheduler, shutdown_scheduler, get_scheduler_status
from app.utils.logger import setup_logger, get_logger
from app.config_manager import config_manager
import logging

# 获取配置的日志设置
system_config = config_manager.get_system_settings()
log_level = system_config.get('log_level', 'INFO')
enable_logging = system_config.get('enable_logging', True)

# 根据配置设置日志级别
log_level_map = {
    'DEBUG': logging.DEBUG,
    'INFO': logging.INFO,
    'WARNING': logging.WARNING,
    'ERROR': logging.ERROR
}

# 配置日志级别
if enable_logging:
    logging.basicConfig(level=log_level_map.get(log_level, logging.INFO))
else:
    logging.basicConfig(level=logging.CRITICAL)  # 禁用所有日志

# 配置httpx日志（HTTP请求日志）
if enable_logging and log_level in ['INFO', 'DEBUG']:
    logging.getLogger("httpx").setLevel(logging.INFO)
else:
    logging.getLogger("httpx").setLevel(logging.CRITICAL)

# 配置httpcore日志
if enable_logging and log_level in ['INFO', 'DEBUG']:
    logging.getLogger("httpcore").setLevel(logging.INFO)
else:
    logging.getLogger("httpcore").setLevel(logging.CRITICAL)

# 配置apscheduler日志（定时任务日志）
if enable_logging and log_level in ['INFO', 'DEBUG']:
    logging.getLogger("apscheduler").setLevel(logging.INFO)
else:
    logging.getLogger("apscheduler").setLevel(logging.CRITICAL)

# 配置uvicorn日志（服务器日志）
if enable_logging and log_level in ['INFO', 'DEBUG']:
    logging.getLogger("uvicorn").setLevel(logging.INFO)
    logging.getLogger("uvicorn.access").setLevel(logging.INFO)
    logging.getLogger("uvicorn.error").setLevel(logging.INFO)
else:
    logging.getLogger("uvicorn").setLevel(logging.CRITICAL)
    logging.getLogger("uvicorn.access").setLevel(logging.CRITICAL)
    logging.getLogger("uvicorn.error").setLevel(logging.CRITICAL)

# 初始化日志系统
setup_logger()
logger = get_logger(__name__)

@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用生命周期管理"""
    # 启动时执行
    logger.info("应用启动中...")
    start_scheduler()
    yield
    # 关闭时执行
    logger.info("应用关闭中...")
    shutdown_scheduler()

app = FastAPI(
    title="Crypto-info API",
    description="数字货币价格监控和预警系统 API",
    version="1.0.0",
    lifespan=lifespan
)

# CORS 配置
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 允许所有来源，便于调试
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 日志系统已在上面初始化

# 注册路由
app.include_router(auth.router)
app.include_router(cryptocurrencies.router)
app.include_router(alerts.router)
app.include_router(assets.router)
app.include_router(dashboard.router)
app.include_router(settings_router.router)
app.include_router(api_settings.router)
app.include_router(alert_histories.router)
app.include_router(system_settings.router)
app.include_router(account.router)
app.include_router(watchlist.router)
app.include_router(klines.router)

# 全局异常处理
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """全局异常处理器"""
    logger.error(f"服务器内部错误: {str(exc)}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={
            "error": "服务器内部错误",
            "detail": str(exc) if settings.DEBUG else "请联系管理员"
        }
    )

@app.get("/health")
async def health_check():
    """健康检查接口"""
    return {
        "status": "healthy",
        "message": "Crypto-info API is running",
        "version": "1.0.0"
    }

@app.get("/")
async def root():
    """根路径"""
    return {"message": "Welcome to Crypto-info API"}

@app.get("/scheduler/status")
async def scheduler_status():
    """获取定时任务调度器状态"""
    return get_scheduler_status()