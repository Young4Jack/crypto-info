"""K线数据API"""
from fastapi import APIRouter, Query
from typing import Optional
from app.services.price_service_refactored import fetch_kline_data
from app.models.watchlist import Watchlist
from app.models.cryptocurrency import Cryptocurrency
from app.database import SessionLocal
import logging
from fastapi import WebSocket, WebSocketDisconnect
import asyncio
import json
import websockets

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
    获取关注列表中所有币种的K线数据 (并发优化版)
    """
    db = SessionLocal()
    try:
        watchlist = db.query(Watchlist).join(Cryptocurrency).all()
        
        # 构建并发任务列表
        tasks = []
        symbols_info = []
        for item in watchlist:
            symbol = item.cryptocurrency.symbol
            name = item.cryptocurrency.name
            symbols_info.append((symbol, name))
            # 将外部请求加入任务队列
            tasks.append(fetch_kline_data(symbol, interval, limit))
        
        # 并发执行所有请求
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # 处理并发结果
        result = {}
        for (symbol, name), klines in zip(symbols_info, results):
            if isinstance(klines, Exception):
                logger.error(f"获取 {symbol} K线数据失败: {klines}")
                result[symbol] = {
                    "name": name,
                    "klines": [],
                    "error": str(klines)
                }
            else:
                result[symbol] = {
                    "name": name,
                    "klines": klines
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

# ==========================================
# WebSocket 实时K线推送逻辑
# ==========================================

class ConnectionManager:
    def __init__(self):
        # 记录连接的前端客户端: {"BTCUSDT": [ws1, ws2]}
        self.active_connections: dict = {}
        # 记录后台正在拉取交易所数据的异步任务: {"BTCUSDT": task}
        self.background_tasks: dict = {}

    async def connect(self, websocket: WebSocket, symbol: str):
        await websocket.accept()
        symbol_upper = symbol.upper()
        
        if symbol_upper not in self.active_connections:
            self.active_connections[symbol_upper] = []
        self.active_connections[symbol_upper].append(websocket)
        
        # 如果是该币种的第一个连接，启动后台任务监听币安
        if symbol_upper not in self.background_tasks:
            task = asyncio.create_task(self._fetch_binance_ws(symbol_upper))
            self.background_tasks[symbol_upper] = task

    def disconnect(self, websocket: WebSocket, symbol: str):
        symbol_upper = symbol.upper()
        if symbol_upper in self.active_connections:
            if websocket in self.active_connections[symbol_upper]:
                self.active_connections[symbol_upper].remove(websocket)
            
            # 如果没有前端再监听这个币种，停止后台的币安连接
            if not self.active_connections[symbol_upper]:
                if symbol_upper in self.background_tasks:
                    self.background_tasks[symbol_upper].cancel()
                    del self.background_tasks[symbol_upper]

    async def _fetch_binance_ws(self, symbol: str):
        # 默认使用币安1分钟线WS流
        uri = f"wss://stream.binance.com:9443/ws/{symbol.lower()}@kline_1m"
        try:
            async with websockets.connect(uri) as exchange_ws:
                while True:
                    message = await exchange_ws.recv()
                    data = json.loads(message)
                    kline_data = data.get("k")
                    
                    if kline_data:
                        # 解析并统一为前端所需的数据格式
                        processed_data = {
                            'open_time': kline_data["t"],
                            'open': float(kline_data["o"]),
                            'high': float(kline_data["h"]),
                            'low': float(kline_data["l"]),
                            'close': float(kline_data["c"]),
                            'volume': float(kline_data["v"])
                        }
                        
                        # 广播给所有订阅了该币种的前端
                        dead_connections = []
                        for ws in self.active_connections.get(symbol, []):
                            try:
                                await ws.send_json(processed_data)
                            except Exception:
                                dead_connections.append(ws)
                                
                        # 清理断开的连接
                        for ws in dead_connections:
                            self.disconnect(ws, symbol)
                            
        except asyncio.CancelledError:
            pass # 任务被取消时正常退出
        except Exception as e:
            logger.error(f"币安 WS 连接异常 [{symbol}]: {e}")

manager = ConnectionManager()

# 注意：这里使用 router.websocket 暴露 WebSocket 接口
@router.websocket("/ws/{symbol}")
async def kline_websocket(websocket: WebSocket, symbol: str):
    await manager.connect(websocket, symbol)
    try:
        # 维持连接阻塞
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        manager.disconnect(websocket, symbol)