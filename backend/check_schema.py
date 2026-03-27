from app.database import engine
from sqlalchemy import inspect

inspector = inspect(engine)

# 检查 news_articles 表结构
print("=== news_articles 表结构 ===")
for col in inspector.get_columns('news_articles'):
    print(f"  {col['name']}: {col['type']}")

# 检查 news_sources 表结构
print("\n=== news_sources 表结构 ===")
for col in inspector.get_columns('news_sources'):
    print(f"  {col['name']}: {col['type']}")

# 检查外键
print("\n=== news_articles 外键 ===")
for fk in inspector.get_foreign_keys('news_articles'):
    print(f"  {fk}")