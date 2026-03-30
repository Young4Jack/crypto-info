"""重构后的价格获取服务
支持币安和OKX批量价格获取，实现严格的数据过滤和Failover机制"""
import httpx
from typing import Dict, List, Set, Optional
from sqlalchemy.orm import Session
from app.database import SessionLocal
from app.models.cryptocurrency import Cryptocurrency
from app.config_manager import config_manager
import logging

# 配置日志
logger = logging.getLogger(__name__)

class PriceService:
    """价格服务类，负责从多个交易所获取价格数据"""
    
    def __init__(self):
        # 默认API地址（仅在配置文件未设置时使用）
        self.default_binance_url = "https://api.binance.com"
        self.default_okx_url = "https://www.okx.com"
    
    def _log_info(self, message: str):
        """根据配置记录INFO日志"""
        system_settings = config_manager.get_system_settings()
        enable_logging = system_settings.get('enable_logging', True)
        log_level = system_settings.get('log_level', 'INFO')
        
        if enable_logging and log_level in ['INFO', 'DEBUG']:
            logger.info(message)
    
    def _log_error(self, message: str):
        """根据配置记录ERROR日志"""
        system_settings = config_manager.get_system_settings()
        enable_logging = system_settings.get('enable_logging', True)
        log_level = system_settings.get('log_level', 'INFO')
        
        if enable_logging and log_level in ['INFO', 'ERROR', 'DEBUG']:
            logger.error(message)
    
    def _log_warning(self, message: str):
        """根据配置记录WARNING日志"""
        system_settings = config_manager.get_system_settings()
        enable_logging = system_settings.get('enable_logging', True)
        log_level = system_settings.get('log_level', 'INFO')
        
        if enable_logging and log_level in ['INFO', 'WARNING', 'ERROR', 'DEBUG']:
            logger.warning(message)
    
    def _log_debug(self, message: str):
        """根据配置记录DEBUG日志"""
        system_settings = config_manager.get_system_settings()
        enable_logging = system_settings.get('enable_logging', True)
        log_level = system_settings.get('log_level', 'INFO')
        
        if enable_logging and log_level == 'DEBUG':
            logger.debug(message)
    
    async def fetch_all_prices(self) -> Dict[str, float]:
        """
        获取所有需要监控的币种价格
        实现Failover机制：优先使用主API，失败时切换到备用API
        """
        db = SessionLocal()
        try:
            # 步骤1：获取系统需要监控的币种列表
            target_symbols = await self._get_target_symbols(db)
            if not target_symbols:
                self._log_info("没有需要监控的币种")
                return {}
            
            # 步骤2：从配置获取API设置
            api_settings = config_manager.get_api_settings()
            primary_api_url = api_settings.get("primary_api_url")
            backup_api_url = api_settings.get("backup_api_url")
            
            # 步骤3：优先使用主API
            self._log_info(f"使用主API获取价格: {primary_api_url}")
            prices = await self._fetch_from_primary_api(target_symbols, primary_api_url)
            
            # 步骤4：如果主API失败，使用备用API
            if not prices and backup_api_url:
                self._log_warning(f"主API失败，切换到备用API: {backup_api_url}")
                prices = await self._fetch_from_backup_api(target_symbols, backup_api_url)
            
            # 步骤5：如果两个API都失败，使用默认API
            if not prices:
                self._log_warning("主备API都失败，使用默认API")
                prices = await self._fetch_from_default_apis(target_symbols)
            
            return prices
            
        except Exception as e:
            self._log_error(f"获取价格失败: {e}")
            return {}
        finally:
            db.close()
    
    async def _get_target_symbols(self, db: Session) -> Set[str]:
        """
        获取系统需要监控的币种集合
        从cryptocurrencies表中获取所有激活的币种
        """
        active_cryptos = db.query(Cryptocurrency).filter(
            Cryptocurrency.is_active == True
        ).all()
        
        target_symbols = set()
        for crypto in active_cryptos:
            target_symbols.add(crypto.symbol)
        
        self._log_info(f"系统需要监控 {len(target_symbols)} 个币种")
        return target_symbols
    
    async def _fetch_from_primary_api(self, target_symbols: Set[str], primary_api_url: str) -> Dict[str, float]:
        """
        从主API获取价格
        实现严格匹配和批量获取
        """
        if not primary_api_url:
            self._log_warning("主API地址未配置")
            return {}
        
        try:
            # 判断是币安还是OKX API
            if 'binance' in primary_api_url.lower():
                return await self._fetch_binance_batch(target_symbols, primary_api_url)
            elif 'okx' in primary_api_url.lower():
                return await self._fetch_okx_batch(target_symbols, primary_api_url)
            else:
                # 自定义API，使用单个币种查询
                return await self._fetch_custom_api_batch(target_symbols, primary_api_url)
        except Exception as e:
            self._log_error(f"主API获取失败: {e}")
            return {}
    
    async def _fetch_from_backup_api(self, target_symbols: Set[str], backup_api_url: str) -> Dict[str, float]:
        """
        从备用API获取价格
        实现严格匹配和批量获取
        """
        if not backup_api_url:
            self._log_warning("备用API地址未配置")
            return {}
        
        try:
            # 判断是币安还是OKX API
            if 'binance' in backup_api_url.lower():
                return await self._fetch_binance_batch(target_symbols, backup_api_url)
            elif 'okx' in backup_api_url.lower():
                return await self._fetch_okx_batch(target_symbols, backup_api_url)
            else:
                # 自定义API，使用单个币种查询
                return await self._fetch_custom_api_batch(target_symbols, backup_api_url)
        except Exception as e:
            self._log_error(f"备用API获取失败: {e}")
            return {}
    
    async def _fetch_from_default_apis(self, target_symbols: Set[str]) -> Dict[str, float]:
        """
        使用默认API获取价格（币安和OKX）
        """
        prices = {}
        
        # 尝试币安
        try:
            prices = await self._fetch_binance_batch(target_symbols, self.default_binance_url)
            if prices:
                self._log_info("使用默认币安API获取价格成功")
                return prices
        except Exception as e:
            self._log_error(f"默认币安API失败: {e}")
        
        # 尝试OKX
        try:
            prices = await self._fetch_okx_batch(target_symbols, self.default_okx_url)
            if prices:
                self._log_info("使用默认OKX API获取价格成功")
                return prices
        except Exception as e:
            self._log_error(f"默认OKX API失败: {e}")
        
        return prices
    
    async def _fetch_binance_batch(self, target_symbols: Set[str], base_url: str) -> Dict[str, float]:
        """
        从币安批量获取价格
        实现严格匹配：BTCUSDT == BTCUSDT
        """
        prices = {}
        
        # 构建批量获取URL
        url = f"{base_url}/api/v3/ticker/price"
        
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
        
        try:
            async with httpx.AsyncClient(timeout=15.0) as client:
                response = await client.get(url, headers=headers)
                
                if response.status_code == 200:
                    all_prices = response.json()
                    
                    # 严格匹配：只保留目标币种
                    for price_data in all_prices:
                        symbol = price_data.get("symbol")
                        price = price_data.get("price")
                        
                        # 严格匹配检查
                        if symbol in target_symbols and price:
                            try:
                                price_float = float(price)
                                if price_float > 0:
                                    prices[symbol] = price_float
                            except (ValueError, TypeError):
                                continue
                    
                    self._log_info(f"币安API返回 {len(all_prices)} 个价格，匹配到 {len(prices)} 个目标币种")
                else:
                    self._log_error(f"币安API返回状态码: {response.status_code}")
                    
        except Exception as e:
            self._log_error(f"币安API请求失败: {e}")
        
        return prices
    
    async def _fetch_okx_batch(self, target_symbols: Set[str], base_url: str) -> Dict[str, float]:
        """
        从OKX批量获取价格
        实现严格匹配：BTCUSDT == BTC-USDT
        """
        prices = {}
        
        # 构建批量获取URL
        url = f"{base_url}/api/v5/market/tickers?instType=SPOT"
        
        try:
            async with httpx.AsyncClient(timeout=15.0) as client:
                response = await client.get(url)
                
                if response.status_code == 200:
                    data = response.json()
                    all_tickers = data.get("data", [])
                    
                    # 严格匹配：只保留目标币种
                    for ticker in all_tickers:
                        inst_id = ticker.get("instId")  # 格式：BTC-USDT
                        last_price = ticker.get("last")
                        
                        if inst_id and last_price:
                            # 将OKX格式转换为标准格式
                            symbol = inst_id.replace("-", "")
                            
                            # 严格匹配检查
                            if symbol in target_symbols:
                                try:
                                    price_float = float(last_price)
                                    if price_float > 0:
                                        prices[symbol] = price_float
                                except (ValueError, TypeError):
                                    continue
                    
                    self._log_info(f"OKX API返回 {len(all_tickers)} 个价格，匹配到 {len(prices)} 个目标币种")
                else:
                    self._log_error(f"OKX API返回状态码: {response.status_code}")
                    
        except Exception as e:
            self._log_error(f"OKX API请求失败: {e}")
        
        return prices
    
    async def _fetch_custom_api_batch(self, target_symbols: Set[str], api_url: str) -> Dict[str, float]:
        """
        从自定义API获取价格
        实现严格匹配和批量获取
        """
        prices = {}
        
        try:
            async with httpx.AsyncClient(timeout=15.0) as client:
                # 尝试批量获取
                if '?' in api_url:
                    url = f"{api_url}&symbols={','.join(target_symbols)}"
                else:
                    url = f"{api_url}?symbols={','.join(target_symbols)}"
                
                response = await client.get(url)
                
                if response.status_code == 200:
                    data = response.json()
                    
                    # 支持多种响应格式
                    if isinstance(data, dict):
                        # 格式1: {"BTCUSDT": 50000, "ETHUSDT": 3000}
                        for symbol in target_symbols:
                            if symbol in data:
                                try:
                                    price = float(data[symbol])
                                    if price > 0:
                                        prices[symbol] = price
                                except (ValueError, TypeError):
                                    continue
                    elif isinstance(data, list):
                        # 格式2: [{"symbol": "BTCUSDT", "price": 50000}, ...]
                        for item in data:
                            if isinstance(item, dict):
                                symbol = item.get("symbol") or item.get("instId")
                                price = item.get("price") or item.get("last")
                                
                                if symbol and price:
                                    # 严格匹配检查
                                    if symbol in target_symbols:
                                        try:
                                            price_float = float(price)
                                            if price_float > 0:
                                                prices[symbol] = price_float
                                        except (ValueError, TypeError):
                                            continue
                    
                    self._log_info(f"自定义API匹配到 {len(prices)} 个目标币种")
                else:
                    self._log_error(f"自定义API返回状态码: {response.status_code}")
                    
        except Exception as e:
            self._log_error(f"自定义API请求失败: {e}")
        
        return prices

# 创建全局实例
price_service = PriceService()

async def fetch_crypto_prices() -> Dict[str, float]:
    """
    异步获取加密货币价格（主入口函数）
    实现Failover机制和严格数据过滤
    """
    return await price_service.fetch_all_prices()

def get_current_prices(db: Session) -> Dict[str, float]:
    """
    获取当前价格（同步版本，用于 API 调用）
    返回最近存储的价格数据
    """
    # 这里可以从数据库中获取最近的价格
    # 目前返回空字典，实际应用中应该从数据库获取
    return {}

async def fetch_kline_data(symbol: str, interval: str = '1h', limit: int = 200) -> list:
    """
    获取K线数据
    :param symbol: 交易对符号，如 BTCUSDT
    :param interval: K线周期，如 1m, 5m, 15m, 1h, 4h, 1d, 1w, 1M
    :param limit: 返回数量，最大1000
    :return: K线数据列表
    """
    # 从配置获取API设置
    api_settings = config_manager.get_api_settings()
    primary_api_url = api_settings.get("primary_api_url", "https://api.binance.com")
    
    # 根据API类型构建正确的K线URL
    if 'okx' in primary_api_url.lower():
        # OKX K线API格式
        # 将BTCUSDT转换为BTC-USDT格式
        if symbol.endswith('USDT'):
            inst_id = f"{symbol[:-4]}-USDT"
        elif symbol.endswith('BTC'):
            inst_id = f"{symbol[:-3]}-BTC"
        elif symbol.endswith('ETH'):
            inst_id = f"{symbol[:-3]}-ETH"
        else:
            inst_id = symbol
        
        # OKX K线周期映射
        okx_interval_map = {
            '1m': '1m', '3m': '3m', '5m': '5m', '15m': '15m', '30m': '30m',
            '1h': '1H', '2h': '2H', '4h': '4H', '6h': '6H', '12h': '12H',
            '1d': '1D', '2d': '2D', '3d': '3D',
            '1w': '1W', '1M': '1M'
        }
        okx_interval = okx_interval_map.get(interval, '1H')
        
        url = f"{primary_api_url}/api/v5/market/history-candles"
        params = {
            'instId': inst_id,
            'bar': okx_interval,
            'limit': min(limit, 300)  # OKX限制最大300
        }
    else:
        # 币安K线API格式
        url = f"{primary_api_url}/api/v3/klines"
        params = {
            'symbol': symbol,
            'interval': interval,
            'limit': min(limit, 1000)  # 币安限制最大1000
        }
    
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
    }
    
    try:
        async with httpx.AsyncClient(timeout=15.0) as client:
            response = await client.get(url, params=params, headers=headers)
            
            if response.status_code == 200:
                data = response.json()
                
                if 'okx' in primary_api_url.lower():
                    # OKX K线数据格式：
                    # {
                    #   "code": "0",
                    #   "msg": "",
                    #   "data": [
                    #     ["1597026383085", "3.721", "3.743", "3.677", "3.708", "8422410", "22698348.04828491"],
                    #     ...
                    #   ]
                    # }
                    
                    # 验证API响应
                    if isinstance(data, dict):
                        if data.get('code') != '0':
                            logger.error(f"OKX API返回错误: {data.get('msg', '未知错误')}")
                            return []
                        klines_data = data.get('data', [])
                    else:
                        klines_data = data
                    
                    formatted_klines = []
                    for k in klines_data:
                        try:
                            # 验证数据长度和类型
                            if len(k) < 7:
                                logger.warning(f"OKX K线数据格式不完整: {k}")
                                continue
                            
                            # 验证时间戳格式
                            open_time = k[0]
                            if not open_time or not str(open_time).isdigit():
                                logger.warning(f"OKX K线时间戳格式错误: {open_time}")
                                continue
                            
                            formatted_klines.append({
                                'open_time': int(open_time),
                                'open': float(k[1]),
                                'high': float(k[2]),
                                'low': float(k[3]),
                                'close': float(k[4]),
                                'volume': float(k[5]),
                                'quote_volume': float(k[6]),
                                'trades': 0,  # OKX不提供成交笔数
                                'taker_buy_base': 0,  # OKX不提供
                                'taker_buy_quote': 0  # OKX不提供
                            })
                        except (ValueError, TypeError, IndexError) as e:
                            logger.warning(f"OKX K线数据解析失败: {k}, 错误: {e}")
                            continue
                    
                    logger.info(f"成功获取OKX {symbol} {interval} K线数据，共 {len(formatted_klines)} 条")
                else:
                    # 币安K线数据格式
                    formatted_klines = []
                    for k in data:
                        formatted_klines.append({
                            'open_time': k[0],
                            'open': float(k[1]),
                            'high': float(k[2]),
                            'low': float(k[3]),
                            'close': float(k[4]),
                            'volume': float(k[5]),
                            'close_time': k[6],
                            'quote_volume': float(k[7]),
                            'trades': k[8],
                            'taker_buy_base': float(k[9]),
                            'taker_buy_quote': float(k[10])
                        })
                    logger.info(f"成功获取币安 {symbol} {interval} K线数据，共 {len(formatted_klines)} 条")
                
                return formatted_klines
            else:
                logger.error(f"K线API返回状态码: {response.status_code}")
                return []
                
    except Exception as e:
        logger.error(f"获取K线数据失败: {e}")
        return []
