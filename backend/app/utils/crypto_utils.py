"""加密货币工具函数"""

def extract_coin_name_from_symbol(symbol: str) -> str:
    """
    从交易对符号中提取币种名称
    例如：
    - BTCUSDT -> BTC
    - ETHUSDT -> ETH
    - ADAUSDT -> ADA
    - SOLUSDT -> SOL
    """
    if not symbol:
        return ""
    
    symbol = symbol.upper().strip()
    
    # 常见的交易对后缀
    suffixes = ['USDT', 'USDC', 'BTC', 'ETH', 'BNB', 'BUSD']
    
    for suffix in suffixes:
        if symbol.endswith(suffix):
            return symbol[:-len(suffix)]
    
    # 如果没有匹配的后缀，返回原符号
    return symbol

def get_coin_full_name(coin_symbol: str) -> str:
    """
    根据币种符号获取完整名称
    """
    coin_names = {
        'BTC': 'Bitcoin',
        'ETH': 'Ethereum',
        'ADA': 'Cardano',
        'SOL': 'Solana',
        'DOT': 'Polkadot',
        'DOGE': 'Dogecoin',
        'AVAX': 'Avalanche',
        'MATIC': 'Polygon',
        'LINK': 'Chainlink',
        'UNI': 'Uniswap',
        'ATOM': 'Cosmos',
        'FTM': 'Fantom',
        'NEAR': 'NEAR Protocol',
        'ALGO': 'Algorand',
        'XRP': 'Ripple',
        'LTC': 'Litecoin',
        'BCH': 'Bitcoin Cash',
        'FIL': 'Filecoin',
        'TRX': 'TRON',
        'EOS': 'EOS'
    }
    
    return coin_names.get(coin_symbol, coin_symbol)