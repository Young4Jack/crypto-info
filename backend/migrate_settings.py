#!/usr/bin/env python3
"""将数据库中的设置数据迁移到配置文件，并删除相关表"""
import sys
import os
from pathlib import Path

# 添加项目根目录到Python路径
sys.path.append(str(Path(__file__).parent))

from app.database import SessionLocal, engine
from app.models.api_setting import ApiSetting
from app.models.system_setting import NotificationSetting, SystemSetting
from app.config_manager import config_manager

def migrate_settings_to_config():
    """将数据库中的设置迁移到配置文件"""
    db = SessionLocal()
    try:
        print("开始迁移设置数据到配置文件...")
        
        # 1. 迁移API设置
        print("迁移API设置...")
        api_setting = db.query(ApiSetting).first()
        if api_setting:
            api_settings = {
                "primary_api_url": api_setting.primary_api_url or "https://api.binance.com/api/v3/ticker/price",
                "backup_api_url": api_setting.backup_api_url or "",
                "api_key": api_setting.api_key or "",
                "api_secret": api_setting.api_secret or ""
            }
            config_manager.save_api_settings(api_settings)
            print(f"  - 已保存API设置: {api_settings['primary_api_url']}")
        else:
            print("  - 数据库中没有API设置，使用默认值")
        
        # 2. 迁移通知设置
        print("迁移通知设置...")
        notification_setting = db.query(NotificationSetting).first()
        if notification_setting:
            notification_settings = {
                "api_url": notification_setting.api_url or "",
                "auth_token": notification_setting.auth_token or "",
                "channel": notification_setting.channel or "email"
            }
            config_manager.save_notification_settings(notification_settings)
            print(f"  - 已保存通知设置: {notification_settings['api_url']}")
        else:
            print("  - 数据库中没有通知设置，使用默认值")
        
        # 3. 迁移系统设置
        print("迁移系统设置...")
        system_setting = db.query(SystemSetting).first()
        if system_setting:
            system_settings = {
                "refresh_interval": system_setting.refresh_interval or 5,
                "enable_captcha": system_setting.enable_captcha or False,
                "site_title": system_setting.site_title or "Crypto-info",
                "site_description": system_setting.site_description or "数字货币价格监控和预警系统"
            }
            config_manager.save_system_settings(system_settings)
            print(f"  - 已保存系统设置: {system_settings['site_title']}")
        else:
            print("  - 数据库中没有系统设置，使用默认值")
        
        print("设置数据迁移完成！")
        return True
        
    except Exception as e:
        print(f"迁移过程中出错: {e}")
        return False
    finally:
        db.close()

def delete_setting_tables():
    """删除设置相关的数据库表"""
    try:
        print("开始删除设置相关的数据库表...")
        
        # 使用SQLAlchemy的text()函数执行SQL
        from sqlalchemy import text
        
        with engine.connect() as conn:
            # 删除API设置表
            conn.execute(text("DROP TABLE IF EXISTS api_settings"))
            print("  - 已删除 api_settings 表")
            
            # 删除通知设置表
            conn.execute(text("DROP TABLE IF EXISTS notification_settings"))
            print("  - 已删除 notification_settings 表")
            
            # 删除系统设置表
            conn.execute(text("DROP TABLE IF EXISTS system_settings"))
            print("  - 已删除 system_settings 表")
            
            conn.commit()
        
        print("设置相关表删除完成！")
        return True
        
    except Exception as e:
        print(f"删除表时出错: {e}")
        return False

def main():
    """主函数"""
    print("=" * 50)
    print("设置数据迁移工具")
    print("=" * 50)
    
    # 1. 迁移设置到配置文件
    if not migrate_settings_to_config():
        print("设置迁移失败！")
        return
    
    # 2. 删除数据库中的设置表
    if not delete_setting_tables():
        print("删除表失败！")
        return
    
    print("\n" + "=" * 50)
    print("迁移完成！")
    print("设置数据已从数据库迁移到配置文件：backend/config.json")
    print("数据库中的设置相关表已删除")
    print("=" * 50)

if __name__ == "__main__":
    main()