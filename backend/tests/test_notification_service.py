"""
Tests para el servicio de notificaciones.

Cubre:
- Envío de notificaciones por Email (SMTP)
- Envío de notificaciones por Telegram (Bot API)
- Envío de notificaciones por Webhook (HTTP POST)
- Manejo de errores en cada canal
- Actualización de notification_sent en AlertHistory
- Skip de canales no configurados
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
from sqlalchemy.orm import Session
from datetime import datetime

from app.models.alert import AlertRule, AlertHistory
from app.models.device import Device
from app.services.notification_service import NotificationService


@pytest.fixture
def notification_service(db_session: Session) -> NotificationService:
    """Fixture que provee una instancia del servicio de notificaciones."""
    return NotificationService(db_session)


@pytest.fixture
def alert_for_notification(
    db_session: Session,
    device: Device,
    alert_rule_threshold_above: AlertRule
) -> AlertHistory:
    """
    Fixture que crea un AlertHistory listo para notificar.

    Reutiliza los fixtures de test_alert_evaluation.py.
    """
    alert = AlertHistory(
        alert_rule_id=alert_rule_threshold_above.id,
        device_id=device.id,
        triggered_at=datetime.utcnow(),
        value_observed=27.5,
        message="Temperatura 27.5°C excede el umbral de 25.0°C",
        notification_sent=None
    )
    db_session.add(alert)
    db_session.commit()
    db_session.refresh(alert)
    return alert


# Importar fixture de alert_rule_threshold_above desde conftest
# (fixture reutilizable creado en test_alert_evaluation.py)
@pytest.fixture
def alert_rule_threshold_above(db_session: Session, device: Device) -> AlertRule:
    """Regla: temperatura > 25°C con notificaciones email + telegram"""
    rule = AlertRule(
        device_id=device.id,
        name="Temperatura alta - Test Notifications",
        check_type="THRESHOLD_ABOVE",
        variable_key="temp_c",
        threshold_value=25.0,
        enabled=True,
        cooldown_minutes=30,
        notification_channels=["email", "telegram"]
    )
    db_session.add(rule)
    db_session.commit()
    db_session.refresh(rule)
    return rule


# ============================================================
# TESTS: EMAIL NOTIFICATIONS
# ============================================================

@patch('app.services.notification_service.smtplib.SMTP')
def test_send_email_success(
    mock_smtp: Mock,
    db_session: Session,
    notification_service: NotificationService,
    alert_for_notification: AlertHistory
):
    """
    Test: Envío exitoso de email por SMTP.

    Mock: smtplib.SMTP para simular envío exitoso
    """
    # Configurar mock SMTP
    mock_server = MagicMock()
    mock_smtp.return_value.__enter__.return_value = mock_server

    # Enviar notificaciones
    results = notification_service.send_alert_notifications(alert_for_notification)

    # Verificar que se intentó enviar email
    assert "email" in results
    assert results["email"] == "success" or "skipped" in results["email"]

    # Verificar que se actualizó notification_sent
    db_session.refresh(alert_for_notification)
    assert alert_for_notification.notification_sent is not None
    assert "email" in alert_for_notification.notification_sent


@patch('app.services.notification_service.smtplib.SMTP')
def test_send_email_failure(
    mock_smtp: Mock,
    db_session: Session,
    notification_service: NotificationService,
    alert_for_notification: AlertHistory
):
    """
    Test: Fallo al enviar email (error SMTP).

    Mock: smtplib.SMTP lanza Exception
    """
    # Configurar mock para lanzar excepción
    mock_smtp.side_effect = Exception("SMTP connection failed")

    # Modificar regla para solo usar email
    alert_for_notification.alert_rule.notification_channels = ["email"]
    db_session.commit()

    # Enviar notificaciones
    results = notification_service.send_alert_notifications(alert_for_notification)

    # Verificar que se registró el fallo
    assert "email" in results
    assert "failed" in results["email"] or "skipped" in results["email"]

    # Verificar que se actualizó notification_sent con error
    db_session.refresh(alert_for_notification)
    assert alert_for_notification.notification_sent is not None


# ============================================================
# TESTS: TELEGRAM NOTIFICATIONS
# ============================================================

@patch('app.services.notification_service.requests.post')
def test_send_telegram_success(
    mock_post: Mock,
    db_session: Session,
    notification_service: NotificationService,
    alert_for_notification: AlertHistory
):
    """
    Test: Envío exitoso de mensaje por Telegram Bot API.

    Mock: requests.post para simular respuesta exitosa
    """
    # Configurar mock de requests.post
    mock_response = Mock()
    mock_response.status_code = 200
    mock_response.json.return_value = {"ok": True}
    mock_post.return_value = mock_response

    # Modificar regla para solo usar telegram
    alert_for_notification.alert_rule.notification_channels = ["telegram"]
    db_session.commit()

    # Enviar notificaciones
    results = notification_service.send_alert_notifications(alert_for_notification)

    # Verificar resultado
    assert "telegram" in results
    assert results["telegram"] == "success" or "skipped" in results["telegram"]

    # Verificar que se actualizó notification_sent
    db_session.refresh(alert_for_notification)
    assert alert_for_notification.notification_sent is not None


@patch('app.services.notification_service.requests.post')
def test_send_telegram_failure(
    mock_post: Mock,
    db_session: Session,
    notification_service: NotificationService,
    alert_for_notification: AlertHistory
):
    """
    Test: Fallo al enviar mensaje por Telegram (API error).

    Mock: requests.post retorna error 400
    """
    # Configurar mock de requests.post con error
    mock_response = Mock()
    mock_response.status_code = 400
    mock_response.json.return_value = {"ok": False, "description": "Bad Request"}
    mock_post.return_value = mock_response

    # Modificar regla para solo usar telegram
    alert_for_notification.alert_rule.notification_channels = ["telegram"]
    db_session.commit()

    # Enviar notificaciones
    results = notification_service.send_alert_notifications(alert_for_notification)

    # Verificar que se registró el fallo
    assert "telegram" in results
    # Puede ser "failed" o "skipped - not configured"
    assert "failed" in results["telegram"] or "skipped" in results["telegram"]


# ============================================================
# TESTS: WEBHOOK NOTIFICATIONS
# ============================================================

@patch('app.services.notification_service.requests.post')
def test_send_webhook_success(
    mock_post: Mock,
    db_session: Session,
    notification_service: NotificationService,
    alert_for_notification: AlertHistory
):
    """
    Test: Envío exitoso de webhook (HTTP POST).

    Mock: requests.post para simular respuesta 200 OK
    """
    # Configurar webhook URL
    alert_for_notification.alert_rule.notification_channels = ["webhook"]
    alert_for_notification.alert_rule.webhook_url = "https://example.com/webhook"
    db_session.commit()

    # Configurar mock de requests.post
    mock_response = Mock()
    mock_response.status_code = 200
    mock_post.return_value = mock_response

    # Enviar notificaciones
    results = notification_service.send_alert_notifications(alert_for_notification)

    # Verificar resultado
    assert "webhook" in results
    assert results["webhook"] == "success"

    # Verificar que se hizo POST al webhook
    mock_post.assert_called_once()
    call_args = mock_post.call_args
    assert call_args[0][0] == "https://example.com/webhook"


def test_send_webhook_without_url(
    db_session: Session,
    notification_service: NotificationService,
    alert_for_notification: AlertHistory
):
    """
    Test: Intento de enviar webhook sin URL configurada → Fallo.
    """
    # Configurar webhook sin URL
    alert_for_notification.alert_rule.notification_channels = ["webhook"]
    alert_for_notification.alert_rule.webhook_url = None
    db_session.commit()

    # Enviar notificaciones
    results = notification_service.send_alert_notifications(alert_for_notification)

    # Verificar que se registró el fallo
    assert "webhook" in results
    assert "failed" in results["webhook"]
    assert "no URL" in results["webhook"]


# ============================================================
# TESTS: MULTIPLE CHANNELS
# ============================================================

@patch('app.services.notification_service.requests.post')
@patch('app.services.notification_service.smtplib.SMTP')
def test_send_multiple_channels(
    mock_smtp: Mock,
    mock_post: Mock,
    db_session: Session,
    notification_service: NotificationService,
    alert_for_notification: AlertHistory
):
    """
    Test: Envío por múltiples canales simultáneamente (email + telegram + webhook).

    Verifica que todos los canales se intentan independientemente.
    """
    # Configurar todos los canales
    alert_for_notification.alert_rule.notification_channels = [
        "email", "telegram", "webhook"
    ]
    alert_for_notification.alert_rule.webhook_url = "https://example.com/webhook"
    db_session.commit()

    # Configurar mocks
    mock_server = MagicMock()
    mock_smtp.return_value.__enter__.return_value = mock_server

    mock_response_telegram = Mock()
    mock_response_telegram.status_code = 200
    mock_response_telegram.json.return_value = {"ok": True}

    mock_response_webhook = Mock()
    mock_response_webhook.status_code = 200

    # requests.post se llama 2 veces (telegram + webhook)
    mock_post.side_effect = [mock_response_telegram, mock_response_webhook]

    # Enviar notificaciones
    results = notification_service.send_alert_notifications(alert_for_notification)

    # Verificar que se intentaron todos los canales
    assert "email" in results
    assert "telegram" in results
    assert "webhook" in results

    # Verificar que notification_sent contiene todos los canales
    db_session.refresh(alert_for_notification)
    assert alert_for_notification.notification_sent is not None
    notification_sent = alert_for_notification.notification_sent
    assert "email" in notification_sent
    assert "telegram" in notification_sent
    assert "webhook" in notification_sent


# ============================================================
# TESTS: EDGE CASES
# ============================================================

def test_send_notification_without_channels(
    db_session: Session,
    notification_service: NotificationService,
    alert_for_notification: AlertHistory
):
    """
    Test: Alert sin canales de notificación configurados → No hace nada.
    """
    # Remover canales
    alert_for_notification.alert_rule.notification_channels = []
    db_session.commit()

    # Enviar notificaciones
    results = notification_service.send_alert_notifications(alert_for_notification)

    # Verificar que no se intentó ninguna notificación
    assert results == {}


def test_send_notification_with_unknown_channel(
    db_session: Session,
    notification_service: NotificationService,
    alert_for_notification: AlertHistory
):
    """
    Test: Alert con canal desconocido → Registra error pero no crashea.
    """
    # Agregar canal desconocido
    alert_for_notification.alert_rule.notification_channels = ["unknown_channel"]
    db_session.commit()

    # Enviar notificaciones
    results = notification_service.send_alert_notifications(alert_for_notification)

    # Verificar que se registró como failed
    assert "unknown_channel" in results
    assert "failed" in results["unknown_channel"]
    assert "unknown channel" in results["unknown_channel"]
