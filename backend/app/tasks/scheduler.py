"""定时任务调度器 - 价格检查与预警引擎"""
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.interval import IntervalTrigger
from app.services.price_service_refactored import fetch_crypto_prices
from app.config_manager import config_manager
from app.models.alert import PriceAlert, AlertType
from app.models.alert_history import AlertHistory, AlertHistoryStatus
from app.models.cryptocurrency import Cryptocurrency
from app.models.user import User
from app.database import SessionLocal
from app.services.notification_service import send_webhook_alert, send_failure_alert, MAX_RETRY_COUNT
from datetime import datetime, timedelta
import logging
import asyncio

logger = logging.getLogger(__name__)

scheduler = AsyncIOScheduler()

MAX_RETRY_COUNT = 3

def _get_alert_direction_text(alert_type: AlertType) -> str:
    """根据预警类型返回准确的方向描述文字"""
    direction_map = {
        AlertType.ABOVE: "高于",
        AlertType.BELOW: "低于",
        AlertType.AMPLITUDE: "振幅达到",
        AlertType.PERCENT_UP: "涨幅达到",
        AlertType.PERCENT_DOWN: "跌幅达到",
    }
    return direction_map.get(alert_type, "触发")

def _get_alert_description(alert_type: AlertType) -> str:
    """根据预警类型返回准确的描述"""
    desc_map = {
        AlertType.ABOVE: "价格已超过设定阈值",
        AlertType.BELOW: "价格已低于设定阈值",
        AlertType.AMPLITUDE: "价格振幅已达到设定阈值",
        AlertType.PERCENT_UP: "涨幅已达到设定阈值",
        AlertType.PERCENT_DOWN: "跌幅已达到设定阈值",
    }
    return desc_map.get(alert_type, "触发预警条件")

def _build_alert_content(alert_type: AlertType, crypto_name: str, current_price: float, threshold_price: float, base_price: float = None, threshold_value: float = None) -> str:
    """构建完整的通知内容"""
    direction = _get_alert_direction_text(alert_type)

    if alert_type in (AlertType.AMPLITUDE, AlertType.PERCENT_UP, AlertType.PERCENT_DOWN):
        content = f"您监控的 {crypto_name} 基准价为 {base_price}，当前价格为 {current_price}，已{direction}{threshold_value}%。"
    else:
        content = f"您监控的 {crypto_name} 当前价格为 {current_price}，已{direction}设定的阈值 {threshold_price}。"
    return content

async def price_check_job():
    """价格检查定时任务"""
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
                        'crypto_id': crypto.id,
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
                        'last_triggered_at': alert.last_triggered_at,
                        'notification_channel': alert.notification_channel,
                        'notification_group': alert.notification_group
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

            # 2. 安全计算时间差
            time_since_last = None
            if alert_data['last_triggered_at'] is not None:
                last_triggered_naive = alert_data['last_triggered_at'].replace(tzinfo=None)
                time_since_last = (now_naive - last_triggered_naive).total_seconds() / 60

            should_notify = False

            # 3. 核心分流判定
            if not alert_data['is_continuous'] and alert_data['notified_count'] > 0:
                # 非连续模式后续触发：只看时间
                if time_since_last is not None and time_since_last >= alert_data['interval_minutes']:
                    should_notify = True
            else:
                # 连续模式或首次触发：先看时间，再看价格
                time_condition_met = False
                if alert_data['last_triggered_at'] is None:
                    time_condition_met = True
                elif time_since_last is not None and time_since_last >= alert_data['interval_minutes']:
                    time_condition_met = True

                if time_condition_met:
                    at = alert_data['alert_type']
                    if at == AlertType.ABOVE:
                        should_notify = current_price > alert_data['threshold_price']
                    elif at == AlertType.BELOW:
                        should_notify = current_price < alert_data['threshold_price']
                    elif at == AlertType.AMPLITUDE:
                        if alert_data['base_price'] and alert_data['threshold_value']:
                            amplitude = abs(current_price - alert_data['base_price']) / alert_data['base_price'] * 100
                            should_notify = amplitude >= alert_data['threshold_value']
                    elif at == AlertType.PERCENT_UP:
                        if alert_data['base_price'] and alert_data['threshold_value']:
                            pct = (current_price - alert_data['base_price']) / alert_data['base_price'] * 100
                            should_notify = pct >= alert_data['threshold_value']
                    elif at == AlertType.PERCENT_DOWN:
                        if alert_data['base_price'] and alert_data['threshold_value']:
                            pct = (alert_data['base_price'] - current_price) / alert_data['base_price'] * 100
                            should_notify = pct >= alert_data['threshold_value']

            # 4. 收集待通知和待更新的预警
            if should_notify:
                alerts_to_notify.append({
                    'id': alert_data['id'],
                    'user_id': alert_data['user_id'],
                    'crypto_id': alert_data['crypto_id'],
                    'crypto_symbol': alert_data['crypto_symbol'],
                    'crypto_name': alert_data['crypto_name'],
                    'alert_type': alert_data['alert_type'],
                    'threshold_price': alert_data['threshold_price'],
                    'base_price': alert_data.get('base_price'),
                    'threshold_value': alert_data.get('threshold_value'),
                    'current_price': current_price,
                    'notified_count': alert_data['notified_count'],
                    'notification_channel': alert_data.get('notification_channel'),
                    'notification_group': alert_data.get('notification_group')
                })
                alerts_to_update.append({
                    'id': alert_data['id'],
                    'notified_count': alert_data['notified_count'] + 1,
                    'last_triggered_at': now_aware
                })

        # 5. 批量更新数据库 + 发送通知 + 写入历史记录
        if alerts_to_update or alerts_to_notify:
            db = SessionLocal()
            try:
                # 5.1 更新预警状态
                for update_data in alerts_to_update:
                    alert = db.query(PriceAlert).filter(PriceAlert.id == update_data['id']).first()
                    if alert:
                        for key, value in update_data.items():
                            if key != 'id':
                                setattr(alert, key, value)

                # 5.2 发送通知 + 写入 AlertHistory
                for notify_data in alerts_to_notify:
                    alert_type = notify_data['alert_type']
                    title = f"【价格预警】{notify_data['crypto_name']} 触发阈值"
                    description = _get_alert_description(alert_type)
                    content = _build_alert_content(
                        alert_type,
                        notify_data['crypto_name'],
                        notify_data['current_price'],
                        notify_data['threshold_price'],
                        notify_data.get('base_price'),
                        notify_data.get('threshold_value')
                    )

                    # 解析渠道配置
                    channel_name = notify_data.get('notification_channel')
                    group_name = notify_data.get('notification_group')
                    channel_config = None

                    if channel_name:
                        ch = config_manager.get_channel_by_name(channel_name)
                        if ch:
                            resolved_group = group_name if group_name else ch.get("default_group", "yes")
                            channel_config = {
                                "api_url": ch["api_url"],
                                "auth_token": ch.get("auth_token", ""),
                                "group": resolved_group
                            }
                        else:
                            logger.warning(f"预警 {notify_data['id']} 指定的渠道 '{channel_name}' 不存在，使用默认渠道")

                    try:
                        await send_webhook_alert(title, description, content, user_id=notify_data['user_id'], channel_config=channel_config)
                        history_status = AlertHistoryStatus.NOTIFIED
                        notification_sent = now_aware
                        logger.info(f"预警通知发送成功: {title}")
                    except Exception as e:
                        logger.error(f"发送通知失败: {e}")
                        history_status = AlertHistoryStatus.FAILED
                        notification_sent = None

                        # 失败达到最大重试次数，自动停用预警并发送告警
                        if notify_data['notified_count'] + 1 >= MAX_RETRY_COUNT:
                            alerts_to_update.append({'id': notify_data['id'], 'is_active': False})
                            await send_failure_alert(
                                notify_data['crypto_name'],
                                str(e)
                            )
                            logger.warning(f"预警 {notify_data['id']} 因连续{MAX_RETRY_COUNT}次推送失败已被自动停用")

                    # 写入 AlertHistory 记录
                    history = AlertHistory(
                        alert_id=notify_data['id'],
                        user_id=notify_data['user_id'],
                        crypto_id=notify_data['crypto_id'],
                        alert_type=alert_type.value if hasattr(alert_type, 'value') else str(alert_type),
                        threshold_price=notify_data['threshold_price'],
                        trigger_price=notify_data['current_price'],
                        status=history_status,
                        notification_channel=notify_data.get('notification_channel'),
                        notification_group=notify_data.get('notification_group'),
                        webhook_url=channel_config.get('api_url') if channel_config else None,
                        notification_sent=notification_sent,
                        created_at=now_aware
                    )
                    db.add(history)

                db.commit()
            except Exception as e:
                db.rollback()
                logger.error(f"更新预警记录失败: {e}", exc_info=True)
            finally:
                db.close()

    except Exception as e:
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
