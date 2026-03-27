#!/usr/bin/env python3
"""初始化系统设置"""
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.database import SessionLocal
from app.models.system_setting import SystemSetting
from app.models.user import User

def init_system_settings():
    """初始化系统设置"""
    db = SessionLocal()
    try:
        # 获取第一个用户
        first_user = db.query(User).first()
        
        if not first_user:
            print("没有找到用户，请先创建用户")
            return
        
        # 检查是否已存在系统设置
        existing_setting = db.query(SystemSetting).filter(
            SystemSetting.user_id == first_user.id
        ).first()
        
        if existing_setting:
            print(f"系统设置已存在，用户ID: {first_user.id}")
            print(f"网站标题: {existing_setting.site_title}")
            print(f"网站描述: {existing_setting.site_description}")
            return
        
        # 创建默认系统设置
        default_setting = SystemSetting(
            user_id=first_user.id,
            refresh_interval=5,
            enable_captcha=False,
            site_title="Crypto-info",
            site_description="数字货币价格监控和预警系统"
        )
        
        db.add(default_setting)
        db.commit()
        db.refresh(default_setting)
        
        print(f"系统设置初始化成功，用户ID: {first_user.id}")
        print(f"网站标题: {default_setting.site_title}")
        print(f"网站描述: {default_setting.site_description}")
        
    except Exception as e:
        print(f"初始化系统设置失败: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    init_system_settings()