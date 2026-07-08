"""
Tests para endpoints de sensor readings (POST /readings, GET /readings).

POST /readings requiere headers X-API-Key + X-Device-EUI (autenticación de device).
GET /readings requiere Bearer token de usuario autenticado.
"""

import pytest
from datetime import datetime, timedelta
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.models.device import Device
from app.models.sensor_reading import SensorReading
from app.core.security import encrypt_api_key


# ============================================================
# FIXTURES específicas de readings
# ============================================================

DEVICE_API_KEY = "test_api_key_esp32_12345"


@pytest.fixture
def device_with_api_key(db_session: Session, asset) -> Device:
    """Device con API key plaintext para autenticación."""
    device_obj = Device(
        asset_id=asset.id,
        device_eui="ESP32_READING_001",
        name="ESP32 Reading Test",
        status="active",
        firmware_version="v1.0.0",
        api_key=DEVICE_API_KEY,
        config={"sampling_interval_sec": 300},
        extra_data={}
    )
    db_session.add(device_obj)
    db_session.commit()
    db_session.refresh(device_obj)
    return device_obj


@pytest.fixture
def device_with_encrypted_key(db_session: Session, asset) -> Device:
    """Device con API key encriptada (método nuevo)."""
    device_obj = Device(
        asset_id=asset.id,
        device_eui="ESP32_ENCRYPTED_001",
        name="ESP32 Encrypted Key",
        status="active",
        firmware_version="v1.0.0",
        api_key_encrypted=encrypt_api_key(DEVICE_API_KEY),
        config={"sampling_interval_sec": 300},
        extra_data={}
    )
    db_session.add(device_obj)
    db_session.commit()
    db_session.refresh(device_obj)
    return device_obj


@pytest.fixture
def api_headers(device_with_api_key: Device) -> dict:
    """Headers de autenticación de device (plaintext key)."""
    return {
        "X-API-Key": DEVICE_API_KEY,
        "X-Device-EUI": device_with_api_key.device_eui,
    }


@pytest.fixture
def api_headers_encrypted(device_with_encrypted_key: Device) -> dict:
    """Headers de autenticación de device (encrypted key)."""
    return {
        "X-API-Key": DEVICE_API_KEY,
        "X-Device-EUI": device_with_encrypted_key.device_eui,
    }


# ============================================================
# TESTS: POST /readings (ESP32 envía datos)
# ============================================================

class TestCreateReading:
    """Tests para POST /api/v1/readings (endpoint CRITICO para ESP32)"""

    def test_create_reading_success(
        self, client: TestClient, device_with_api_key: Device, api_headers: dict
    ):
        """Creación exitosa de un reading con API key plaintext."""
        payload = {
            "device_eui": device_with_api_key.device_eui,
            "data_payload": {
                "temp_c": 25.5,
                "humidity_pct": 62.3,
                "battery_mv": 3750,
            },
            "timestamp": datetime.utcnow().isoformat()
        }

        response = client.post("/api/v1/readings", json=payload, headers=api_headers)

        assert response.status_code == 201
        data = response.json()
        assert data["device_id"] == device_with_api_key.id
        assert data["data_payload"]["temp_c"] == 25.5
        assert data["data_payload"]["humidity_pct"] == 62.3
        assert "quality_score" in data
        assert data["processed"] is False

    def test_create_reading_encrypted_key(
        self, client: TestClient, device_with_encrypted_key: Device, api_headers_encrypted: dict
    ):
        """Creación exitosa con API key encriptada (método preferido)."""
        payload = {
            "device_eui": device_with_encrypted_key.device_eui,
            "data_payload": {"temp_c": 22.0},
        }

        response = client.post("/api/v1/readings", json=payload, headers=api_headers_encrypted)

        assert response.status_code == 201
        data = response.json()
        assert data["device_id"] == device_with_encrypted_key.id

    def test_create_reading_auto_timestamp(
        self, client: TestClient, device_with_api_key: Device, api_headers: dict
    ):
        """Si no se envía timestamp, se asigna automáticamente."""
        payload = {
            "device_eui": device_with_api_key.device_eui,
            "data_payload": {"temp_c": 24.0},
        }

        response = client.post("/api/v1/readings", json=payload, headers=api_headers)

        assert response.status_code == 201
        data = response.json()
        assert "timestamp" in data
        assert data["timestamp"] is not None

    def test_create_reading_updates_last_seen(
        self, client: TestClient, device_with_api_key: Device, api_headers: dict, db_session: Session
    ):
        """Crear reading actualiza device.last_seen_at."""
        initial_last_seen = device_with_api_key.last_seen_at

        payload = {
            "device_eui": device_with_api_key.device_eui,
            "data_payload": {"temp_c": 26.0},
        }

        response = client.post("/api/v1/readings", json=payload, headers=api_headers)
        assert response.status_code == 201

        db_session.refresh(device_with_api_key)
        assert device_with_api_key.last_seen_at is not None
        assert device_with_api_key.last_seen_at != initial_last_seen

    def test_create_reading_invalid_api_key(
        self, client: TestClient, device_with_api_key: Device
    ):
        """API key incorrecta retorna 401."""
        headers = {
            "X-API-Key": "wrong_key_12345",
            "X-Device-EUI": device_with_api_key.device_eui,
        }
        payload = {
            "device_eui": device_with_api_key.device_eui,
            "data_payload": {"temp_c": 25.0},
        }

        response = client.post("/api/v1/readings", json=payload, headers=headers)

        assert response.status_code == 401

    def test_create_reading_missing_headers(self, client: TestClient):
        """Sin headers X-API-Key/X-Device-EUI retorna 422."""
        payload = {
            "device_eui": "ESP32_READING_001",
            "data_payload": {"temp_c": 25.0},
        }

        response = client.post("/api/v1/readings", json=payload)

        assert response.status_code == 422

    def test_create_reading_device_not_found(self, client: TestClient):
        """Device EUI inexistente retorna 401."""
        headers = {
            "X-API-Key": "some_key",
            "X-Device-EUI": "ESP32_NONEXISTENT",
        }
        payload = {
            "device_eui": "ESP32_NONEXISTENT",
            "data_payload": {"temp_c": 25.0},
        }

        response = client.post("/api/v1/readings", json=payload, headers=headers)

        assert response.status_code == 401

    def test_create_reading_eui_mismatch(
        self, client: TestClient, device_with_api_key: Device, api_headers: dict
    ):
        """EUI en body distinto al del header retorna 400."""
        payload = {
            "device_eui": "ESP32_DIFERENTE_999",
            "data_payload": {"temp_c": 25.0},
        }

        response = client.post("/api/v1/readings", json=payload, headers=api_headers)

        assert response.status_code == 400
        assert "no coincide" in response.json()["detail"]

    def test_create_reading_quality_score_good(
        self, client: TestClient, device_with_api_key: Device, api_headers: dict
    ):
        """Payload con valores normales genera quality_score alto."""
        payload = {
            "device_eui": device_with_api_key.device_eui,
            "data_payload": {"temp_c": 25.0, "humidity_pct": 60.0},
        }

        response = client.post("/api/v1/readings", json=payload, headers=api_headers)

        assert response.status_code == 201
        assert response.json()["quality_score"] >= 0.9

    def test_create_reading_quality_score_low(
        self, client: TestClient, device_with_api_key: Device, api_headers: dict
    ):
        """Payload con valores de error (-999) genera quality_score bajo."""
        payload = {
            "device_eui": device_with_api_key.device_eui,
            "data_payload": {
                "temp_c": -999.0,
                "humidity_pct": -999.0,
                "pressure": -999.0,
            },
        }

        response = client.post("/api/v1/readings", json=payload, headers=api_headers)

        assert response.status_code == 201
        assert response.json()["quality_score"] < 0.5

    def test_create_reading_multiple_sensors(
        self, client: TestClient, device_with_api_key: Device, api_headers: dict
    ):
        """Payload con múltiples sensores se guarda completo."""
        sensors = {
            "temp_c": 25.5,
            "humidity_pct": 62.3,
            "pressure_bar": 1.013,
            "battery_mv": 3750,
            "rssi_dbm": -65,
            "co2_ppm": 412,
        }
        payload = {
            "device_eui": device_with_api_key.device_eui,
            "data_payload": sensors,
        }

        response = client.post("/api/v1/readings", json=payload, headers=api_headers)

        assert response.status_code == 201
        data = response.json()
        for key, val in sensors.items():
            assert data["data_payload"][key] == val


# ============================================================
# TESTS: GET /readings (usuario autenticado)
# ============================================================

class TestGetReadings:
    """Tests para GET /api/v1/readings"""

    def test_get_readings_list(
        self, client: TestClient, auth_headers_admin: dict, device: Device, db_session: Session
    ):
        """Lista de readings para un admin."""
        for i in range(5):
            reading = SensorReading(
                device_id=device.id,
                data_payload={"temp_c": 20.0 + i},
                quality_score=0.95,
                processed=False,
                timestamp=datetime.utcnow()
            )
            db_session.add(reading)
        db_session.commit()

        response = client.get("/api/v1/readings", headers=auth_headers_admin)

        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) == 5

    def test_get_readings_filter_by_device(
        self, client: TestClient, auth_headers_admin: dict, device: Device, db_session: Session
    ):
        """Filtrar readings por device_id."""
        for i in range(3):
            db_session.add(SensorReading(
                device_id=device.id,
                data_payload={"temp_c": 20.0 + i},
                quality_score=0.95,
                timestamp=datetime.utcnow()
            ))
        db_session.commit()

        response = client.get(
            f"/api/v1/readings?device_id={device.id}",
            headers=auth_headers_admin
        )

        assert response.status_code == 200
        data = response.json()
        assert len(data) == 3
        for r in data:
            assert r["device_id"] == device.id

    def test_get_readings_filter_by_date_range(
        self, client: TestClient, auth_headers_admin: dict, device: Device, db_session: Session
    ):
        """Filtrar por rango de fechas."""
        now = datetime.utcnow()

        db_session.add(SensorReading(
            device_id=device.id,
            data_payload={"temp_c": 20.0},
            quality_score=0.95,
            timestamp=now - timedelta(days=10)
        ))
        db_session.add(SensorReading(
            device_id=device.id,
            data_payload={"temp_c": 25.0},
            quality_score=0.95,
            timestamp=now
        ))
        db_session.commit()

        date_from = (now - timedelta(days=1)).isoformat()
        response = client.get(
            f"/api/v1/readings?date_from={date_from}",
            headers=auth_headers_admin
        )

        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
        assert data[0]["data_payload"]["temp_c"] == 25.0

    def test_get_readings_unauthorized(self, client: TestClient):
        """GET /readings sin token retorna 403."""
        response = client.get("/api/v1/readings")
        assert response.status_code == 403

    def test_get_readings_empty(self, client: TestClient, auth_headers_admin: dict):
        """Lista vacía cuando no hay readings."""
        response = client.get("/api/v1/readings", headers=auth_headers_admin)

        assert response.status_code == 200
        assert response.json() == []

    def test_get_readings_pagination(
        self, client: TestClient, auth_headers_admin: dict, device: Device, db_session: Session
    ):
        """Paginación de readings."""
        for i in range(25):
            db_session.add(SensorReading(
                device_id=device.id,
                data_payload={"temp_c": 20.0 + i},
                quality_score=0.95,
                timestamp=datetime.utcnow()
            ))
        db_session.commit()

        # Primera página
        resp1 = client.get("/api/v1/readings?skip=0&limit=10", headers=auth_headers_admin)
        assert resp1.status_code == 200
        assert len(resp1.json()) == 10

        # Segunda página
        resp2 = client.get("/api/v1/readings?skip=10&limit=10", headers=auth_headers_admin)
        assert resp2.status_code == 200
        assert len(resp2.json()) == 10


# ============================================================
# TESTS: GET /readings/{id}
# ============================================================

class TestGetReadingById:
    """Tests para GET /api/v1/readings/{id}"""

    def test_get_reading_by_id_success(
        self, client: TestClient, auth_headers_admin: dict, device: Device, db_session: Session
    ):
        """Obtener reading por ID."""
        reading = SensorReading(
            device_id=device.id,
            data_payload={"temp_c": 25.5, "humidity_pct": 60.0},
            quality_score=0.95,
            timestamp=datetime.utcnow()
        )
        db_session.add(reading)
        db_session.commit()
        db_session.refresh(reading)

        response = client.get(f"/api/v1/readings/{reading.id}", headers=auth_headers_admin)

        assert response.status_code == 200
        data = response.json()
        assert data["id"] == reading.id
        assert data["data_payload"]["temp_c"] == 25.5

    def test_get_reading_by_id_not_found(self, client: TestClient, auth_headers_admin: dict):
        """Reading inexistente retorna 404."""
        response = client.get("/api/v1/readings/999999", headers=auth_headers_admin)
        assert response.status_code == 404

    def test_get_reading_by_id_unauthorized(
        self, client: TestClient, device: Device, db_session: Session
    ):
        """GET /readings/{id} sin token retorna 403."""
        reading = SensorReading(
            device_id=device.id,
            data_payload={"temp_c": 25.5},
            quality_score=0.95,
            timestamp=datetime.utcnow()
        )
        db_session.add(reading)
        db_session.commit()
        db_session.refresh(reading)

        response = client.get(f"/api/v1/readings/{reading.id}")
        assert response.status_code == 403


class TestExportReadings:
    """Tests para GET /api/v1/readings/export"""

    def test_export_route_not_shadowed_by_reading_id(
        self, client: TestClient, auth_headers_admin: dict
    ):
        """Regresión: /export debe registrarse antes que /{reading_id}.

        Si el orden es incorrecto, FastAPI intenta parsear "export" como int
        y responde 422 en vez de llegar al endpoint.
        """
        response = client.get("/api/v1/readings/export", headers=auth_headers_admin)
        assert response.status_code != 422

    def test_export_csv_success(
        self, client: TestClient, auth_headers_admin: dict, device: Device, db_session: Session
    ):
        """Export CSV devuelve archivo descargable con los readings."""
        reading = SensorReading(
            device_id=device.id,
            data_payload={"temp_c": 25.5, "humidity_pct": 60.0},
            quality_score=0.95,
            timestamp=datetime.utcnow()
        )
        db_session.add(reading)
        db_session.commit()

        response = client.get(
            "/api/v1/readings/export?format=csv",
            headers=auth_headers_admin
        )

        assert response.status_code == 200
        assert response.headers["content-type"].startswith("text/csv")
        assert "attachment" in response.headers["content-disposition"]
        assert "temp_c" in response.text

    def test_export_no_data_returns_404(
        self, client: TestClient, auth_headers_admin: dict
    ):
        """Export sin readings que matcheen los filtros retorna 404."""
        response = client.get(
            "/api/v1/readings/export?device_id=999999",
            headers=auth_headers_admin
        )
        assert response.status_code == 404

    def test_export_unauthorized(self, client: TestClient):
        """Export sin token retorna 403."""
        response = client.get("/api/v1/readings/export")
        assert response.status_code == 403


# ============================================================
# TESTS: Integración end-to-end
# ============================================================

class TestReadingsIntegration:
    """Tests de integración: ESP32 envía → Backend almacena → Frontend consulta."""

    def test_full_esp32_workflow(
        self,
        client: TestClient,
        auth_headers_admin: dict,
        device_with_api_key: Device,
        api_headers: dict,
        db_session: Session
    ):
        """
        Flujo completo:
        1. ESP32 envía reading con X-API-Key
        2. Backend almacena y actualiza last_seen
        3. Frontend obtiene el reading
        """
        # 1. ESP32 envía datos
        payload = {
            "device_eui": device_with_api_key.device_eui,
            "data_payload": {
                "temp_c": 25.5,
                "humidity_pct": 62.3,
                "battery_mv": 3750,
            }
        }
        create_resp = client.post("/api/v1/readings", json=payload, headers=api_headers)
        assert create_resp.status_code == 201
        reading_id = create_resp.json()["id"]

        # 2. Verificar que device.last_seen_at se actualizó
        db_session.refresh(device_with_api_key)
        assert device_with_api_key.last_seen_at is not None

        # 3. Frontend obtiene el reading
        get_resp = client.get(
            f"/api/v1/readings/{reading_id}",
            headers=auth_headers_admin
        )
        assert get_resp.status_code == 200
        data = get_resp.json()
        assert data["data_payload"]["temp_c"] == 25.5
        assert data["data_payload"]["humidity_pct"] == 62.3

    def test_multiple_devices_readings(
        self,
        client: TestClient,
        auth_headers_admin: dict,
        device_with_api_key: Device,
        device_with_encrypted_key: Device,
        api_headers: dict,
        api_headers_encrypted: dict,
    ):
        """Dos devices (plaintext y encrypted key) envían readings simultáneamente."""
        payload1 = {
            "device_eui": device_with_api_key.device_eui,
            "data_payload": {"temp_c": 25.0},
        }
        payload2 = {
            "device_eui": device_with_encrypted_key.device_eui,
            "data_payload": {"temp_c": 30.0},
        }

        resp1 = client.post("/api/v1/readings", json=payload1, headers=api_headers)
        resp2 = client.post("/api/v1/readings", json=payload2, headers=api_headers_encrypted)

        assert resp1.status_code == 201
        assert resp2.status_code == 201

        # Filtrar por device
        resp = client.get(
            f"/api/v1/readings?device_id={device_with_api_key.id}",
            headers=auth_headers_admin
        )
        data = resp.json()
        assert len(data) == 1
        assert data[0]["data_payload"]["temp_c"] == 25.0
