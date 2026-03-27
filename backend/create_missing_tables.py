#!/usr/bin/env python3
"""创建缺失的数据库表"""
import sqlite3
import os

def create_missing_tables():
    """创建缺失的数据库表"""
    db_path = 'crypto.db'
    
    # 连接数据库
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    try:
        # 创建 system_settings 表
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS system_settings (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL UNIQUE,
                refresh_interval INTEGER DEFAULT 5,
                enable_captcha BOOLEAN DEFAULT 0,
                site_title VARCHAR(100) DEFAULT 'Crypto-info',
                site_description VARCHAR(500) DEFAULT '数字货币价格监控和预警系统',
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(id)
            )
        ''')
        print("✅ 创建 system_settings 表成功")
        
        # 创建 api_settings 表
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS api_settings (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL UNIQUE,
                primary_api_url VARCHAR(500),
                backup_api_url VARCHAR(500),
                api_key VARCHAR(500),
                api_secret VARCHAR(500),
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(id)
            )
        ''')
        print("✅ 创建 api_settings 表成功")
        
        # 创建 notification_settings 表
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS notification_settings (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL UNIQUE,
                api_url VARCHAR(500),
                auth_token VARCHAR(500),
                channel VARCHAR(50) DEFAULT 'email',
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(id)
            )
        ''')
        print("✅ 创建 notification_settings 表成功")
        
        # 提交更改
        conn.commit()
        print("\n🎉 所有缺失的表已创建完成！")
        
    except Exception as e:
        print(f"❌ 创建表时出错: {e}")
        conn.rollback()
    finally:
        conn.close()

if __name__ == "__main__":
    create_missing_tables()