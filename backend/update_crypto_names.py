#!/usr/bin/env python3
"""更新数据库中的币种名称"""
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.database import SessionLocal
from app.models.cryptocurrency import Cryptocurrency
from app.utils.crypto_utils import extract_coin_name_from_symbol, get_coin_full_name

def update_cryptocurrency_names():
    """更新数据库中的币种名称"""
    db = SessionLocal()
    try:
        # 获取所有币种
        cryptos = db.query(Cryptocurrency).all()
        
        print(f"找到 {len(cryptos)} 个币种记录")
        
        updated_count = 0
        
        for crypto in cryptos:
            # 从交易对中提取币种名称
            extracted_name = extract_coin_name_from_symbol(crypto.symbol)
            full_name = get_coin_full_name(extracted_name)
            
            # 检查是否需要更新
            if crypto.name != extracted_name or crypto.display_name != full_name:
                old_name = crypto.name
                old_display_name = crypto.display_name
                
                crypto.name = extracted_name
                crypto.display_name = full_name
                
                print(f"更新 {crypto.symbol}: {old_name} -> {extracted_name}, {old_display_name} -> {full_name}")
                updated_count += 1
            else:
                print(f"跳过 {crypto.symbol}: 名称已正确")
        
        # 提交更改
        db.commit()
        print(f"\n完成！更新了 {updated_count} 个币种记录")
        
    except Exception as e:
        print(f"更新过程中出错: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    update_cryptocurrency_names()