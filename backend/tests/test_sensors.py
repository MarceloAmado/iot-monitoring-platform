"""
Tests para endpoints del catálogo de sensores (/api/v1/sensors).

RBAC:
- Listar/leer/stats: cualquier usuario autenticado
- Crear/actualizar/activar/desactivar: super_admin y service_admin
- Eliminar: solo super_admin
"""

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.models.sensor_catalog import SensorCatalog


@pytest.fixture
def sensor(db_session: Session) -> SensorCatalog:
    """Sensor de catálogo para tests."""
    sensor_obj = SensorCatalog(
        name="DS18B20 Test",
        sensor_type="temperature",
        protocol="OneWire",
        unit="°C",
        is_active=True,
        is_builtin=False,
    )
    db_session.add(sensor_obj)
    db_session.commit()
    db_session.refresh(sensor_obj)
    return sensor_obj


class TestListSensors:
    """Tests para GET /api/v1/sensors/"""

    def test_list_sensors(
        self, client: TestClient, auth_headers_admin: dict, sensor: SensorCatalog
    ):
        """Listar sensores retorna los existentes."""
        response = client.get("/api/v1/sensors/", headers=auth_headers_admin)

        assert response.status_code == 200
        assert any(s["name"] == "DS18B20 Test" for s in response.json())

    def test_list_sensors_filter_by_type(
        self, client: TestClient, auth_headers_admin: dict, sensor: SensorCatalog
    ):
        """Filtrar sensores por tipo."""
        response = client.get(
            "/api/v1/sensors/?sensor_type=temperature", headers=auth_headers_admin
        )

        assert response.status_code == 200
        assert all(s["sensor_type"] == "temperature" for s in response.json())

    def test_sensor_stats(
        self, client: TestClient, auth_headers_admin: dict, sensor: SensorCatalog
    ):
        """Stats del catálogo de sensores."""
        response = client.get("/api/v1/sensors/stats", headers=auth_headers_admin)

        assert response.status_code == 200
        data = response.json()
        assert data["total"] >= 1


class TestCreateSensor:
    """Tests para POST /api/v1/sensors/"""

    def test_create_sensor_as_admin(self, client: TestClient, auth_headers_admin: dict):
        """Super admin puede crear un sensor."""
        response = client.post(
            "/api/v1/sensors/",
            json={
                "name": "DHT22 Nuevo",
                "sensor_type": "humidity",
                "protocol": "Digital",
                "unit": "%",
            },
            headers=auth_headers_admin,
        )

        assert response.status_code == 201
        data = response.json()
        assert data["name"] == "DHT22 Nuevo"
        assert data["is_builtin"] is False

    def test_create_sensor_duplicate_name(
        self, client: TestClient, auth_headers_admin: dict, sensor: SensorCatalog
    ):
        """Crear sensor con nombre duplicado retorna 400."""
        response = client.post(
            "/api/v1/sensors/",
            json={"name": "DS18B20 Test", "sensor_type": "temperature"},
            headers=auth_headers_admin,
        )
        assert response.status_code == 400

    def test_create_sensor_invalid_range(
        self, client: TestClient, auth_headers_admin: dict
    ):
        """value_min >= value_max retorna 400."""
        response = client.post(
            "/api/v1/sensors/",
            json={
                "name": "Sensor Rango Invalido",
                "sensor_type": "temperature",
                "value_min": 100,
                "value_max": 10,
            },
            headers=auth_headers_admin,
        )
        assert response.status_code == 400

    def test_create_sensor_as_technician_forbidden(
        self, client: TestClient, auth_headers_technician: dict
    ):
        """Technician NO puede crear sensores (403)."""
        response = client.post(
            "/api/v1/sensors/",
            json={"name": "No deberia", "sensor_type": "custom"},
            headers=auth_headers_technician,
        )
        assert response.status_code == 403


class TestSensorDetail:
    """Tests para GET/PATCH/DELETE /api/v1/sensors/{id}"""

    def test_get_sensor_by_id(
        self, client: TestClient, auth_headers_admin: dict, sensor: SensorCatalog
    ):
        """Obtener sensor por ID."""
        response = client.get(f"/api/v1/sensors/{sensor.id}", headers=auth_headers_admin)

        assert response.status_code == 200
        assert response.json()["name"] == "DS18B20 Test"

    def test_get_sensor_not_found(self, client: TestClient, auth_headers_admin: dict):
        """Sensor inexistente retorna 404."""
        response = client.get("/api/v1/sensors/999999", headers=auth_headers_admin)
        assert response.status_code == 404

    def test_update_sensor(
        self, client: TestClient, auth_headers_admin: dict, sensor: SensorCatalog
    ):
        """Actualizar un sensor."""
        response = client.patch(
            f"/api/v1/sensors/{sensor.id}",
            json={"description": "Sensor actualizado"},
            headers=auth_headers_admin,
        )

        assert response.status_code == 200
        assert response.json()["description"] == "Sensor actualizado"

    def test_deactivate_and_activate_sensor(
        self, client: TestClient, auth_headers_admin: dict, sensor: SensorCatalog
    ):
        """Desactivar y reactivar un sensor."""
        response = client.patch(
            f"/api/v1/sensors/{sensor.id}/deactivate", headers=auth_headers_admin
        )
        assert response.status_code == 200
        assert response.json()["is_active"] is False

        response = client.patch(
            f"/api/v1/sensors/{sensor.id}/activate", headers=auth_headers_admin
        )
        assert response.status_code == 200
        assert response.json()["is_active"] is True

    def test_delete_sensor_as_admin(
        self, client: TestClient, auth_headers_admin: dict, sensor: SensorCatalog
    ):
        """Super admin puede eliminar un sensor."""
        response = client.delete(
            f"/api/v1/sensors/{sensor.id}", headers=auth_headers_admin
        )
        assert response.status_code == 204

    def test_delete_sensor_as_technician_forbidden(
        self, client: TestClient, auth_headers_technician: dict, sensor: SensorCatalog
    ):
        """Technician NO puede eliminar sensores (403)."""
        response = client.delete(
            f"/api/v1/sensors/{sensor.id}", headers=auth_headers_technician
        )
        assert response.status_code == 403
