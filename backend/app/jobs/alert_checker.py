"""
Job periódico para chequear devices offline y disparar alertas.

Utiliza APScheduler para ejecutar tareas en background cada N minutos.
"""

import logging
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.interval import IntervalTrigger

from app.core.database import db_session
from app.services.alert_service import evaluate_all_devices_offline
from app.services.notification_service import send_multiple_alert_notifications

logger = logging.getLogger(__name__)

# Scheduler global
scheduler = BackgroundScheduler()


def check_offline_devices():
    """
    Job que se ejecuta periódicamente para detectar devices offline.

    Este job:
    1. Busca todos los devices activos en la DB
    2. Evalúa reglas de tipo DEVICE_OFFLINE
    3. Dispara alertas si un device no reportó en el tiempo configurado
    4. Envía notificaciones por los canales configurados

    Se ejecuta cada 5 minutos por defecto.
    """
    logger.info("🔍 Iniciando chequeo de devices offline...")

    try:
        with db_session() as db:
            # Evaluar todas las reglas DEVICE_OFFLINE
            stats = evaluate_all_devices_offline(db)

            logger.info(
                f"✓ Chequeo completado - "
                f"Devices chequeados: {stats['total_devices']}, "
                f"Alertas disparadas: {stats['alerts_triggered']}"
            )

            # Si se dispararon alertas, enviar notificaciones
            if stats['alerts_triggered'] > 0 and stats['alert_ids']:
                logger.info(f"📧 Enviando notificaciones para {len(stats['alert_ids'])} alertas...")
                send_multiple_alert_notifications(db, stats['alert_ids'])
                logger.info("✓ Notificaciones enviadas")

                # Push en tiempo real al frontend (best-effort)
                from app.models.alert import AlertHistory
                from app.services.websocket_service import emit_alerts_triggered_sync
                alerts = (
                    db.query(AlertHistory)
                    .filter(AlertHistory.id.in_(stats['alert_ids']))
                    .all()
                )
                emit_alerts_triggered_sync(alerts)

    except Exception as e:
        logger.error(f"❌ Error en job check_offline_devices: {str(e)}", exc_info=True)


def start_scheduler():
    """
    Inicia el scheduler de APScheduler.

    Configura y arranca todos los jobs periódicos.

    **Jobs configurados:**
    - check_offline_devices: Cada 5 minutos
    """
    if scheduler.running:
        logger.warning("⚠️ El scheduler ya está corriendo")
        return

    logger.info("🚀 Iniciando APScheduler...")

    # Job 1: Chequear devices offline cada 5 minutos
    scheduler.add_job(
        func=check_offline_devices,
        trigger=IntervalTrigger(minutes=5),
        id="check_offline_devices",
        name="Chequear devices offline",
        replace_existing=True,
    )

    # Iniciar scheduler
    scheduler.start()

    logger.info("✓ APScheduler iniciado correctamente")
    logger.info("  • Job 'check_offline_devices': cada 5 minutos")


def stop_scheduler():
    """
    Detiene el scheduler de APScheduler.

    Debe llamarse al cerrar la aplicación para liberar recursos.
    """
    if not scheduler.running:
        logger.warning("⚠️ El scheduler no está corriendo")
        return

    logger.info("🛑 Deteniendo APScheduler...")
    scheduler.shutdown(wait=True)
    logger.info("✓ APScheduler detenido correctamente")
