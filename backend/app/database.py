"""数据库连接配置"""
from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker, DeclarativeBase
from sqlalchemy.pool import NullPool
from app.config import settings

# 创建数据库引擎，禁用连接池以避免超时问题
engine = create_engine(
    settings.DATABASE_URL,
    connect_args={"check_same_thread": False} if "sqlite" in settings.DATABASE_URL else {},
    poolclass=NullPool  # 禁用连接池，每次请求使用独立连接
)

# 针对SQLite数据库，设置WAL模式和超时参数
if "sqlite" in settings.DATABASE_URL:
    @event.listens_for(engine, "connect")
    def set_sqlite_pragma(dbapi_connection, connection_record):
        cursor = dbapi_connection.cursor()
        # 启用WAL模式以支持并发读写
        cursor.execute("PRAGMA journal_mode=WAL")
        # 设置同步模式为NORMAL，提高性能
        cursor.execute("PRAGMA synchronous=NORMAL")
        # 设置超时时间（毫秒）
        cursor.execute("PRAGMA busy_timeout=20000")
        cursor.close()

# 创建会话工厂
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# 创建基础模型类
class Base(DeclarativeBase):
    pass

# 获取数据库会话的依赖函数
def get_db():
    """获取数据库会话"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
