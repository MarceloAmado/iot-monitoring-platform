"""
Tests para el job periódico de chequeo de alertas.

Cubre:
- Detección de devices offline
- Ignorar devices online
- Estadísticas correctas (devices chequeados, alertas disparadas)
- Envío de notificaciones automáticas
"""

import pytest
from unittest.mock import patch, MagicMock
from sqlalchemy.orm import Session
from datetime import datetime, timedelta

from app.models.device import Device
from app.models.alert import AlertRule
from app.jobs.alert_checker import check_offline_devices


@pytest.fixture
def offline_device(db_session: Session, device: Device, alert_rule_device_offline: AlertRule) -> Device:
    """
    Fixture que crea un device offline (sin reportar en 10 minutos).
    """
    device.last_seen_at = datetime.utcnow() - timedelta(minutes=10)
    db_session.commit()
    db_session.refresh(device)
    return device


@pytest.fixture
def online_device(db_session: Session, location, asset) -> Device:
    """
    Fixture que crea un device online (reportó hace 2 minutos).
    """
    device = Device(
        asset_id=asset.id,
        device_eui="ESP32_ONLINE_001",
        name="ESP32 Online 001",
        status="active",
        firmware_version="v1.0.0",
        last_seen_at=datetime.utcnow() - timedelta(minutes=2),
        config={"sampling_interval_sec": 300},
        extra_data={}
    )
    db_session.add(device)
    db_session.commit()
    db_session.refresh(device)
    return device


@pytest.fixture
def alert_rule_device_offline(db_session: Session, device: Device) -> AlertRule:
    """Regla: device sin reportar en 5 minutos"""
    rule = AlertRule(
        device_id=device.id,
        name="Device offline - Test Job",
        check_type="DEVICE_OFFLINE",
        time_window_minutes=5,
        enabled=True,
        cooldown_minutes=60,
        notification_channels=["email"]
    )
    db_session.add(rule)
    db_session.commit()
    db_session.refresh(rule)
    return rule


# ============================================================
# TESTS: JOB check_offline_devices()
# ============================================================

@patch('app.jobs.alert_checker.send_multiple_alert_notifications')
@patch('app.jobs.alert_checker.evaluate_all_devices_offline')
def test_check_offline_devices_detects_offline(
    mock_evaluate: MagicMock,
    mock_send_notifications: MagicMock,
    db_session: Session,
    offline_device: Device,
    alert_rule_device_offline: AlertRule
):
    """
    Test: Job detecta device offline y dispara alerta.

    Mock: evaluate_all_devices_offline y send_multiple_alert_notifications
    """
    # Configurar mock de evaluate_all_devices_offline
    mock_evaluate.return_value = {
        'total_devices': 1,
        'alerts_triggered': 1,
        'alert_ids': [1]
    }

    # Ejecutar job
    check_offline_devices()

    # Verificar que se llamó evaluate_all_devices_offline
    mock_evaluate.assert_called_once()

    # Verificar que se llamó send_multiple_alert_notifications con alert_ids
    mock_send_notifications.assert_called_once()
    # Verificar que el segundo argumento es la lista de alert_ids
    call_args = mock_send_notifications.call_args
    alert_ids = call_args[0][1]  # Segundo argumento
    assert alert_ids == [1]


@patch('app.jobs.alert_checker.send_multiple_alert_notifications')
@patch('app.jobs.alert_checker.evaluate_all_devices_offline')
def test_check_offline_devices_ignores_online(
    mock_evaluate: MagicMock,
    mock_send_notifications: MagicMock,
    db_session: Session,
    online_device: Device
):
    """
    Test: Job no dispara alertas para devices online.

    Mock: evaluate_all_devices_offline retorna 0 alertas
    """
    # Configurar mock para device online (sin alertas)
    mock_evaluate.return_value = {
        'total_devices': 1,
        'alerts_triggered': 0,
        'alert_ids': []
    }

    # Ejecutar job
    check_offline_devices()

    # Verificar que se llamó evaluate_all_devices_offline
    mock_evaluate.assert_called_once()

    # Verificar que NO se intentó enviar notificaciones
    mock_send_notifications.assert_not_called()


@patch('app.jobs.alert_checker.send_multiple_alert_notifications')
@patch('app.jobs.alert_checker.evaluate_all_devices_offline')
def test_check_offline_devices_stats_correct(
    mock_evaluate: MagicMock,
    mock_send_notifications: MagicMock,
    db_session: Session
):
    """
    Test: Job retorna estadísticas correctas.

    Verifica que las stats incluyan:
    - total_devices: Cantidad de devices chequeados
    - alerts_triggered: Cantidad de alertas disparadas
    - alert_ids: Lista de IDs de alertas
    """
    # Configurar mock con múltiples devices y alertas
    mock_evaluate.return_value = {
        'total_devices': 5,
        'alerts_triggered': 2,
        'alert_ids': [10, 11]
    }

    # Ejecutar job
    check_offline_devices()

    # Verificar que se llamó evaluate_all_devices_offline
    mock_evaluate.assert_called_once()

    # Verificar que se envió notificaciones para las 2 alertas
    mock_send_notifications.assert_called_once()
    call_args = mock_send_notifications.call_args
    alert_ids = call_args[0][1]  # Segundo argumento (alert_ids)
    assert alert_ids == [10, 11]


@patch('app.jobs.alert_checker.send_multiple_alert_notifications')
@patch('app.jobs.alert_checker.evaluate_all_devices_offline')
def test_check_offline_devices_sends_notifications(
    mock_evaluate: MagicMock,
    mock_send_notifications: MagicMock,
    db_session: Session
):
    """
    Test: Job envía notificaciones cuando se disparan alertas.

    Verifica que send_multiple_alert_notifications se llama
    con los alert_ids correctos.
    """
    # Configurar mock con alertas
    mock_evaluate.return_value = {
        'total_devices': 3,
        'alerts_triggered': 3,
        'alert_ids': [100, 101, 102]
    }

    # Ejecutar job
    check_offline_devices()

    # Verificar que se enviaron notificaciones
    mock_send_notifications.assert_called_once()

    # Verificar que se pasaron los 3 alert_ids
    call_args = mock_send_notifications.call_args
    alert_ids = call_args[0][1]
    assert len(alert_ids) == 3
    assert alert_ids == [100, 101, 102]


# ============================================================
# TESTS: ERROR HANDLING
# ============================================================

@patch('app.jobs.alert_checker.send_multiple_alert_notifications')
@patch('app.jobs.alert_checker.evaluate_all_devices_offline')
def test_check_offline_devices_handles_errors(
    mock_evaluate: MagicMock,
    mock_send_notifications: MagicMock,
    db_session: Session
):
    """
    Test: Job maneja errores sin crashear.

    Si evaluate_all_devices_offline lanza Exception,
    el job debe capturarla y loggear.
    """
    # Configurar mock para lanzar excepción
    mock_evaluate.side_effect = Exception("Database connection lost")

    # Ejecutar job (no debe crashear)
    try:
        check_offline_devices()
    except Exception as e:
        pytest.fail(f"Job crasheó con excepción: {e}")

    # Verificar que se intentó evaluar
    mock_evaluate.assert_called_once()

    # Verificar que NO se enviaron notificaciones (por el error)
    mock_send_notifications.assert_not_called()


@patch('app.jobs.alert_checker.send_multiple_alert_notifications')
@patch('app.jobs.alert_checker.evaluate_all_devices_offline')
def test_check_offline_devices_continues_if_notification_fails(
    mock_evaluate: MagicMock,
    mock_send_notifications: MagicMock,
    db_session: Session
):
    """
    Test: Job continúa incluso si send_multiple_alert_notifications falla.

    La evaluación debe completarse exitosamente aunque
    las notificaciones fallen.
    """
    # Configurar mocks
    mock_evaluate.return_value = {
        'total_devices': 2,
        'alerts_triggered': 1,
        'alert_ids': [50]
    }

    # Configurar mock de notificaciones para fallar
    mock_send_notifications.side_effect = Exception("SMTP server unavailable")

    # Ejecutar job (no debe crashear)
    try:
        check_offline_devices()
    except Exception as e:
        pytest.fail(f"Job crasheó cuando notificación falló: {e}")

    # Verificar que se intentó evaluar
    mock_evaluate.assert_called_once()

    # Verificar que se intentó enviar notificación (aunque falló)
    mock_send_notifications.assert_called_once()
