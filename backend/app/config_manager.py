"""配置文件管理器 - 将系统设置存储到本地配置文件"""
import json
import os
from typing import Dict, Any, Optional
from pathlib import Path
from copy import deepcopy
from zoneinfo import ZoneInfo
from datetime import timezone

class ConfigManager:
    """配置文件管理器"""
    
    def __init__(self, config_file: str = "config.json"):
        self.config_file = Path(config_file)
        self.default_config = {
            "api_settings": {
                "primary_api_url": "https://api.binance.com/api/v3/ticker/price",
                "backup_api_url": "",
                "api_key": "",
                "api_secret": ""
            },
            "notification_settings": {
                "api_url": "",
                "auth_token": "",
                "channel": "email"
            },
            "system_settings": {
                "refresh_interval": 5,
                "enable_captcha": False,
                "site_title": "Crypto-info",
                "site_description": "数字货币价格监控和预警系统",
                "log_level": "INFO",
                "enable_logging": True,
                "default_dark_mode": False,
                "timezone": "Asia/Shanghai",
                "backend_port": 8000,
                "frontend_port": 5173
            }
        }
    
    def load_config(self) -> Dict[str, Any]:
        """加载配置文件"""
        try:
            if self.config_file.exists():
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    config = json.load(f)
                    # 确保所有必要的键都存在
                    return self._merge_config(self.default_config, config)
            else:
                # 如果配置文件不存在，创建默认配置
                self.save_config(self.default_config)
                return self.default_config
        except Exception as e:
            print(f"加载配置文件失败: {e}")
            return self.default_config
    
    def save_config(self, config: Dict[str, Any]) -> bool:
        """保存配置文件"""
        try:
            # 确保目录存在
            self.config_file.parent.mkdir(parents=True, exist_ok=True)
            
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(config, f, indent=2, ensure_ascii=False)
            return True
        except Exception as e:
            print(f"保存配置文件失败: {e}")
            return False
    
    def get_api_settings(self) -> Dict[str, Any]:
        """获取API设置"""
        config = self.load_config()
        return config.get("api_settings", self.default_config["api_settings"])
    
    def save_api_settings(self, api_settings: Dict[str, Any]) -> bool:
        """保存API设置"""
        config = self.load_config()
        config["api_settings"] = api_settings
        return self.save_config(config)
    
    def get_notification_settings(self) -> Dict[str, Any]:
        """获取通知设置"""
        config = self.load_config()
        return config.get("notification_settings", self.default_config["notification_settings"])
    
    def save_notification_settings(self, notification_settings: Dict[str, Any]) -> bool:
        """保存通知设置"""
        config = self.load_config()
        config["notification_settings"] = notification_settings
        return self.save_config(config)
    
    def get_system_settings(self) -> Dict[str, Any]:
        """获取系统设置 (融合环境变量优先级)"""
        config = self.load_config()
        settings = config.get("system_settings", self.default_config["system_settings"])
        
        # 如果检测到 Docker 环境注入的端口，强行覆盖 config.json 中的值
        env_backend_port = os.getenv("BACKEND_PORT")
        if env_backend_port:
            settings["backend_port"] = int(env_backend_port)
            
        env_frontend_port = os.getenv("FRONTEND_PORT")
        if env_frontend_port:
            settings["frontend_port"] = int(env_frontend_port)
            
        return settings
    
    def save_system_settings(self, system_settings: Dict[str, Any]) -> bool:
        """保存系统设置（更新而不是覆盖）"""
        config = self.load_config()
        # 使用update而不是直接赋值，保留现有配置
        if "system_settings" not in config:
            config["system_settings"] = {}
        config["system_settings"].update(system_settings)
        return self.save_config(config)
    
    def _merge_config(self, default: Dict[str, Any], custom: Dict[str, Any]) -> Dict[str, Any]:
        """合并配置，确保所有必要的键都存在"""
        result = deepcopy(default)
        for key, value in custom.items():
            if key in result and isinstance(result[key], dict) and isinstance(value, dict):
                result[key] = self._merge_config(result[key], value)
            else:
                result[key] = value
        return result
    
    def initialize_default_config(self) -> bool:
        """初始化默认配置文件"""
        if not self.config_file.exists():
            return self.save_config(self.default_config)
        return True
    
    def get_timezone(self):
        """获取时区对象"""
        settings = self.get_system_settings()
        tz_str = settings.get("timezone", "Asia/Shanghai")
        try:
            return ZoneInfo(tz_str)
        except Exception:
            return timezone.utc

# 全局配置管理器实例
config_manager = ConfigManager("config.json")