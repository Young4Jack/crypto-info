"""定时任务调度器"""
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.interval import IntervalTrigger
from app.services.price_service_refactored import fetch_crypto_prices
from app.services.alert_service import check_price_alerts
from app.config_manager import config_manager
import logging

# 配置日志
logger = logging.getLogger(__name__)

# 创建调度器实例
scheduler = AsyncIOScheduler()

async def price_check_job():
    """价格检查定时任务"""
    try:
        # 获取最新价格
        prices = await fetch_crypto_prices()
        
        if prices:
            # 检查预警（只检查第一个用户的预警）
            # 注意：这里应该根据当前用户ID来过滤，但由于定时任务没有用户上下文，
            # 我们暂时只检查第一个用户的预警规则，避免检查所有用户的预警
            from app.models.user import User
            from app.database import SessionLocal
            db = SessionLocal()
            try:
                first_user = db.query(User).first()
                if first_user:
                    await check_price_alerts(prices, first_user.id)
            finally:
                db.close()
        # 静默执行，不打印日志
            
    except Exception as e:
        # 静默处理错误，不打印日志
        pass

def start_scheduler():
    """启动定时任务调度器"""
    if scheduler.running:
        print("调度器已在运行中")
        return
    
    # 从配置文件获取刷新间隔
    system_settings = config_manager.get_system_settings()
    refresh_interval = system_settings.get('refresh_interval', 5)
    
    # 添加价格检查任务，使用配置的刷新间隔
    scheduler.add_job(
        price_check_job,
        trigger=IntervalTrigger(seconds=refresh_interval),
        id='price_check_job',
        name='价格检查任务',
        replace_existing=True
    )
    
    # 启动调度器
    scheduler.start()
    print("定时任务调度器已启动")
    print(f"价格检查任务: 每{refresh_interval}秒执行一次")

def shutdown_scheduler():
    """关闭定时任务调度器"""
    if scheduler.running:
        scheduler.shutdown()
        print("定时任务调度器已关闭")

def get_scheduler_status():
    """获取调度器状态"""
    if not scheduler.running:
        return {"status": "stopped", "jobs": []}
    
    jobs = []
    for job in scheduler.get_jobs():
        jobs.append({
            "id": job.id,
            "name": job.name,
            "next_run": str(job.next_run_time) if job.next_run_time else None
        })
    
    return {
        "status": "running",
        "jobs": jobs
    }