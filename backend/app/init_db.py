"""数据库初始化脚本"""
from sqlalchemy.orm import Session
from app.database import SessionLocal, engine
from app.models import user, cryptocurrency, alert, asset
from app.database import Base
from passlib.context import CryptContext

# 密码加密上下文
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def init_db():
    """初始化数据库"""
    db = SessionLocal()
    try:
        # 检查是否已有用户
        existing_user = db.query(user.User).first()
        if existing_user:
            print("数据库已有数据，跳过初始化")
            return
        
        # 创建默认管理员用户
        hashed_password = pwd_context.hash("admin123")
        admin_user = user.User(
            username="admin",
            email="admin@crypto.local",
            hashed_password=hashed_password,
            is_active=True
        )
        db.add(admin_user)
        db.flush()  # 获取用户ID
        
        # 创建默认监控币种
        cryptos = [
            cryptocurrency.Cryptocurrency(
                symbol="BTCUSDT",
                name="Bitcoin",
                is_active=True
            ),
            cryptocurrency.Cryptocurrency(
                symbol="ETHUSDT",
                name="Ethereum",
                is_active=True
            )
        ]
        db.add_all(cryptos)
        
        # 提交事务
        db.commit()
        print("数据库初始化成功！")
        print(f"创建管理员用户: admin@crypto.local / admin123")
        print(f"创建监控币种: BTCUSDT (Bitcoin), ETHUSDT (Ethereum)")
        
    except Exception as e:
        db.rollback()
        print(f"数据库初始化失败: {e}")
        raise
    finally:
        db.close()

if __name__ == "__main__":
    init_db()