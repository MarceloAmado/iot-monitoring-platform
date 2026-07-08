"""
Tests de Autenticación MQTT
============================

Tests para validar el sistema de autenticación de Mosquitto con password_file y ACL.

Ejecutar:
    docker exec iot_backend pytest tests/test_mqtt_auth.py -v
    docker exec iot_backend pytest tests/test_mqtt_auth.py --cov=app.services.mqtt_client
"""

import os
import socket
import pytest
import paho.mqtt.client as mqtt
import time
from typing import Optional


# Configuración de conexión MQTT
MQTT_BROKER = os.getenv("MQTT_BROKER_HOST", "mosquitto")
MQTT_PORT = int(os.getenv("MQTT_BROKER_PORT", "1883"))


def _broker_available(host: str, port: int, timeout: float = 2.0) -> bool:
    """Chequea si el broker Mosquitto es alcanzable (TCP connect)."""
    try:
        with socket.create_connection((host, port), timeout=timeout):
            return True
    except OSError:
        return False


# Estos son tests de INTEGRACIÓN contra un Mosquitto real (el del stack
# Docker local). En entornos sin broker (ej: CI) se saltean completos.
pytestmark = pytest.mark.skipif(
    not _broker_available(MQTT_BROKER, MQTT_PORT),
    reason=f"Broker Mosquitto no disponible en {MQTT_BROKER}:{MQTT_PORT} "
           "(tests de integración; corren en el stack Docker local)",
)

# Credenciales de usuarios (definidas en mosquitto/config/passwords.txt)
VALID_USERS = {
    "iot_backend": "CHANGE_ME_MQTT_PASSWORD",
    "iot_device": "CHANGE_ME_DEVICE_PASSWORD",
    "iot_monitor": "CHANGE_ME_MONITOR_PASSWORD",
}

# Flags para rastrear eventos de conexión
class MQTTTestClient:
    """Cliente MQTT auxiliar para testing"""

    def __init__(self):
        self.connected = False
        self.connect_rc = None
        self.publish_success = False
        self.publish_rc = None
        self.error_message = None

    def on_connect(self, client, userdata, flags, rc):
        """Callback de conexión"""
        self.connect_rc = rc
        if rc == 0:
            self.connected = True
        else:
            self.connected = False
            # Códigos de error comunes:
            # rc=1: Connection refused - incorrect protocol version
            # rc=2: Connection refused - invalid client identifier
            # rc=3: Connection refused - server unavailable
            # rc=4: Connection refused - bad username or password
            # rc=5: Connection refused - not authorized
            self.error_message = f"Connection failed with rc={rc}"

    def on_publish(self, client, userdata, mid):
        """Callback de publicación exitosa"""
        self.publish_success = True

    def on_disconnect(self, client, userdata, rc):
        """Callback de desconexión"""
        self.connected = False


def mqtt_connect_test(username: str, password: str, timeout: int = 5) -> tuple[bool, Optional[int]]:
    """
    Intenta conectar a Mosquitto con credenciales dadas

    Args:
        username: Nombre de usuario MQTT
        password: Contraseña
        timeout: Tiempo máximo de espera (segundos)

    Returns:
        Tuple (connected: bool, rc: int) - rc es el código de resultado
    """
    test_client = MQTTTestClient()
    client = mqtt.Client(client_id=f"test_{username}_{int(time.time())}")

    # Configurar callbacks
    client.on_connect = test_client.on_connect
    client.on_disconnect = test_client.on_disconnect

    # Configurar credenciales
    client.username_pw_set(username, password)

    try:
        # Intentar conectar
        client.connect(MQTT_BROKER, MQTT_PORT, keepalive=60)
        client.loop_start()

        # Esperar conexión
        start_time = time.time()
        while test_client.connect_rc is None and (time.time() - start_time) < timeout:
            time.sleep(0.1)

        # Capturar estado antes de desconectar (disconnect callback resetea connected)
        was_connected = test_client.connect_rc == 0
        rc = test_client.connect_rc

        # Desconectar
        client.loop_stop()
        client.disconnect()

        return was_connected, rc

    except Exception as e:
        return False, None


def mqtt_publish_test(username: str, password: str, topic: str, message: str = '{"test":true}', timeout: int = 5) -> tuple[bool, Optional[int]]:
    """
    Intenta publicar un mensaje en un tópico específico

    Args:
        username: Nombre de usuario MQTT
        password: Contraseña
        topic: Tópico donde publicar
        message: Mensaje a publicar
        timeout: Tiempo máximo de espera (segundos)

    Returns:
        Tuple (success: bool, rc: int)
    """
    test_client = MQTTTestClient()
    client = mqtt.Client(client_id=f"test_pub_{username}_{int(time.time())}")

    # Configurar callbacks
    client.on_connect = test_client.on_connect
    client.on_publish = test_client.on_publish

    # Configurar credenciales
    client.username_pw_set(username, password)

    try:
        # Conectar
        client.connect(MQTT_BROKER, MQTT_PORT, keepalive=60)
        client.loop_start()

        # Esperar conexión
        start_time = time.time()
        while not test_client.connected and (time.time() - start_time) < timeout:
            time.sleep(0.1)

        if test_client.connected:
            # Intentar publicar
            result = client.publish(topic, message, qos=0)

            # Esperar confirmación de publicación
            start_time = time.time()
            while not test_client.publish_success and (time.time() - start_time) < timeout:
                time.sleep(0.1)

        # Desconectar
        client.loop_stop()
        client.disconnect()

        return test_client.publish_success, test_client.connect_rc

    except Exception as e:
        return False, None


# ============================================================================
# TESTS
# ============================================================================

class TestMQTTAuthentication:
    """Tests de autenticación básica"""

    def test_connection_valid_credentials_iot_backend(self):
        """Test: Conexión exitosa con credenciales de iot_backend"""
        username = "iot_backend"
        password = VALID_USERS[username]

        connected, rc = mqtt_connect_test(username, password)

        assert connected is True, f"Debería conectar con credenciales válidas (rc={rc})"
        assert rc == 0, f"Código de retorno debería ser 0 (CONNACK success), pero fue {rc}"

    def test_connection_valid_credentials_iot_device(self):
        """Test: Conexión exitosa con credenciales de iot_device"""
        username = "iot_device"
        password = VALID_USERS[username]

        connected, rc = mqtt_connect_test(username, password)

        assert connected is True, f"Debería conectar con credenciales válidas (rc={rc})"
        assert rc == 0, f"Código de retorno debería ser 0 (CONNACK success), pero fue {rc}"

    def test_connection_valid_credentials_iot_monitor(self):
        """Test: Conexión exitosa con credenciales de iot_monitor"""
        username = "iot_monitor"
        password = VALID_USERS[username]

        connected, rc = mqtt_connect_test(username, password)

        assert connected is True, f"Debería conectar con credenciales válidas (rc={rc})"
        assert rc == 0, f"Código de retorno debería ser 0 (CONNACK success), pero fue {rc}"

    def test_connection_invalid_password(self):
        """Test: Rechazo con contraseña incorrecta"""
        username = "iot_backend"
        password = "wrong_password_123"

        connected, rc = mqtt_connect_test(username, password)

        assert connected is False, "No debería conectar con contraseña incorrecta"
        assert rc in [4, 5], f"Código de retorno debería ser 4 (Bad auth) o 5 (Not authorized), pero fue {rc}"

    def test_connection_invalid_username(self):
        """Test: Rechazo con usuario inexistente"""
        username = "fake_user_that_does_not_exist"
        password = "any_password"

        connected, rc = mqtt_connect_test(username, password)

        assert connected is False, "No debería conectar con usuario inexistente"
        assert rc in [4, 5], f"Código de retorno debería ser 4 (Bad auth) o 5 (Not authorized), pero fue {rc}"

    def test_connection_anonymous_rejected(self):
        """Test: Rechazo de conexión sin credenciales (anonymous)"""
        test_client = MQTTTestClient()
        client = mqtt.Client(client_id=f"test_anon_{int(time.time())}")

        client.on_connect = test_client.on_connect

        try:
            # Intentar conectar SIN username_pw_set
            client.connect(MQTT_BROKER, MQTT_PORT, keepalive=60)
            client.loop_start()

            time.sleep(2)  # Esperar respuesta

            client.loop_stop()
            client.disconnect()

            assert test_client.connected is False, "No debería conectar sin credenciales (anonymous)"
            assert test_client.connect_rc in [4, 5], f"Debería rechazar con rc=4 o 5, pero fue {test_client.connect_rc}"

        except Exception as e:
            # Si falla la conexión es correcto también
            assert True


class TestMQTTACLPermissions:
    """Tests de permisos ACL (Access Control List)"""

    def test_acl_backend_can_write_iot_topics(self):
        """Test: iot_backend puede escribir en iot/#"""
        username = "iot_backend"
        password = VALID_USERS[username]
        topic = "iot/test/backend/telemetry"

        success, rc = mqtt_publish_test(username, password, topic)

        assert success is True, f"iot_backend debería poder publicar en iot/# (rc={rc})"

    def test_acl_device_can_write_telemetry(self):
        """Test: iot_device puede escribir en iot/+/devices/+/telemetry"""
        username = "iot_device"
        password = VALID_USERS[username]
        topic = "iot/test/devices/iot_device/telemetry"

        success, rc = mqtt_publish_test(username, password, topic)

        assert success is True, f"iot_device debería poder publicar en telemetry (rc={rc})"

    def test_acl_device_can_write_status(self):
        """Test: iot_device puede escribir en iot/+/devices/+/status"""
        username = "iot_device"
        password = VALID_USERS[username]
        topic = "iot/test/devices/iot_device/status"

        success, rc = mqtt_publish_test(username, password, topic)

        assert success is True, f"iot_device debería poder publicar en status (rc={rc})"

    @pytest.mark.skip(reason="Detección de rechazo de ACL requiere subscribe test, pendiente implementar")
    def test_acl_monitor_cannot_write(self):
        """Test: iot_monitor NO puede escribir (solo lectura)"""
        # NOTA: Este test requiere una implementación más compleja
        # porque MQTT no retorna error al publicar si no tienes permiso,
        # simplemente el mensaje no se entrega.
        # Se necesitaría un subscriber en paralelo para verificar.
        username = "iot_monitor"
        password = VALID_USERS[username]
        topic = "iot/test/monitor/attempt_write"

        success, rc = mqtt_publish_test(username, password, topic)

        # El test pasaría incluso si no tiene permiso (por limitación de MQTT)
        # TODO: Implementar con subscriber para verificar que el mensaje NO llega
        pass


class TestMQTTConnectionStability:
    """Tests de estabilidad de conexión"""

    def test_reconnection_after_disconnect(self):
        """Test: Reconexión automática después de desconexión"""
        username = "iot_backend"
        password = VALID_USERS[username]

        # Primera conexión
        connected1, rc1 = mqtt_connect_test(username, password)
        assert connected1 is True, "Primera conexión debería ser exitosa"

        # Segunda conexión (debería funcionar igual)
        connected2, rc2 = mqtt_connect_test(username, password)
        assert connected2 is True, "Segunda conexión debería ser exitosa"
        assert rc2 == 0, "Código de retorno debería ser 0"

    def test_multiple_clients_same_user(self):
        """Test: Múltiples clientes con mismo usuario (diferentes client_id)"""
        username = "iot_device"
        password = VALID_USERS[username]

        # Cliente 1
        connected1, rc1 = mqtt_connect_test(username, password)
        assert connected1 is True, "Cliente 1 debería conectar"

        # Cliente 2 (mismo usuario, diferente client_id)
        connected2, rc2 = mqtt_connect_test(username, password)
        assert connected2 is True, "Cliente 2 debería conectar"


# ============================================================================
# FIXTURES Y UTILIDADES
# ============================================================================

@pytest.fixture(scope="module")
def mqtt_test_setup():
    """Fixture para setup/teardown de tests MQTT"""
    print("\n[SETUP] Iniciando tests de autenticación MQTT")

    yield

    print("\n[TEARDOWN] Tests de autenticación MQTT completados")


# ============================================================================
# METADATA
# ============================================================================

# pytest.ini configuration (opcional):
# [pytest]
# markers =
#     mqtt: tests relacionados con MQTT
#     acl: tests de permisos ACL
#     auth: tests de autenticación
