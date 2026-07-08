"""
Servicio de evaluación de alertas.

Evalúa sensor readings contra alert_rules configuradas y dispara
notificaciones cuando se cumplen las condiciones.

Tipos de chequeos soportados:
- THRESHOLD_ABOVE: variable > threshold_value
- THRESHOLD_BELOW: variable < threshold_value
- THRESHOLD_RANGE: variable NOT BETWEEN threshold_min AND threshold_max
- RATE_OF_CHANGE: cambio en time_window_minutes > threshold_value
- DEVICE_OFFLINE: last_seen_at > time_window_minutes (ago)
- SENSOR_FAULT: variable == -999 o NULL (sensor roto/error)
- ANOMALY_ML: (Futuro) detección de anomalías por ML
"""

import logging
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_

from app.models.sensor_reading import SensorReading
from app.models.alert import AlertRule, AlertHistory
from app.models.device import Device

logger = logging.getLogger(__name__)


class AlertEvaluationService:
    """
    Servicio para evaluar readings contra alert_rules y disparar alertas.
    """

    def __init__(self, db: Session):
        """
        Inicializa el servicio de alertas.

        Args:
            db: Sesión de base de datos SQLAlchemy
        """
        self.db = db

    def evaluate_reading(self, reading: SensorReading) -> List[AlertHistory]:
        """
        Evalúa un reading contra todas las alert_rules aplicables.

        Args:
            reading: SensorReading a evaluar

        Returns:
            Lista de AlertHistory creados (si se dispararon alertas)
        """
        # Obtener device para determinar location
        device = self.db.query(Device).filter(Device.id == reading.device_id).first()
        if not device:
            logger.warning(f"Device {reading.device_id} no encontrado para reading {reading.id}")
            return []

        # Obtener reglas aplicables (habilitadas y que aplican a este device/location)
        applicable_rules = self._get_applicable_rules(device)

        logger.debug(
            f"Evaluando reading {reading.id} contra {len(applicable_rules)} reglas"
        )

        triggered_alerts: List[AlertHistory] = []

        for rule in applicable_rules:
            # Verificar cooldown (evitar alertas spam)
            if self._is_in_cooldown(rule):
                logger.debug(
                    f"Regla '{rule.name}' (ID: {rule.id}) en cooldown, saltando"
                )
                continue

            # Evaluar regla según tipo
            alert = self._evaluate_rule(rule, reading, device)
            if alert:
                triggered_alerts.append(alert)
                logger.info(
                    f"Alerta disparada: {rule.name} (ID: {rule.id}) - {alert.message}"
                )

        # Marcar reading como procesado
        reading.processed = True
        self.db.commit()

        return triggered_alerts

    def evaluate_device_offline(self, device_id: int) -> List[AlertHistory]:
        """
        Evalúa si un device está offline y dispara alertas DEVICE_OFFLINE.

        Args:
            device_id: ID del device a evaluar

        Returns:
            Lista de AlertHistory creados
        """
        device = self.db.query(Device).filter(Device.id == device_id).first()
        if not device:
            return []

        # Obtener reglas DEVICE_OFFLINE aplicables
        rules = (
            self.db.query(AlertRule)
            .filter(
                and_(
                    AlertRule.enabled == True,
                    AlertRule.check_type == "DEVICE_OFFLINE",
                    or_(
                        AlertRule.device_id == device_id,
                        AlertRule.device_id == None,
                    ),
                )
            )
            .all()
        )

        triggered_alerts: List[AlertHistory] = []

        for rule in rules:
            if self._is_in_cooldown(rule):
                continue

            # Verificar si device está offline
            if self._check_device_offline(device, rule):
                alert = self._create_alert_history(
                    rule=rule,
                    device=device,
                    reading=None,
                    value_observed=None,
                    message=f"Device '{device.name}' (EUI: {device.device_eui}) offline por más de {rule.time_window_minutes} minutos. Última actividad: {device.last_seen_at.isoformat() if device.last_seen_at else 'nunca'}",
                )
                triggered_alerts.append(alert)
                logger.info(
                    f"Alerta DEVICE_OFFLINE disparada para device {device.name}"
                )

        return triggered_alerts

    def _get_applicable_rules(self, device: Device) -> List[AlertRule]:
        """
        Obtiene las reglas aplicables a un device específico.

        Args:
            device: Device al que aplican las reglas

        Returns:
            Lista de AlertRule aplicables
        """
        # Reglas habilitadas y que:
        # - Aplican a este device específico, O
        # - Aplican a la location del device (device_id NULL), O
        # - Son globales (location_id NULL y device_id NULL)

        rules = (
            self.db.query(AlertRule)
            .filter(
                and_(
                    AlertRule.enabled == True,
                    AlertRule.check_type != "DEVICE_OFFLINE",  # DEVICE_OFFLINE se evalúa por separado
                    or_(
                        AlertRule.device_id == device.id,  # Regla específica del device
                        and_(
                            AlertRule.device_id == None,
                            or_(
                                AlertRule.location_id == device.asset.location_id
                                if device.asset
                                else False,  # Regla de la location
                                AlertRule.location_id == None,  # Regla global
                            ),
                        ),
                    ),
                )
            )
            .all()
        )

        return rules

    def _is_in_cooldown(self, rule: AlertRule) -> bool:
        """
        Verifica si una regla está en periodo de cooldown.

        Args:
            rule: AlertRule a verificar

        Returns:
            True si está en cooldown, False si puede dispararse
        """
        cooldown_delta = timedelta(minutes=rule.cooldown_minutes)
        cutoff_time = datetime.utcnow() - cooldown_delta

        # Buscar última alerta de esta regla
        last_alert = (
            self.db.query(AlertHistory)
            .filter(AlertHistory.alert_rule_id == rule.id)
            .order_by(AlertHistory.triggered_at.desc())
            .first()
        )

        if not last_alert:
            return False  # No hay alertas previas

        return last_alert.triggered_at > cutoff_time

    def _evaluate_rule(
        self, rule: AlertRule, reading: SensorReading, device: Device
    ) -> Optional[AlertHistory]:
        """
        Evalúa una regla específica contra un reading.

        Args:
            rule: AlertRule a evaluar
            reading: SensorReading a verificar
            device: Device asociado

        Returns:
            AlertHistory si se disparó la alerta, None si no
        """
        check_type = rule.check_type
        variable_key = rule.variable_key
        value = reading.data_payload.get(variable_key)

        # Log para debugging
        logger.debug(
            f"Evaluando regla '{rule.name}' (tipo: {check_type}) - Variable '{variable_key}' = {value}"
        )

        # Dispatcher de métodos de evaluación
        evaluators = {
            "THRESHOLD_ABOVE": self._check_threshold_above,
            "THRESHOLD_BELOW": self._check_threshold_below,
            "THRESHOLD_RANGE": self._check_threshold_range,
            "RATE_OF_CHANGE": self._check_rate_of_change,
            "SENSOR_FAULT": self._check_sensor_fault,
        }

        evaluator = evaluators.get(check_type)
        if not evaluator:
            logger.warning(f"Tipo de chequeo '{check_type}' no soportado (regla ID: {rule.id})")
            return None

        # Ejecutar evaluador
        triggered, message = evaluator(rule, reading, device, value)

        if triggered:
            return self._create_alert_history(
                rule=rule,
                device=device,
                reading=reading,
                value_observed=value if isinstance(value, (int, float)) else None,
                message=message,
            )

        return None

    def _check_threshold_above(
        self, rule: AlertRule, reading: SensorReading, device: Device, value: Any
    ) -> tuple[bool, str]:
        """Verifica si valor > threshold_value."""
        if not isinstance(value, (int, float)):
            return False, ""

        if value > rule.threshold_value:
            message = (
                f"⚠️ {rule.name}: Variable '{rule.variable_key}' = {value:.2f} "
                f"excede el umbral de {rule.threshold_value:.2f} "
                f"en device '{device.name}' (EUI: {device.device_eui})"
            )
            return True, message

        return False, ""

    def _check_threshold_below(
        self, rule: AlertRule, reading: SensorReading, device: Device, value: Any
    ) -> tuple[bool, str]:
        """Verifica si valor < threshold_value."""
        if not isinstance(value, (int, float)):
            return False, ""

        if value < rule.threshold_value:
            message = (
                f"⚠️ {rule.name}: Variable '{rule.variable_key}' = {value:.2f} "
                f"está por debajo del umbral de {rule.threshold_value:.2f} "
                f"en device '{device.name}' (EUI: {device.device_eui})"
            )
            return True, message

        return False, ""

    def _check_threshold_range(
        self, rule: AlertRule, reading: SensorReading, device: Device, value: Any
    ) -> tuple[bool, str]:
        """Verifica si valor NO está entre threshold_min y threshold_max."""
        if not isinstance(value, (int, float)):
            return False, ""

        if not (rule.threshold_min <= value <= rule.threshold_max):
            message = (
                f"⚠️ {rule.name}: Variable '{rule.variable_key}' = {value:.2f} "
                f"fuera de rango permitido [{rule.threshold_min:.2f}, {rule.threshold_max:.2f}] "
                f"en device '{device.name}' (EUI: {device.device_eui})"
            )
            return True, message

        return False, ""

    def _check_rate_of_change(
        self, rule: AlertRule, reading: SensorReading, device: Device, value: Any
    ) -> tuple[bool, str]:
        """Verifica si el cambio en time_window_minutes > threshold_value."""
        if not isinstance(value, (int, float)):
            return False, ""

        # Obtener reading anterior dentro de la ventana de tiempo
        time_window = timedelta(minutes=rule.time_window_minutes)
        cutoff_time = reading.timestamp - time_window

        previous_reading = (
            self.db.query(SensorReading)
            .filter(
                and_(
                    SensorReading.device_id == device.id,
                    SensorReading.timestamp >= cutoff_time,
                    SensorReading.timestamp < reading.timestamp,
                    SensorReading.id != reading.id,
                )
            )
            .order_by(SensorReading.timestamp.desc())
            .first()
        )

        if not previous_reading:
            # No hay reading previo en la ventana, no podemos calcular tasa de cambio
            return False, ""

        previous_value = previous_reading.data_payload.get(rule.variable_key)
        if not isinstance(previous_value, (int, float)):
            return False, ""

        # Calcular cambio absoluto
        change = abs(value - previous_value)

        if change > rule.threshold_value:
            message = (
                f"⚠️ {rule.name}: Variable '{rule.variable_key}' cambió {change:.2f} "
                f"en {rule.time_window_minutes} minutos (de {previous_value:.2f} a {value:.2f}), "
                f"superando el límite de {rule.threshold_value:.2f} "
                f"en device '{device.name}' (EUI: {device.device_eui})"
            )
            return True, message

        return False, ""

    def _check_sensor_fault(
        self, rule: AlertRule, reading: SensorReading, device: Device, value: Any
    ) -> tuple[bool, str]:
        """Verifica si el sensor reporta un error (-999) o valor nulo."""
        # Error típico de sensores: -999 o None
        if value is None or value == -999 or value == -999.0:
            message = (
                f"⚠️ {rule.name}: Sensor '{rule.variable_key}' reporta falla (valor: {value}) "
                f"en device '{device.name}' (EUI: {device.device_eui}). "
                f"Verificar conexión del sensor."
            )
            return True, message

        return False, ""

    def _check_device_offline(self, device: Device, rule: AlertRule) -> bool:
        """Verifica si un device está offline según time_window_minutes."""
        if not device.last_seen_at:
            # Device nunca ha reportado
            return True

        time_window = timedelta(minutes=rule.time_window_minutes)
        cutoff_time = datetime.utcnow() - time_window

        return device.last_seen_at < cutoff_time

    def _create_alert_history(
        self,
        rule: AlertRule,
        device: Device,
        reading: Optional[SensorReading],
        value_observed: Optional[float],
        message: str,
    ) -> AlertHistory:
        """
        Crea un registro de AlertHistory en la DB.

        Args:
            rule: AlertRule que se disparó
            device: Device que causó la alerta
            reading: SensorReading asociado (puede ser None para DEVICE_OFFLINE)
            value_observed: Valor que causó la alerta
            message: Mensaje descriptivo

        Returns:
            AlertHistory creado
        """
        alert = AlertHistory(
            alert_rule_id=rule.id,
            device_id=device.id,
            sensor_reading_id=reading.id if reading else None,
            value_observed=value_observed,
            message=message,
            triggered_at=datetime.utcnow(),
            notification_sent=None,  # Se actualizará por notification_service
        )

        self.db.add(alert)
        self.db.commit()
        self.db.refresh(alert)

        logger.info(f"AlertHistory creado: ID={alert.id}, Regla='{rule.name}', Device='{device.name}'")

        return alert


# ============================================
# Funciones helper para uso en endpoints
# ============================================

def evaluate_reading_alerts(db: Session, reading: SensorReading) -> List[AlertHistory]:
    """
    Evalúa un reading contra alert_rules (wrapper para usar en endpoints).

    Args:
        db: Sesión de base de datos
        reading: SensorReading a evaluar

    Returns:
        Lista de AlertHistory disparados
    """
    service = AlertEvaluationService(db)
    return service.evaluate_reading(reading)


def evaluate_device_offline_alerts(db: Session, device_id: int) -> List[AlertHistory]:
    """
    Evalúa si un device está offline (wrapper para job periódico).

    Args:
        db: Sesión de base de datos
        device_id: ID del device a verificar

    Returns:
        Lista de AlertHistory disparados
    """
    service = AlertEvaluationService(db)
    return service.evaluate_device_offline(device_id)


def evaluate_all_devices_offline(db: Session) -> Dict[str, Any]:
    """
    Evalúa todos los devices activos en busca de offline alerts.

    Útil para ejecutar periódicamente (cada 1-5 minutos) como job.

    Args:
        db: Sesión de base de datos

    Returns:
        Dict con estadísticas: {
            "total_devices_checked": int,
            "offline_devices": int,
            "alerts_triggered": int
        }
    """
    # Obtener todos los devices activos
    devices = db.query(Device).filter(Device.status == "active").all()

    total_alerts = 0
    offline_count = 0

    for device in devices:
        alerts = evaluate_device_offline_alerts(db, device.id)
        if alerts:
            offline_count += 1
            total_alerts += len(alerts)

    stats = {
        "total_devices_checked": len(devices),
        "offline_devices": offline_count,
        "alerts_triggered": total_alerts,
        "checked_at": datetime.utcnow().isoformat(),
    }

    logger.info(f"Offline check completado: {stats}")
    return stats
