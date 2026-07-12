"""
Tests para endpoints de devices (CRUD + health + heartbeat).

Cubre: list, get, create, update, delete, schema, heartbeat, health.
RBAC: super_admin ve todo, technician filtrado por location.
"""

import pytest
from datetime import datetime, timedelta
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.models.device import Device
from app.models.sensor_reading import SensorReading


# ============================================================
# TESTS: GET /devices (listar)
# ============================================================

class TestListDevices:
    """Tests para GET /api/v1/devices"""

    def test_list_devices_admin(
        self, client: TestClient, auth_headers_admin: dict, device: Device
    ):
        """Admin puede ver todos los devices."""
        response = client.get("/api/v1/devices", headers=auth_headers_admin)

        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) >= 1
        assert any(d["device_eui"] == device.device_eui for d in data)

    def test_list_devices_technician_filtered(
        self,
        client: TestClient,
        auth_headers_technician: dict,
        device: Device,
        location,
        technician_user,
        db_session: Session,
    ):
        """Technician solo ve devices en sus locations permitidas."""
        # Actualizar technician para que tenga acceso a la location del device
        technician_user.allowed_location_ids = [location.id]
        db_session.commit()

        response = client.get("/api/v1/devices", headers=auth_headers_technician)

        assert response.status_code == 200
        data = response.json()
        assert len(data) >= 1

    def test_list_devices_pagination(
        self, client: TestClient, auth_headers_admin: dict, device: Device
    ):
        """Paginación con skip y limit."""
        response = client.get(
            "/api/v1/devices?skip=0&limit=1", headers=auth_headers_admin
        )

        assert response.status_code == 200
        data = response.json()
        assert len(data) <= 1

    def test_list_devices_unauthorized(self, client: TestClient):
        """Sin token retorna 403."""
        response = client.get("/api/v1/devices")
        assert response.status_code == 403


# ============================================================
# TESTS: GET /devices/{id}
# ============================================================

class TestGetDevice:
    """Tests para GET /api/v1/devices/{id}"""

    def test_get_device_success(
        self, client: TestClient, auth_headers_admin: dict, device: Device
    ):
        """Obtener device por ID."""
        response = client.get(
            f"/api/v1/devices/{device.id}", headers=auth_headers_admin
        )

        assert response.status_code == 200
        data = response.json()
        assert data["id"] == device.id
        assert data["device_eui"] == device.device_eui
        assert data["name"] == device.name

    def test_get_device_not_found(self, client: TestClient, auth_headers_admin: dict):
        """Device inexistente retorna 404."""
        response = client.get(
            "/api/v1/devices/999999", headers=auth_headers_admin
        )
        assert response.status_code == 404

    def test_get_device_unauthorized(self, client: TestClient, device: Device):
        """Sin token retorna 403."""
        response = client.get(f"/api/v1/devices/{device.id}")
        assert response.status_code == 403


# ============================================================
# TESTS: POST /devices (crear)
# ============================================================

class TestCreateDevice:
    """Tests para POST /api/v1/devices"""

    def test_create_device_success(
        self, client: TestClient, auth_headers_admin: dict, asset
    ):
        """Admin puede crear un device."""
        payload = {
            "asset_id": asset.id,
            "device_eui": "ESP32_NEW_001",
            "name": "New Device Test",
            "status": "active",
            "firmware_version": "v2.0.0",
            "api_key": "my_secret_api_key_123",
        }

        response = client.post(
            "/api/v1/devices", json=payload, headers=auth_headers_admin
        )

        assert response.status_code == 201
        data = response.json()
        assert data["device_eui"] == "ESP32_NEW_001"
        assert data["name"] == "New Device Test"
        # api_key se muestra solo en la respuesta de creación
        assert data["api_key"] == "my_secret_api_key_123"

    def test_create_device_duplicate_eui(
        self, client: TestClient, auth_headers_admin: dict, device: Device, asset
    ):
        """EUI duplicado retorna 400."""
        payload = {
            "asset_id": asset.id,
            "device_eui": device.device_eui,  # Ya existe
            "name": "Duplicate Device",
        }

        response = client.post(
            "/api/v1/devices", json=payload, headers=auth_headers_admin
        )

        assert response.status_code == 400
        assert "ya existe" in response.json()["detail"]

    def test_create_device_non_admin_forbidden(
        self, client: TestClient, auth_headers_technician: dict, asset
    ):
        """Technician no puede crear devices (403)."""
        payload = {
            "asset_id": asset.id,
            "device_eui": "ESP32_FORBIDDEN_001",
            "name": "Forbidden Device",
        }

        response = client.post(
            "/api/v1/devices", json=payload, headers=auth_headers_technician
        )

        assert response.status_code == 403


# ============================================================
# TESTS: PATCH /devices/{id} (actualizar)
# ============================================================

class TestUpdateDevice:
    """Tests para PATCH /api/v1/devices/{id}"""

    def test_update_device_name(
        self, client: TestClient, auth_headers_admin: dict, device: Device
    ):
        """Admin puede actualizar nombre de un device."""
        response = client.patch(
            f"/api/v1/devices/{device.id}",
            json={"name": "Updated Name"},
            headers=auth_headers_admin,
        )

        assert response.status_code == 200
        assert response.json()["name"] == "Updated Name"

    def test_update_device_status(
        self, client: TestClient, auth_headers_admin: dict, device: Device
    ):
        """Actualizar status de un device."""
        response = client.patch(
            f"/api/v1/devices/{device.id}",
            json={"status": "maintenance"},
            headers=auth_headers_admin,
        )

        assert response.status_code == 200
        assert response.json()["status"] == "maintenance"

    def test_update_device_not_found(
        self, client: TestClient, auth_headers_admin: dict
    ):
        """Actualizar device inexistente retorna 404."""
        response = client.patch(
            "/api/v1/devices/999999",
            json={"name": "Ghost"},
            headers=auth_headers_admin,
        )
        assert response.status_code == 404

    def test_update_device_non_admin_forbidden(
        self, client: TestClient, auth_headers_technician: dict, device: Device
    ):
        """Technician no puede actualizar devices."""
        response = client.patch(
            f"/api/v1/devices/{device.id}",
            json={"name": "Hacked Name"},
            headers=auth_headers_technician,
        )
        assert response.status_code == 403


# ============================================================
# TESTS: DELETE /devices/{id}
# ============================================================

class TestDeleteDevice:
    """Tests para DELETE /api/v1/devices/{id}"""

    def test_delete_device_success(
        self, client: TestClient, auth_headers_admin: dict, device: Device
    ):
        """Admin puede eliminar un device."""
        response = client.delete(
            f"/api/v1/devices/{device.id}", headers=auth_headers_admin
        )
        assert response.status_code == 204

        # Verificar que ya no existe
        get_resp = client.get(
            f"/api/v1/devices/{device.id}", headers=auth_headers_admin
        )
        assert get_resp.status_code == 404

    def test_delete_device_not_found(
        self, client: TestClient, auth_headers_admin: dict
    ):
        """Eliminar device inexistente retorna 404."""
        response = client.delete(
            "/api/v1/devices/999999", headers=auth_headers_admin
        )
        assert response.status_code == 404

    def test_delete_device_non_admin_forbidden(
        self, client: TestClient, auth_headers_technician: dict, device: Device
    ):
        """Technician no puede eliminar devices."""
        response = client.delete(
            f"/api/v1/devices/{device.id}", headers=auth_headers_technician
        )
        assert response.status_code == 403


# ============================================================
# TESTS: GET /devices/{id}/schema
# ============================================================

class TestDeviceSchema:
    """Tests para GET /api/v1/devices/{id}/schema"""

    def test_device_schema_empty(
        self, client: TestClient, auth_headers_admin: dict, device: Device
    ):
        """Device sin readings retorna schema vacío."""
        response = client.get(
            f"/api/v1/devices/{device.id}/schema", headers=auth_headers_admin
        )

        assert response.status_code == 200
        data = response.json()
        assert data["device_id"] == device.id
        assert data["variables"] == []

    def test_device_schema_with_readings(
        self,
        client: TestClient,
        auth_headers_admin: dict,
        device: Device,
        db_session: Session,
    ):
        """Device con readings retorna schema auto-descubierto."""
        reading = SensorReading(
            device_id=device.id,
            data_payload={"temp_c": 25.5, "humidity_pct": 60.0, "custom_val": 42},
            quality_score=0.95,
            timestamp=datetime.utcnow(),
        )
        db_session.add(reading)
        db_session.commit()

        response = client.get(
            f"/api/v1/devices/{device.id}/schema", headers=auth_headers_admin
        )

        assert response.status_code == 200
        data = response.json()
        keys = [v["key"] for v in data["variables"]]
        assert "temp_c" in keys
        assert "humidity_pct" in keys
        assert "custom_val" in keys

    def test_device_schema_not_found(
        self, client: TestClient, auth_headers_admin: dict
    ):
        """Schema de device inexistente retorna 404."""
        response = client.get(
            "/api/v1/devices/999999/schema", headers=auth_headers_admin
        )
        assert response.status_code == 404


# ============================================================
# TESTS: POST /devices/heartbeat
# ============================================================

class TestDeviceHeartbeat:
    """Tests para POST /api/v1/devices/heartbeat

    Desde 2026-07-11 el heartbeat exige el mismo contrato de autenticación
    que POST /readings: headers X-API-Key + X-Device-EUI.
    """

    HEARTBEAT_API_KEY = "test_heartbeat_key_123"

    @pytest.fixture
    def heartbeat_device(self, db_session: Session, asset) -> Device:
        """Device con API key para autenticar heartbeats."""
        device_obj = Device(
            asset_id=asset.id,
            device_eui="ESP32_HB_001",
            name="ESP32 Heartbeat Test",
            status="active",
            firmware_version="v1.0.0",
            api_key=self.HEARTBEAT_API_KEY,
            config={},
            extra_data={},
        )
        db_session.add(device_obj)
        db_session.commit()
        db_session.refresh(device_obj)
        return device_obj

    @pytest.fixture
    def heartbeat_headers(self, heartbeat_device: Device) -> dict:
        return {
            "X-API-Key": self.HEARTBEAT_API_KEY,
            "X-Device-EUI": heartbeat_device.device_eui,
        }

    def test_heartbeat_success(
        self,
        client: TestClient,
        heartbeat_device: Device,
        heartbeat_headers: dict,
        db_session: Session,
    ):
        """Heartbeat autenticado actualiza last_seen_at y firmware_version."""
        payload = {
            "device_eui": heartbeat_device.device_eui,
            "firmware_version": "v1.1.0",
            "metadata": {"rssi_dbm": -55, "uptime_sec": 3600},
        }

        response = client.post(
            "/api/v1/devices/heartbeat", json=payload, headers=heartbeat_headers
        )

        assert response.status_code == 200
        data = response.json()
        assert data["device_eui"] == heartbeat_device.device_eui
        assert data["is_online"] is True
        assert data["message"] == "Heartbeat recibido correctamente"

        # Verificar que firmware se actualizó
        db_session.refresh(heartbeat_device)
        assert heartbeat_device.firmware_version == "v1.1.0"

    def test_heartbeat_missing_device_eui_header(
        self, client: TestClient, heartbeat_device: Device
    ):
        """Regresión ticket X-Device-EUI: solo X-API-Key (firmware viejo) → 422."""
        payload = {"device_eui": heartbeat_device.device_eui}

        response = client.post(
            "/api/v1/devices/heartbeat",
            json=payload,
            headers={"X-API-Key": self.HEARTBEAT_API_KEY},
        )
        assert response.status_code == 422

    def test_heartbeat_without_auth_headers(
        self, client: TestClient, heartbeat_device: Device
    ):
        """Heartbeat sin ningún header de auth (contrato pre-2026-07-11) → 422."""
        payload = {"device_eui": heartbeat_device.device_eui}

        response = client.post("/api/v1/devices/heartbeat", json=payload)
        assert response.status_code == 422

    def test_heartbeat_invalid_api_key(
        self, client: TestClient, heartbeat_device: Device
    ):
        """Heartbeat con API key incorrecta → 401."""
        payload = {"device_eui": heartbeat_device.device_eui}

        response = client.post(
            "/api/v1/devices/heartbeat",
            json=payload,
            headers={
                "X-API-Key": "clave_incorrecta",
                "X-Device-EUI": heartbeat_device.device_eui,
            },
        )
        assert response.status_code == 401

    def test_heartbeat_device_not_found(self, client: TestClient):
        """Heartbeat con EUI inexistente en el header → 401 (auth falla)."""
        payload = {"device_eui": "ESP32_GHOST_999"}

        response = client.post(
            "/api/v1/devices/heartbeat",
            json=payload,
            headers={
                "X-API-Key": "cualquier_key",
                "X-Device-EUI": "ESP32_GHOST_999",
            },
        )
        assert response.status_code == 401

    def test_heartbeat_eui_mismatch(
        self, client: TestClient, heartbeat_device: Device, heartbeat_headers: dict
    ):
        """EUI del body distinto al del header autenticado → 400."""
        payload = {"device_eui": "ESP32_OTRO_DEVICE"}

        response = client.post(
            "/api/v1/devices/heartbeat", json=payload, headers=heartbeat_headers
        )
        assert response.status_code == 400


# ============================================================
# TESTS: Health endpoints
# ============================================================

class TestDeviceHealth:
    """Tests para /devices/health/summary y /devices/{id}/health"""

    def test_health_summary(
        self, client: TestClient, auth_headers_admin: dict, device: Device
    ):
        """Health summary retorna métricas agregadas."""
        response = client.get(
            "/api/v1/devices/health/summary", headers=auth_headers_admin
        )

        assert response.status_code == 200
        data = response.json()
        assert "total_devices" in data
        assert "online_devices" in data
        assert "offline_devices" in data
        assert data["total_devices"] >= 1

    def test_device_health_detail(
        self, client: TestClient, auth_headers_admin: dict, device: Device
    ):
        """Health detallada de un device."""
        response = client.get(
            f"/api/v1/devices/{device.id}/health", headers=auth_headers_admin
        )

        assert response.status_code == 200
        data = response.json()
        assert data["device_id"] == device.id
        assert data["device_eui"] == device.device_eui
        assert "status" in data
        assert "total_readings" in data

    def test_health_dashboard(
        self, client: TestClient, auth_headers_admin: dict, device: Device
    ):
        """Health dashboard retorna datos completos."""
        response = client.get(
            "/api/v1/devices/health/dashboard", headers=auth_headers_admin
        )

        assert response.status_code == 200
        data = response.json()
        assert "total_devices" in data
        assert "devices_online" in data
        assert "devices" in data
        assert isinstance(data["devices"], list)
