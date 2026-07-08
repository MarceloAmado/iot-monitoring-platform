"""
Servicio de WebSocket con Socket.IO para tiempo real.

Emite eventos a los clientes frontend cuando:
- Llega una nueva lectura de sensor (new_reading)
- Un device actualiza su estado vía heartbeat (device_status)
- Se dispara una alerta (alert_triggered)

Usa rooms por device_id para que cada cliente solo reciba
los eventos de los devices que está observando.
"""

import asyncio
import logging
import socketio

from app.core.config import settings

logger = logging.getLogger(__name__)

# Crear servidor Socket.IO
sio = socketio.AsyncServer(
    async_mode="asgi",
    cors_allowed_origins=settings.cors_origins_list,
    logger=False,
    engineio_logger=False,
)

# ASGI app para montar en FastAPI
socket_app = socketio.ASGIApp(sio, socketio_path="/ws/socket.io")


# ============================================
# Event Handlers
# ============================================


@sio.event
async def connect(sid, environ):
    """Cliente conectado."""
    logger.info(f"[WS] Cliente conectado: {sid}")


@sio.event
async def disconnect(sid):
    """Cliente desconectado."""
    logger.info(f"[WS] Cliente desconectado: {sid}")


@sio.event
async def join_device(sid, data):
    """
    Cliente se suscribe a updates de un device específico.

    Args:
        data: {"device_id": 1}
    """
    device_id = data.get("device_id")
    if device_id:
        room = f"device:{device_id}"
        sio.enter_room(sid, room)
        logger.debug(f"[WS] {sid} joined room {room}")


@sio.event
async def leave_device(sid, data):
    """
    Cliente se desuscribe de updates de un device.

    Args:
        data: {"device_id": 1}
    """
    device_id = data.get("device_id")
    if device_id:
        room = f"device:{device_id}"
        sio.leave_room(sid, room)
        logger.debug(f"[WS] {sid} left room {room}")


@sio.event
async def join_dashboard(sid, data=None):
    """Cliente se suscribe al room global del dashboard."""
    sio.enter_room(sid, "dashboard")
    logger.debug(f"[WS] {sid} joined dashboard room")


@sio.event
async def leave_dashboard(sid, data=None):
    """Cliente se desuscribe del room del dashboard."""
    sio.leave_room(sid, "dashboard")
    logger.debug(f"[WS] {sid} left dashboard room")


# ============================================
# Emit Functions (llamadas desde endpoints)
# ============================================


async def emit_new_reading(device_id: int, reading_data: dict):
    """
    Emite un evento new_reading al room del device y al dashboard.

    Args:
        device_id: ID del device que envió la lectura
        reading_data: Datos del reading (id, timestamp, data_payload, quality_score)
    """
    payload = {"device_id": device_id, **reading_data}

    # Al room del device específico
    await sio.emit("new_reading", payload, room=f"device:{device_id}")

    # Al dashboard global
    await sio.emit("new_reading", payload, room="dashboard")


async def emit_device_status(device_id: int, status_data: dict):
    """
    Emite un evento device_status cuando un device actualiza su estado.

    Args:
        device_id: ID del device
        status_data: Datos de estado (is_online, last_seen_at, firmware_version, etc.)
    """
    payload = {"device_id": device_id, **status_data}
    await sio.emit("device_status", payload, room=f"device:{device_id}")
    await sio.emit("device_status", payload, room="dashboard")


async def emit_alert_triggered(device_id: int, alert_data: dict):
    """
    Emite un evento alert_triggered cuando se activa una alerta.

    Args:
        device_id: ID del device relacionado
        alert_data: Datos de la alerta (alert_id, rule_name, severity, etc.)
    """
    payload = {"device_id": device_id, **alert_data}
    await sio.emit("alert_triggered", payload, room=f"device:{device_id}")
    await sio.emit("alert_triggered", payload, room="dashboard")


def emit_alerts_triggered_sync(alerts) -> None:
    """
    Wrapper síncrono para emitir alert_triggered desde background tasks
    y jobs de APScheduler (contextos sin event loop propio).

    El emit es best-effort: un fallo del WebSocket nunca debe afectar
    el flujo que disparó la alerta.

    Args:
        alerts: Lista de AlertHistory ya persistidos (con alert_rule cargada)
    """
    if not alerts:
        return

    try:
        loop = asyncio.new_event_loop()
        for alert in alerts:
            rule = getattr(alert, "alert_rule", None)
            loop.run_until_complete(emit_alert_triggered(alert.device_id, {
                "alert_id": alert.id,
                "rule_name": rule.name if rule else None,
                "check_type": rule.check_type if rule else None,
                "message": alert.message,
                "value_observed": alert.value_observed,
                "triggered_at": alert.triggered_at.isoformat() if alert.triggered_at else None,
            }))
        loop.close()
    except Exception as e:
        logger.debug(f"[WS] emit alert_triggered falló (no crítico): {e}")
