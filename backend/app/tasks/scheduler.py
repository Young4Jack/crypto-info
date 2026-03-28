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
        active_alerts = []
        crypto_symbols = set()
        
        db = SessionLocal()
        try:
            alerts = db.query(PriceAlert).filter(PriceAlert.is_active == True).all()
            for alert in alerts:
                crypto = db.query(Cryptocurrency).filter(Cryptocurrency.id == alert.crypto_id).first()
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
        
        prices = await fetch_crypto_prices()
        if not prices:
            return
        
        alerts_to_update = []
        alerts_to_notify = []
        
        # 获取当前时间（带时区用于入库，去时区用于安全计算）
        now_aware = datetime.now(config_manager.get_timezone())
        now_naive = now_aware.replace(tzinfo=None)
        
        for alert_data in active_alerts:
            current_price = prices.get(alert_data['crypto_symbol'])
            if current_price is None:
                continue
            
            # 1. 拦截器：校验通知次数上限
            if alert_data['notified_count'] >= alert_data['max_notifications']:
                alerts_to_update.append({'id': alert_data['id'], 'is_active': False})
                continue
            
            # 2. 安全计算时间差：强制抹除时区差异
            time_since_last = None
            if alert_data['last_triggered_at'] is not None:
                last_triggered_naive = alert_data['last_triggered_at'].replace(tzinfo=None)
                time_since_last = (now_naive - last_triggered_naive).total_seconds() / 60
            
            should_notify = False
            
            # 3. 核心分流判定
            if not alert_data['is_continuous'] and alert_data['notified_count'] > 0:
                # 模式1后续触发：只看时间
                if time_since_last is not None and time_since_last >= alert_data['interval_minutes']:
                    should_notify = True
            else:
                # 模式2或首次触发：先看时间，再看价格
                time_condition_met = False
                if alert_data['last_triggered_at'] is None:
                    time_condition_met = True
                elif time_since_last is not None and time_since_last >= alert_data['interval_minutes']:
                    time_condition_met = True
                
                if time_condition_met:
                    if alert_data['alert_type'] == AlertType.ABOVE:
                        should_notify = current_price > alert_data['threshold_price']
                    elif alert_data['alert_type'] == AlertType.BELOW:
                        should_notify = current_price < alert_data['threshold_price']
                    elif alert_data['alert_type'] == AlertType.AMPLITUDE:
                        if alert_data['base_price'] and alert_data['threshold_value']:
                            amplitude = abs(current_price - alert_data['base_price']) / alert_data['base_price'] * 100
                            should_notify = amplitude >= alert_data['threshold_value']
                    elif alert_data['alert_type'] == AlertType.PERCENT_UP:
                        if alert_data['base_price'] and alert_data['threshold_value']:
                            percent_change = (current_price - alert_data['base_price']) / alert_data['base_price'] * 100
                            should_notify = percent_change >= alert_data['threshold_value']
                    elif alert_data['alert_type'] == AlertType.PERCENT_DOWN:
                        if alert_data['base_price'] and alert_data['threshold_value']:
                            percent_change = (alert_data['base_price'] - current_price) / alert_data['base_price'] * 100
                            should_notify = percent_change >= alert_data['threshold_value']
            
            # 4. 执行更新
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
                alerts_to_update.append({
                    'id': alert_data['id'],
                    'notified_count': alert_data['notified_count'] + 1,
                    'last_triggered_at': now_aware
                })
        
        if alerts_to_update or alerts_to_notify:
            db = SessionLocal()
            try:
                for update_data in alerts_to_update:
                    alert = db.query(PriceAlert).filter(PriceAlert.id == update_data['id']).first()
                    if alert:
                        for key, value in update_data.items():
                            if key != 'id':
                                setattr(alert, key, value)
                
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
            
    except Exception as e:
        # 取消静默，强制暴露崩溃原因
        logger.error(f"价格检查任务运行崩溃: {e}", exc_info=True)

def start_scheduler():
    if scheduler.running:
        print("调度器已在运行中")
        return
    system_settings = config_manager.get_system_settings()
    refresh_interval = system_settings.get('refresh_interval', 5)
    
    scheduler.add_job(
        price_check_job,
        trigger=IntervalTrigger(seconds=refresh_interval),
        id='price_check_job',
        name='价格检查任务',
        replace_existing=True
    )
    scheduler.start()
    print("定时任务调度器已启动")
    print(f"价格检查任务: 每{refresh_interval}秒执行一次")

def shutdown_scheduler():
    if scheduler.running:
        scheduler.shutdown()
        print("定时任务调度器已关闭")

def get_scheduler_status():
    if not scheduler.running:
        return {"status": "stopped", "jobs": []}
    
    jobs = []
    for job in scheduler.get_jobs():
        jobs.append({
            "id": job.id,
            "name": job.name,
            "next_run": str(job.next_run_time) if job.next_run_time else None
        })
    return {"status": "running", "jobs": jobs}