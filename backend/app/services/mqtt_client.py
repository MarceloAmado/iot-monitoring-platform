"""
Servicio de cliente MQTT para recibir telemetría de devices.

Este servicio:
1. Se conecta al broker Mosquitto
2. Se subscribe a tópicos de telemetría de devices
3. Valida API Keys encriptadas
4. Procesa mensajes y crea SensorReadings
5. Maneja reconexión automática

Tópicos MQTT:
- iot/+/devices/+/telemetry - Telemetría de sensores
- iot/+/devices/+/status    - Estado de devices

Formato de mensaje:
{
    "device_eui": "ESP32_LAB_001",
    "api_key": "plaintext_api_key",
    "data_payload": {"temp_c": 25.5, "humidity_pct": 60},
    "timestamp": "2025-11-08T23:00:00Z"
}

Autor: Sistema SCADA - Fase 1.3
Fecha: 2025-11-08
"""

import json
import logging
from typing import Optional
from datetime import datetime
from paho.mqtt import client as mqtt_client
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.database import SessionLocal
from app.models.device import Device
from app.models.sensor_reading import SensorReading
from app.core.security import decrypt_api_key
from app.services.audit_service import AuditService

logger = logging.getLogger(__name__)


class MQTTClientService:
    """
    Cliente MQTT para recibir telemetría de devices ESP32.

    Características:
    - Conexión persistente al broker Mosquitto
    - Reconexión automática en caso de falla
    - Validación de API keys encriptadas
    - Audit logging de intentos fallidos
    - QoS 1 para garantizar entrega de mensajes

    Uso:
        mqtt_service.start()  # Iniciar cliente
        mqtt_service.stop()   # Detener cliente
    """

    def __init__(self):
        """Inicializa el cliente MQTT."""
        self.client: Optional[mqtt_client.Client] = None
        self.connected = False
        self.message_count = 0
        self.error_count = 0

    def on_connect(self, client, userdata, flags, rc):
        """
        Callback al conectar al broker.

        Args:
            client: Cliente MQTT
            userdata: Datos de usuario (no usado)
            flags: Flags de conexión
            rc: Código de resultado (0 = éxito)
        """
        if rc == 0:
            logger.info("[MQTT] Conectado a Mosquitto broker exitosamente")
            self.connected = True

            # Subscribe a tópicos de telemetría
            topics = [
                ("iot/+/devices/+/telemetry", 1),  # QoS 1
                ("iot/+/devices/+/status", 1),
            ]

            for topic, qos in topics:
                self.client.subscribe(topic, qos=qos)
                logger.info(f"[MQTT] Subscripto a tópico: {topic} (QoS {qos})")

        else:
            error_messages = {
                1: "Incorrect protocol version",
                2: "Invalid client identifier",
                3: "Server unavailable",
                4: "Bad username or password",
                5: "Not authorized"
            }
            error_msg = error_messages.get(rc, f"Unknown error code {rc}")
            logger.error(f"[MQTT] Error al conectar: {error_msg}")
            self.connected = False

    def on_disconnect(self, client, userdata, rc):
        """
        Callback al desconectar del broker.

        Args:
            client: Cliente MQTT
            userdata: Datos de usuario (no usado)
            rc: Código de resultado (0 = desconexión limpia)
        """
        logger.warning(f"[MQTT] Desconectado del broker (rc={rc})")
        self.connected = False

        # Reconexión automática si fue desconexión inesperada
        if rc != 0:
            logger.info("[MQTT] Intentando reconexión automática...")

    def on_message(self, client, userdata, msg):
        """
        Callback al recibir mensaje MQTT.

        Procesa mensajes de telemetría de devices ESP32.
        Valida API key y crea SensorReading en base de datos.

        Args:
            client: Cliente MQTT
            userdata: Datos de usuario (no usado)
            msg: Mensaje MQTT recibido
        """
        try:
            topic = msg.topic
            payload_str = msg.payload.decode()

            logger.debug(f"[MQTT] Mensaje recibido en tópico: {topic}")
            logger.debug(f"[MQTT] Payload: {payload_str[:200]}...")  # Log primeros 200 chars

            # Parse payload JSON
            try:
                payload = json.loads(payload_str)
            except json.JSONDecodeError as e:
                logger.error(f"[MQTT] JSON inválido en tópico {topic}: {e}")
                logger.error(f"[MQTT] Payload recibido: {payload_str}")
                self.error_count += 1
                return

            # Extraer campos requeridos
            device_eui = payload.get("device_eui")
            api_key = payload.get("api_key")
            data_payload = payload.get("data_payload")
            timestamp = payload.get("timestamp")

            # Validar campos obligatorios
            if not all([device_eui, api_key, data_payload]):
                logger.error(f"[MQTT] Mensaje incompleto en tópico {topic}")
                logger.error(f"[MQTT] Campos recibidos: device_eui={device_eui}, api_key={'***' if api_key else None}, data_payload={bool(data_payload)}")
                self.error_count += 1
                return

            # Procesar telemetría (síncrono - corre en thread MQTT)
            self.process_telemetry(device_eui, api_key, data_payload, timestamp, topic)

        except Exception as e:
            logger.error(f"[MQTT] Error procesando mensaje en tópico {msg.topic}: {e}")
            logger.exception(e)  # Stack trace completo
            self.error_count += 1

    def process_telemetry(
        self,
        device_eui: str,
        api_key: str,
        data_payload: dict,
        timestamp: Optional[str],
        topic: str
    ):
        """
        Procesa telemetría de device:
        1. Busca device por EUI
        2. Valida API key encriptada
        3. Crea SensorReading
        4. Actualiza last_seen_at
        5. Registra en audit log si hay error

        Args:
            device_eui: Device EUI (ej: ESP32_LAB_001)
            api_key: API key en plaintext del ESP32
            data_payload: Datos del sensor (dict JSONB)
            timestamp: Timestamp ISO 8601 (opcional)
            topic: Tópico MQTT del mensaje
        """
        db = SessionLocal()
        try:
            # 1. Buscar device por EUI
            device = db.query(Device).filter(Device.device_eui == device_eui).first()
            if not device:
                logger.warning(f"[MQTT] Device {device_eui} no encontrado en BD")
                AuditService.log(
                    db=db,
                    action_type="API_KEY_INVALID",
                    extra_data={
                        "device_eui": device_eui,
                        "reason": "device_not_found",
                        "source": "mqtt",
                        "topic": topic
                    }
                )
                self.error_count += 1
                return

            # 2. Validar API key encriptada
            is_valid = False

            if device.api_key_encrypted:
                # Intentar con key encriptada (método preferido)
                decrypted = decrypt_api_key(device.api_key_encrypted)

                if not decrypted:
                    # API key corrupta o ENCRYPTION_KEY cambió
                    logger.error(f"[MQTT] API key corrupta para device {device_eui}")
                    AuditService.log(
                        db=db,
                        action_type="API_KEY_INVALID",
                        device_id=device.id,
                        extra_data={
                            "device_eui": device_eui,
                            "reason": "decryption_failed",
                            "source": "mqtt",
                            "topic": topic
                        }
                    )
                    self.error_count += 1
                    return

                if decrypted != api_key:
                    logger.warning(f"[MQTT] API key inválida para device {device_eui}")
                    AuditService.log(
                        db=db,
                        action_type="API_KEY_INVALID",
                        device_id=device.id,
                        extra_data={
                            "device_eui": device_eui,
                            "reason": "key_mismatch",
                            "source": "mqtt",
                            "topic": topic
                        }
                    )
                    self.error_count += 1
                    return

                is_valid = True

            elif device.api_key:
                # Fallback a plaintext (backward compatibility)
                if device.api_key != api_key:
                    logger.warning(f"[MQTT] API key plaintext inválida para device {device_eui}")
                    AuditService.log(
                        db=db,
                        action_type="API_KEY_INVALID",
                        device_id=device.id,
                        extra_data={
                            "device_eui": device_eui,
                            "reason": "plaintext_key_mismatch",
                            "source": "mqtt",
                            "topic": topic
                        }
                    )
                    self.error_count += 1
                    return

                logger.warning(f"[MQTT] Device {device_eui} usando API key plaintext (deprecated)")
                is_valid = True

            else:
                # Device no tiene API key configurada
                logger.error(f"[MQTT] Device {device_eui} sin API key configurada")
                AuditService.log(
                    db=db,
                    action_type="API_KEY_INVALID",
                    device_id=device.id,
                    extra_data={
                        "device_eui": device_eui,
                        "reason": "no_api_key_configured",
                        "source": "mqtt",
                        "topic": topic
                    }
                )
                self.error_count += 1
                return

            if not is_valid:
                return

            # 3. Parsear timestamp (si no se provee, usar datetime actual)
            if timestamp:
                try:
                    # Intentar parsear ISO 8601
                    reading_timestamp = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
                except (ValueError, AttributeError) as e:
                    logger.warning(f"[MQTT] Timestamp inválido '{timestamp}': {e}. Usando datetime.utcnow()")
                    reading_timestamp = datetime.utcnow()
            else:
                reading_timestamp = datetime.utcnow()

            # 4. Crear SensorReading
            reading = SensorReading(
                device_id=device.id,
                data_payload=data_payload,
                timestamp=reading_timestamp,
                processed=False,
                quality_score=1.0  # TODO: Implementar cálculo de quality score
            )
            db.add(reading)

            # 5. Actualizar last_seen_at del device
            device.last_seen_at = datetime.utcnow()

            # Commit todo junto
            db.commit()

            # Log success
            logger.info(f"[MQTT] Reading creada para {device_eui}: {list(data_payload.keys())} (ID: {reading.id})")
            self.message_count += 1

        except Exception as e:
            db.rollback()
            logger.error(f"[MQTT] Error al procesar telemetría de {device_eui}: {e}")
            logger.exception(e)
            self.error_count += 1

        finally:
            db.close()

    def on_subscribe(self, client, userdata, mid, granted_qos):
        """
        Callback al subscribirse exitosamente.

        Args:
            client: Cliente MQTT
            userdata: Datos de usuario (no usado)
            mid: Message ID
            granted_qos: QoS otorgado por el broker
        """
        logger.debug(f"[MQTT] Subscripción exitosa (mid={mid}, qos={granted_qos})")

    def on_log(self, client, userdata, level, buf):
        """
        Callback de logs internos del cliente MQTT.

        Args:
            client: Cliente MQTT
            userdata: Datos de usuario (no usado)
            level: Nivel de log
            buf: Mensaje de log
        """
        # Solo logear errores y warnings
        if level == mqtt_client.MQTT_LOG_ERR:
            logger.error(f"[MQTT-LIB] {buf}")
        elif level == mqtt_client.MQTT_LOG_WARNING:
            logger.warning(f"[MQTT-LIB] {buf}")

    def start(self):
        """
        Inicia el cliente MQTT.

        Crea cliente, configura callbacks y conecta al broker.
        El loop corre en thread separado (non-blocking).
        """
        try:
            # Crear cliente MQTT (usar client_id fijo de settings o default)
            client_id = settings.mqtt_client_id if settings.mqtt_client_id else "iot_backend_main"

            # IMPORTANTE: Usar protocolo MQTT v3.1.1 explícitamente (compatible con Mosquitto 2.0)
            self.client = mqtt_client.Client(
                client_id=client_id,
                protocol=mqtt_client.MQTTv311  # Forzar MQTT 3.1.1
            )

            # Configurar callbacks
            self.client.on_connect = self.on_connect
            self.client.on_disconnect = self.on_disconnect
            self.client.on_message = self.on_message
            self.client.on_subscribe = self.on_subscribe
            self.client.on_log = self.on_log

            # Configurar credenciales si están definidas (ANTES de conectar)
            if settings.mqtt_username and settings.mqtt_password:
                self.client.username_pw_set(
                    settings.mqtt_username,
                    settings.mqtt_password
                )
                logger.info(f"[MQTT] Autenticación configurada para usuario: {settings.mqtt_username}")
                logger.info(f"[MQTT] Client ID: {client_id}")

            # Conectar al broker
            logger.info(f"[MQTT] Conectando a broker: {settings.mqtt_broker_host}:{settings.mqtt_broker_port}")
            self.client.connect(
                settings.mqtt_broker_host,
                settings.mqtt_broker_port,
                keepalive=60
            )

            # Iniciar loop en thread separado (non-blocking)
            self.client.loop_start()
            logger.info("[MQTT] Cliente MQTT iniciado en thread separado")

        except Exception as e:
            logger.error(f"[MQTT] Error al iniciar cliente MQTT: {e}")
            logger.exception(e)
            raise

    def stop(self):
        """
        Detiene el cliente MQTT.

        Desconecta del broker y detiene el loop thread.
        """
        if self.client:
            try:
                logger.info("[MQTT] Deteniendo cliente MQTT...")
                self.client.loop_stop()
                self.client.disconnect()
                logger.info("[MQTT] Cliente MQTT detenido exitosamente")
                logger.info(f"[MQTT] Estadísticas: {self.message_count} mensajes procesados, {self.error_count} errores")
            except Exception as e:
                logger.error(f"[MQTT] Error al detener cliente MQTT: {e}")

    def get_status(self) -> dict:
        """
        Obtiene estado actual del cliente MQTT.

        Returns:
            dict: Estado del cliente con estadísticas
        """
        return {
            "connected": self.connected,
            "message_count": self.message_count,
            "error_count": self.error_count,
            "broker_host": settings.mqtt_broker_host,
            "broker_port": settings.mqtt_broker_port
        }


# Instancia global (singleton)
mqtt_service = MQTTClientService()
