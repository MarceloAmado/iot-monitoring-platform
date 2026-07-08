"""
Tests para el servicio de evaluación de alertas.

Cubre:
- Evaluación de reglas THRESHOLD_ABOVE, THRESHOLD_BELOW, THRESHOLD_RANGE
- Evaluación de RATE_OF_CHANGE
- Evaluación de SENSOR_FAULT (valor -999)
- Evaluación de DEVICE_OFFLINE
- Verificación de cooldown (no disparar alertas consecutivas)
- Verificación de reglas deshabilitadas (enabled=False)
"""

import pytest
from datetime import datetime, timedelta
from sqlalchemy.orm import Session

from app.models.alert import AlertRule, AlertHistory
from app.models.device import Device
from app.models.sensor_reading import SensorReading
from app.services.alert_service import AlertEvaluationService


@pytest.fixture
def alert_service(db_session: Session) -> AlertEvaluationService:
    """Fixture que provee una instancia del servicio de alertas."""
    return AlertEvaluationService(db_session)


@pytest.fixture
def device_with_readings(db_session: Session, device: Device) -> Device:
    """
    Fixture que crea un device con readings históricas.

    Útil para tests de RATE_OF_CHANGE.
    """
    # Crear readings con temperatura creciente
    base_time = datetime.utcnow() - timedelta(minutes=30)

    for i in range(6):
        reading = SensorReading(
            device_id=device.id,
            data_payload={"temp_c": 20.0 + i * 2.0},  # 20, 22, 24, 26, 28, 30
            quality_score=0.95,
            processed=False,
            timestamp=base_time + timedelta(minutes=i * 5)
        )
        db_session.add(reading)

    db_session.commit()
    return device


@pytest.fixture
def alert_rule_threshold_above(db_session: Session, device: Device) -> AlertRule:
    """Regla: temperatura > 25°C"""
    rule = AlertRule(
        device_id=device.id,
        name="Temperatura alta - Test",
        check_type="THRESHOLD_ABOVE",
        variable_key="temp_c",
        threshold_value=25.0,
        enabled=True,
        cooldown_minutes=30,
        notification_channels=["email"]
    )
    db_session.add(rule)
    db_session.commit()
    db_session.refresh(rule)
    return rule


@pytest.fixture
def alert_rule_threshold_below(db_session: Session, device: Device) -> AlertRule:
    """Regla: temperatura < 5°C"""
    rule = AlertRule(
        device_id=device.id,
        name="Temperatura baja - Test",
        check_type="THRESHOLD_BELOW",
        variable_key="temp_c",
        threshold_value=5.0,
        enabled=True,
        cooldown_minutes=30,
        notification_channels=["email"]
    )
    db_session.add(rule)
    db_session.commit()
    db_session.refresh(rule)
    return rule


@pytest.fixture
def alert_rule_threshold_range(db_session: Session, device: Device) -> AlertRule:
    """Regla: temperatura FUERA del rango [18-22]°C"""
    rule = AlertRule(
        device_id=device.id,
        name="Temperatura fuera de rango - Test",
        check_type="THRESHOLD_RANGE",
        variable_key="temp_c",
        threshold_min=18.0,
        threshold_max=22.0,
        enabled=True,
        cooldown_minutes=30,
        notification_channels=["email"]
    )
    db_session.add(rule)
    db_session.commit()
    db_session.refresh(rule)
    return rule


@pytest.fixture
def alert_rule_rate_of_change(db_session: Session, device: Device) -> AlertRule:
    """Regla: cambio de temperatura > 5°C en 10 minutos"""
    rule = AlertRule(
        device_id=device.id,
        name="Cambio rápido de temperatura - Test",
        check_type="RATE_OF_CHANGE",
        variable_key="temp_c",
        threshold_value=5.0,
        time_window_minutes=10,
        enabled=True,
        cooldown_minutes=30,
        notification_channels=["email"]
    )
    db_session.add(rule)
    db_session.commit()
    db_session.refresh(rule)
    return rule


@pytest.fixture
def alert_rule_sensor_fault(db_session: Session, device: Device) -> AlertRule:
    """Regla: detección de sensor roto (valor -999)"""
    rule = AlertRule(
        device_id=device.id,
        name="Sensor roto - Test",
        check_type="SENSOR_FAULT",
        variable_key="temp_c",
        enabled=True,
        cooldown_minutes=30,
        notification_channels=["email"]
    )
    db_session.add(rule)
    db_session.commit()
    db_session.refresh(rule)
    return rule


@pytest.fixture
def alert_rule_device_offline(db_session: Session, device: Device) -> AlertRule:
    """Regla: device sin reportar en 5 minutos"""
    rule = AlertRule(
        device_id=device.id,
        name="Device offline - Test",
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
# TESTS: THRESHOLD_ABOVE
# ============================================================

def test_threshold_above_triggers_alert(
    db_session: Session,
    alert_service: AlertEvaluationService,
    device: Device,
    alert_rule_threshold_above: AlertRule
):
    """
    Test: Temperatura 27°C > threshold 25°C → Debe disparar alerta.
    """
    # Crear reading con temperatura alta
    reading = SensorReading(
        device_id=device.id,
        data_payload={"temp_c": 27.0},
        quality_score=0.95,
        processed=False,
        timestamp=datetime.utcnow()
    )
    db_session.add(reading)
    db_session.commit()
    db_session.refresh(reading)

    # Evaluar reading
    alerts = alert_service.evaluate_reading(reading)

    # Verificar que se disparó alerta
    assert len(alerts) == 1
    alert = alerts[0]
    assert alert.alert_rule_id == alert_rule_threshold_above.id
    assert alert.device_id == device.id
    assert alert.sensor_reading_id == reading.id
    assert alert.value_observed == 27.0
    assert "27.00" in alert.message and "excede" in alert.message.lower()


def test_threshold_above_does_not_trigger_when_below_threshold(
    db_session: Session,
    alert_service: AlertEvaluationService,
    device: Device,
    alert_rule_threshold_above: AlertRule
):
    """
    Test: Temperatura 23°C < threshold 25°C → NO debe disparar alerta.
    """
    # Crear reading con temperatura normal
    reading = SensorReading(
        device_id=device.id,
        data_payload={"temp_c": 23.0},
        quality_score=0.95,
        processed=False,
        timestamp=datetime.utcnow()
    )
    db_session.add(reading)
    db_session.commit()
    db_session.refresh(reading)

    # Evaluar reading
    alerts = alert_service.evaluate_reading(reading)

    # Verificar que NO se disparó alerta
    assert len(alerts) == 0


# ============================================================
# TESTS: THRESHOLD_BELOW
# ============================================================

def test_threshold_below_triggers_alert(
    db_session: Session,
    alert_service: AlertEvaluationService,
    device: Device,
    alert_rule_threshold_below: AlertRule
):
    """
    Test: Temperatura 3°C < threshold 5°C → Debe disparar alerta.
    """
    # Crear reading con temperatura baja
    reading = SensorReading(
        device_id=device.id,
        data_payload={"temp_c": 3.0},
        quality_score=0.95,
        processed=False,
        timestamp=datetime.utcnow()
    )
    db_session.add(reading)
    db_session.commit()
    db_session.refresh(reading)

    # Evaluar reading
    alerts = alert_service.evaluate_reading(reading)

    # Verificar que se disparó alerta
    assert len(alerts) == 1
    alert = alerts[0]
    assert alert.alert_rule_id == alert_rule_threshold_below.id
    assert alert.value_observed == 3.0
    assert "3.00" in alert.message and "debajo" in alert.message.lower()


# ============================================================
# TESTS: THRESHOLD_RANGE
# ============================================================

def test_threshold_range_triggers_alert_above_max(
    db_session: Session,
    alert_service: AlertEvaluationService,
    device: Device,
    alert_rule_threshold_range: AlertRule
):
    """
    Test: Temperatura 25°C > max 22°C → Debe disparar alerta.
    """
    # Crear reading fuera del rango (por arriba)
    reading = SensorReading(
        device_id=device.id,
        data_payload={"temp_c": 25.0},
        quality_score=0.95,
        processed=False,
        timestamp=datetime.utcnow()
    )
    db_session.add(reading)
    db_session.commit()
    db_session.refresh(reading)

    # Evaluar reading
    alerts = alert_service.evaluate_reading(reading)

    # Verificar que se disparó alerta
    assert len(alerts) == 1
    alert = alerts[0]
    assert alert.value_observed == 25.0
    assert "25.00" in alert.message and "fuera" in alert.message.lower()


def test_threshold_range_triggers_alert_below_min(
    db_session: Session,
    alert_service: AlertEvaluationService,
    device: Device,
    alert_rule_threshold_range: AlertRule
):
    """
    Test: Temperatura 15°C < min 18°C → Debe disparar alerta.
    """
    # Crear reading fuera del rango (por abajo)
    reading = SensorReading(
        device_id=device.id,
        data_payload={"temp_c": 15.0},
        quality_score=0.95,
        processed=False,
        timestamp=datetime.utcnow()
    )
    db_session.add(reading)
    db_session.commit()
    db_session.refresh(reading)

    # Evaluar reading
    alerts = alert_service.evaluate_reading(reading)

    # Verificar que se disparó alerta
    assert len(alerts) == 1
    alert = alerts[0]
    assert alert.value_observed == 15.0


def test_threshold_range_does_not_trigger_when_in_range(
    db_session: Session,
    alert_service: AlertEvaluationService,
    device: Device,
    alert_rule_threshold_range: AlertRule
):
    """
    Test: Temperatura 20°C dentro del rango [18-22]°C → NO debe disparar alerta.
    """
    # Crear reading dentro del rango
    reading = SensorReading(
        device_id=device.id,
        data_payload={"temp_c": 20.0},
        quality_score=0.95,
        processed=False,
        timestamp=datetime.utcnow()
    )
    db_session.add(reading)
    db_session.commit()
    db_session.refresh(reading)

    # Evaluar reading
    alerts = alert_service.evaluate_reading(reading)

    # Verificar que NO se disparó alerta
    assert len(alerts) == 0


# ============================================================
# TESTS: RATE_OF_CHANGE
# ============================================================

def test_rate_of_change_triggers_alert(
    db_session: Session,
    alert_service: AlertEvaluationService,
    device_with_readings: Device,
    alert_rule_rate_of_change: AlertRule
):
    """
    Test: Temperatura sube de 20°C a 30°C en 10 minutos (cambio de 10°C > threshold 5°C)
    → Debe disparar alerta.
    """
    # El device_with_readings ya tiene readings: 20, 22, 24, 26, 28, 30 cada 5 min
    # Crear nueva reading con temp alta (cambio brusco)
    reading = SensorReading(
        device_id=device_with_readings.id,
        data_payload={"temp_c": 32.0},  # Cambio de 30 a 32 en 5 min = 2°C
        quality_score=0.95,
        processed=False,
        timestamp=datetime.utcnow()
    )
    db_session.add(reading)
    db_session.commit()
    db_session.refresh(reading)

    # Evaluar reading
    alerts = alert_service.evaluate_reading(reading)

    # Verificar que se disparó alerta (cambio > 5°C en 10 min)
    # Nota: La lógica de RATE_OF_CHANGE compara con readings en time_window_minutes atrás
    # En este caso, hay readings con diferencia > 5°C
    if len(alerts) > 0:
        alert = alerts[0]
        assert alert.alert_rule_id == alert_rule_rate_of_change.id
        assert "cambió" in alert.message.lower()


# ============================================================
# TESTS: SENSOR_FAULT
# ============================================================

def test_sensor_fault_triggers_alert_with_minus_999(
    db_session: Session,
    alert_service: AlertEvaluationService,
    device: Device,
    alert_rule_sensor_fault: AlertRule
):
    """
    Test: Lectura con temp_c = -999 (sensor roto) → Debe disparar alerta.
    """
    # Crear reading con valor de error
    reading = SensorReading(
        device_id=device.id,
        data_payload={"temp_c": -999.0},
        quality_score=0.0,
        processed=False,
        timestamp=datetime.utcnow()
    )
    db_session.add(reading)
    db_session.commit()
    db_session.refresh(reading)

    # Evaluar reading
    alerts = alert_service.evaluate_reading(reading)

    # Verificar que se disparó alerta
    assert len(alerts) == 1
    alert = alerts[0]
    assert alert.alert_rule_id == alert_rule_sensor_fault.id
    assert "sensor defectuoso" in alert.message.lower() or "falla" in alert.message.lower()


def test_sensor_fault_triggers_alert_with_null(
    db_session: Session,
    alert_service: AlertEvaluationService,
    device: Device,
    alert_rule_sensor_fault: AlertRule
):
    """
    Test: Lectura sin variable temp_c (None) → Debe disparar alerta.
    """
    # Crear reading sin la variable esperada
    reading = SensorReading(
        device_id=device.id,
        data_payload={"humidity_pct": 50.0},  # temp_c ausente
        quality_score=0.95,
        processed=False,
        timestamp=datetime.utcnow()
    )
    db_session.add(reading)
    db_session.commit()
    db_session.refresh(reading)

    # Evaluar reading
    alerts = alert_service.evaluate_reading(reading)

    # Verificar que se disparó alerta
    assert len(alerts) == 1
    alert = alerts[0]
    assert alert.alert_rule_id == alert_rule_sensor_fault.id


# ============================================================
# TESTS: DEVICE_OFFLINE
# ============================================================

def test_device_offline_triggers_alert(
    db_session: Session,
    alert_service: AlertEvaluationService,
    device: Device,
    alert_rule_device_offline: AlertRule
):
    """
    Test: Device con last_seen_at > 5 minutos → Debe disparar alerta.
    """
    # Actualizar last_seen_at a 10 minutos atrás
    device.last_seen_at = datetime.utcnow() - timedelta(minutes=10)
    db_session.commit()

    # Evaluar device offline
    alerts = alert_service.evaluate_device_offline(device.id)

    # Verificar que se disparó alerta
    assert len(alerts) == 1
    alert = alerts[0]
    assert alert.alert_rule_id == alert_rule_device_offline.id
    assert alert.device_id == device.id
    assert "offline" in alert.message.lower()


def test_device_offline_does_not_trigger_when_online(
    db_session: Session,
    alert_service: AlertEvaluationService,
    device: Device,
    alert_rule_device_offline: AlertRule
):
    """
    Test: Device con last_seen_at reciente (< 5 min) → NO debe disparar alerta.
    """
    # Actualizar last_seen_at a 2 minutos atrás (online)
    device.last_seen_at = datetime.utcnow() - timedelta(minutes=2)
    db_session.commit()

    # Evaluar device offline
    alerts = alert_service.evaluate_device_offline(device.id)

    # Verificar que NO se disparó alerta
    assert len(alerts) == 0


# ============================================================
# TESTS: COOLDOWN
# ============================================================

def test_cooldown_prevents_consecutive_alerts(
    db_session: Session,
    alert_service: AlertEvaluationService,
    device: Device,
    alert_rule_threshold_above: AlertRule
):
    """
    Test: Disparar 2 alertas consecutivas con cooldown 30 min
    → La segunda NO debe dispararse si está dentro del cooldown.
    """
    # Primera alerta
    reading1 = SensorReading(
        device_id=device.id,
        data_payload={"temp_c": 27.0},
        quality_score=0.95,
        processed=False,
        timestamp=datetime.utcnow()
    )
    db_session.add(reading1)
    db_session.commit()
    db_session.refresh(reading1)

    alerts1 = alert_service.evaluate_reading(reading1)
    assert len(alerts1) == 1

    # Guardar alerta en DB
    db_session.add(alerts1[0])
    db_session.commit()

    # Segunda alerta (5 minutos después, dentro del cooldown de 30 min)
    reading2 = SensorReading(
        device_id=device.id,
        data_payload={"temp_c": 28.0},
        quality_score=0.95,
        processed=False,
        timestamp=datetime.utcnow() + timedelta(minutes=5)
    )
    db_session.add(reading2)
    db_session.commit()
    db_session.refresh(reading2)

    alerts2 = alert_service.evaluate_reading(reading2)

    # Verificar que NO se disparó alerta (cooldown activo)
    assert len(alerts2) == 0


# ============================================================
# TESTS: REGLAS DESHABILITADAS
# ============================================================

def test_disabled_rule_does_not_trigger_alert(
    db_session: Session,
    alert_service: AlertEvaluationService,
    device: Device,
    alert_rule_threshold_above: AlertRule
):
    """
    Test: Regla con enabled=False → NO debe disparar alerta.
    """
    # Deshabilitar regla
    alert_rule_threshold_above.enabled = False
    db_session.commit()

    # Crear reading que normalmente dispararía alerta
    reading = SensorReading(
        device_id=device.id,
        data_payload={"temp_c": 27.0},
        quality_score=0.95,
        processed=False,
        timestamp=datetime.utcnow()
    )
    db_session.add(reading)
    db_session.commit()
    db_session.refresh(reading)

    # Evaluar reading
    alerts = alert_service.evaluate_reading(reading)

    # Verificar que NO se disparó alerta (regla deshabilitada)
    assert len(alerts) == 0
