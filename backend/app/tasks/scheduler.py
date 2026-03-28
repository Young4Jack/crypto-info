"""定时任务调度器"""
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.interval import IntervalTrigger
from app.services.price_service_refactored import fetch_crypto_prices
from app.config_manager import config_manager
from app.models.alert import PriceAlert, AlertType
from app.models.cryptocurrency import Cryptocurrency
from app.models.user import User
from app.database import SessionLocal
from app.services.notification_service import send_webhook_alert
from datetime import datetime, timedelta
import logging
import asyncio

# 配置日志
logger = logging.getLogger(__name__)

# 创建调度器实例
scheduler = AsyncIOScheduler()

async def price_check_job():
    """价格检查定时任务 - 重构版本"""
    try:
        # 第一步：短读事务 - 快速查询数据库，提取所有 Active 规则
        active_alerts = []
        crypto_symbols = set()
        
        db = SessionLocal()
        try:
            # 获取所有激活的预警规则
            alerts = db.query(PriceAlert).filter(
                PriceAlert.is_active == True
            ).all()
            
            for alert in alerts:
                # 获取对应的币种信息
                crypto = db.query(Cryptocurrency).filter(
                    Cryptocurrency.id == alert.crypto_id
                ).first()
                
                if crypto and crypto.symbol:
                    active_alerts.append({
                        'id': alert.id,
                        'user_id': alert.user_id,
                        'crypto_id': alert.crypto_id,
                        'crypto_symbol': crypto.symbol,
                        'crypto_name': crypto.name,
                        'alert_type': alert.alert_type,
                        'threshold_price': alert.threshold_price,
                        'base_price': alert.base_price,
                        'threshold_value': alert.threshold_value,
                        'is_continuous': alert.is_continuous,
                        'interval_minutes': alert.interval_minutes,
                        'max_notifications': alert.max_notifications,
                        'notified_count': alert.notified_count,
                        'last_triggered_at': alert.last_triggered_at
                    })
                    crypto_symbols.add(crypto.symbol)
        finally:
            db.close()
        
        if not active_alerts or not crypto_symbols:
            return
        
        # 第二步：无锁网络 IO - 在内存中提取去重后的币种，请求外部 API 获取最新价格
        prices = await fetch_crypto_prices()
        
        if not prices:
            return
        
        # 第三步：内存计算 - 在内存中将最新价格与预警规则比对
        alerts_to_update = []
        alerts_to_notify = []
        
        now = datetime.now(config_manager.get_timezone())
        
        for alert_data in active_alerts:
            current_price = prices.get(alert_data['crypto_symbol'])
            if current_price is None:
                continue
            
            # 检查是否应该触发预警
            should_trigger = False
            
            # 根据 alert_type 判断触发条件
            if alert_data['alert_type'] == AlertType.ABOVE:
                should_trigger = current_price > alert_data['threshold_price']
            elif alert_data['alert_type'] == AlertType.BELOW:
                should_trigger = current_price < alert_data['threshold_price']
            elif alert_data['alert_type'] == AlertType.AMPLITUDE:
                # 振幅预警
                if alert_data['base_price'] and alert_data['threshold_value']:
                    amplitude = abs(current_price - alert_data['base_price']) / alert_data['base_price'] * 100
                    should_trigger = amplitude >= alert_data['threshold_value']
            elif alert_data['alert_type'] == AlertType.PERCENT_UP:
                # 单向涨幅百分比
                if alert_data['base_price'] and alert_data['threshold_value']:
                    percent_change = (current_price - alert_data['base_price']) / alert_data['base_price'] * 100
                    should_trigger = percent_change >= alert_data['threshold_value']
            elif alert_data['alert_type'] == AlertType.PERCENT_DOWN:
                # 单向跌幅百分比
                if alert_data['base_price'] and alert_data['threshold_value']:
                    percent_change = (alert_data['base_price'] - current_price) / alert_data['base_price'] * 100
                    should_trigger = percent_change >= alert_data['threshold_value']
            
            if not should_trigger:
                continue
            
            # 检查通知次数限制
            if alert_data['notified_count'] >= alert_data['max_notifications']:
                # 达到最大通知次数，标记为完成
                alerts_to_update.append({
                    'id': alert_data['id'],
                    'is_active': False
                })
                continue
            
            # 检查时间间隔
            time_since_last = None
            if alert_data['last_triggered_at'] is not None:
                time_since_last = (now - alert_data['last_triggered_at']).total_seconds() / 60
            
            # 处理空值陷阱：last_triggered_at 为 NULL 时，视为立即触发
            should_notify = False
            if alert_data['last_triggered_at'] is None:
                should_notify = True
            elif time_since_last is not None and time_since_last >= alert_data['interval_minutes']:
                should_notify = True
            
            if should_notify:
                # 根据 is_continuous 区分模式1和模式2
                if alert_data['is_continuous']:
                    # 模式2：持续条件预警 - 每次达到时间间隔后，必须重新比对最新价格
                    # 价格仍然满足条件，触发通知
                    should_notify = True
                else:
                    # 模式1：普通预警带重复提醒 - 第一次触发后，后续的重复通知绝对不请求 API 检查最新价格
                    # 仅凭时间间隔无脑发
                    should_notify = True
            
            if should_notify:
                alerts_to_notify.append({
                    'id': alert_data['id'],
                    'user_id': alert_data['user_id'],
                    'crypto_symbol': alert_data['crypto_symbol'],
                    'crypto_name': alert_data['crypto_name'],
                    'alert_type': alert_data['alert_type'],
                    'threshold_price': alert_data['threshold_price'],
                    'current_price': current_price,
                    'notified_count': alert_data['notified_count']
                })
                
                # 准备更新数据
                alerts_to_update.append({
                    'id': alert_data['id'],
                    'notified_count': alert_data['notified_count'] + 1,
                    'last_triggered_at': now
                })
        
        # 第四步：短写事务 - 使用批量更新迅速修改涉及的记录
        if alerts_to_update or alerts_to_notify:
            db = SessionLocal()
            try:
                # 批量更新预警记录
                for update_data in alerts_to_update:
                    alert = db.query(PriceAlert).filter(PriceAlert.id == update_data['id']).first()
                    if alert:
                        for key, value in update_data.items():
                            if key != 'id':
                                setattr(alert, key, value)
                
                # 发送通知
                for notify_data in alerts_to_notify:
                    try:
                        direction = "高于" if notify_data['alert_type'] == AlertType.ABOVE else "低于"
                        title = f"【价格预警】{notify_data['crypto_name']} 触发阈值"
                        description = "当前价格已达到设定的预警条件"
                        content = f"您监控的 {notify_data['crypto_name']} 当前价格为 {notify_data['current_price']}，已{direction}设定的阈值 {notify_data['threshold_price']}。"
                        
                        await send_webhook_alert(title, description, content, user_id=notify_data['user_id'])
                    except Exception as e:
                        logger.error(f"发送通知失败: {e}")
                
                db.commit()
            except Exception as e:
                db.rollback()
                logger.error(f"更新预警记录失败: {e}")
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