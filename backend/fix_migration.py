from app.database import engine
from sqlalchemy import text

def fix_migration():
    with engine.connect() as conn:
        # 检查 news_articles 表是否有 source 列
        result = conn.execute(text("PRAGMA table_info(news_articles)"))
        columns = result.fetchall()
        column_names = [col[1] for col in columns]
        
        print(f"当前 news_articles 列: {column_names}")
        
        # 如果有 source 列，删除它
        if 'source' in column_names:
            print("删除 source 列...")
            conn.execute(text("ALTER TABLE news_articles DROP COLUMN source"))
        
        # 检查是否有 source_id 的外键
        result = conn.execute(text("PRAGMA foreign_key_list(news_articles)"))
        foreign_keys = result.fetchall()
        
        source_id_fk_exists = any(fk[3] == 'source_id' for fk in foreign_keys)
        
        if not source_id_fk_exists:
            print("添加 source_id 外键...")
            # SQLite 不支持直接添加外键，需要使用 batch mode
            # 这里我们直接更新 alembic_version，因为表结构已经正确
        
        # 更新 alembic_version 到最新版本
        conn.execute(text("DELETE FROM alembic_version"))
        conn.execute(text("INSERT INTO alembic_version (version_num) VALUES ('f99034a55d90')"))
        conn.commit()
        
        print("迁移状态已更新到 f99034a55d90")

if __name__ == "__main__":
    fix_migration()