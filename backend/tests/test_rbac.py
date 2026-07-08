"""
Tests del sistema RBAC (Role-Based Access Control).

Verifica que los permisos se apliquen correctamente en todos los endpoints.
"""

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.models.user import User
from app.models.location import LocationGroup, Location
from app.models.asset import Asset
from app.models.device import Device
from app.models.sensor_reading import SensorReading
from app.core.security import hash_password


# ============================================
# Fixtures
# ============================================

@pytest.fixture
def super_admin_user(db: Session) -> User:
    """Usuario con rol super_admin (ve todo)."""
    user = User(
        email="superadmin@test.com",
        password_hash=hash_password("password123"),
        role="super_admin",
        first_name="Super",
        last_name="Admin",
        is_active=True
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


@pytest.fixture
def service_admin_user(db: Session, test_location: Location) -> User:
    """Usuario service_admin con acceso a una location específica."""
    user = User(
        email="serviceadmin@test.com",
        password_hash=hash_password("password123"),
        role="service_admin",
        first_name="Service",
        last_name="Admin",
        is_active=True,
        allowed_location_ids=[test_location.id]
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


@pytest.fixture
def technician_user(db: Session, test_location: Location) -> User:
    """Usuario técnico con acceso a una location específica."""
    user = User(
        email="technician@test.com",
        password_hash=hash_password("password123"),
        role="technician",
        first_name="Tech",
        last_name="User",
        is_active=True,
        allowed_location_ids=[test_location.id]
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


@pytest.fixture
def guest_user(db: Session) -> User:
    """Usuario guest sin permisos (sin locations asignadas)."""
    user = User(
        email="guest@test.com",
        password_hash=hash_password("password123"),
        role="guest",
        first_name="Guest",
        last_name="User",
        is_active=True,
        allowed_location_ids=[]
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


@pytest.fixture
def test_location_group(db: Session) -> LocationGroup:
    """Location group para testing."""
    group = LocationGroup(
        name="Test Hospital",
        description="Hospital de pruebas"
    )
    db.add(group)
    db.commit()
    db.refresh(group)
    return group


@pytest.fixture
def test_location(db: Session, test_location_group: LocationGroup) -> Location:
    """Location para testing."""
    location = Location(
        location_group_id=test_location_group.id,
        name="Laboratorio Test",
        code="LAB-TEST"
    )
    db.add(location)
    db.commit()
    db.refresh(location)
    return location


@pytest.fixture
def second_location(db: Session, test_location_group: LocationGroup) -> Location:
    """Segunda location para testing de restricciones."""
    location = Location(
        location_group_id=test_location_group.id,
        name="Sala de Cirugía",
        code="CIRUGIA-01"
    )
    db.add(location)
    db.commit()
    db.refresh(location)
    return location


@pytest.fixture
def test_asset(db: Session, test_location: Location) -> Asset:
    """Asset para testing."""
    asset = Asset(
        location_id=test_location.id,
        name="Heladera Test",
        type="refrigerator"
    )
    db.add(asset)
    db.commit()
    db.refresh(asset)
    return asset


@pytest.fixture
def test_device(db: Session, test_asset: Asset) -> Device:
    """Device para testing."""
    device = Device(
        asset_id=test_asset.id,
        device_eui="TEST_DEVICE_001",
        name="ESP32 Test",
        status="active"
    )
    db.add(device)
    db.commit()
    db.refresh(device)
    return device


@pytest.fixture
def test_reading(db: Session, test_device: Device) -> SensorReading:
    """Reading para testing."""
    reading = SensorReading(
        device_id=test_device.id,
        data_payload={"temp_c": 25.5, "humidity_pct": 60.0},
        quality_score=0.95
    )
    db.add(reading)
    db.commit()
    db.refresh(reading)
    return reading


def get_auth_headers(client: TestClient, email: str, password: str) -> dict:
    """Helper para obtener headers de autenticación."""
    response = client.post(
        "/api/v1/auth/login",
        json={"email": email, "password": password}
    )
    assert response.status_code == 200
    token = response.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


# ============================================
# Tests: Listar Devices
# ============================================

def test_super_admin_can_see_all_devices(
    client: TestClient,
    db: Session,
    super_admin_user: User,
    test_device: Device
):
    """Super admin puede ver todos los devices."""
    headers = get_auth_headers(client, "superadmin@test.com", "password123")
    response = client.get("/api/v1/devices", headers=headers)

    assert response.status_code == 200
    devices = response.json()
    assert len(devices) >= 1
    assert any(d["id"] == test_device.id for d in devices)


def test_service_admin_sees_only_allowed_devices(
    client: TestClient,
    db: Session,
    service_admin_user: User,
    test_device: Device,
    second_location: Location
):
    """Service admin solo ve devices en sus locations permitidas."""
    # Crear device en location no permitida
    other_asset = Asset(
        location_id=second_location.id,
        name="Asset Prohibido",
        type="other"
    )
    db.add(other_asset)
    db.commit()

    other_device = Device(
        asset_id=other_asset.id,
        device_eui="FORBIDDEN_DEVICE",
        name="Device Prohibido",
        status="active"
    )
    db.add(other_device)
    db.commit()

    # Login y consultar devices
    headers = get_auth_headers(client, "serviceadmin@test.com", "password123")
    response = client.get("/api/v1/devices", headers=headers)

    assert response.status_code == 200
    devices = response.json()

    # Debe ver solo el device permitido
    device_ids = [d["id"] for d in devices]
    assert test_device.id in device_ids
    assert other_device.id not in device_ids


def test_technician_sees_only_allowed_devices(
    client: TestClient,
    db: Session,
    technician_user: User,
    test_device: Device
):
    """Técnico solo ve devices en sus locations permitidas."""
    headers = get_auth_headers(client, "technician@test.com", "password123")
    response = client.get("/api/v1/devices", headers=headers)

    assert response.status_code == 200
    devices = response.json()
    assert len(devices) >= 1
    assert devices[0]["id"] == test_device.id


def test_guest_without_locations_sees_no_devices(
    client: TestClient,
    db: Session,
    guest_user: User,
    test_device: Device
):
    """Guest sin locations asignadas no ve devices."""
    headers = get_auth_headers(client, "guest@test.com", "password123")
    response = client.get("/api/v1/devices", headers=headers)

    assert response.status_code == 200
    devices = response.json()
    assert len(devices) == 0


# ============================================
# Tests: Listar Readings
# ============================================

def test_super_admin_can_see_all_readings(
    client: TestClient,
    db: Session,
    super_admin_user: User,
    test_reading: SensorReading
):
    """Super admin puede ver todos los readings."""
    headers = get_auth_headers(client, "superadmin@test.com", "password123")
    response = client.get("/api/v1/readings", headers=headers)

    assert response.status_code == 200
    readings = response.json()
    assert len(readings) >= 1
    assert any(r["id"] == test_reading.id for r in readings)


def test_service_admin_sees_only_allowed_readings(
    client: TestClient,
    db: Session,
    service_admin_user: User,
    test_reading: SensorReading,
    second_location: Location
):
    """Service admin solo ve readings de devices en sus locations."""
    # Crear reading en location no permitida
    other_asset = Asset(
        location_id=second_location.id,
        name="Asset Prohibido",
        type="other"
    )
    db.add(other_asset)
    db.commit()

    other_device = Device(
        asset_id=other_asset.id,
        device_eui="FORBIDDEN_DEVICE_2",
        name="Device Prohibido 2",
        status="active"
    )
    db.add(other_device)
    db.commit()

    forbidden_reading = SensorReading(
        device_id=other_device.id,
        data_payload={"temp_c": 30.0},
        quality_score=0.9
    )
    db.add(forbidden_reading)
    db.commit()

    # Login y consultar readings
    headers = get_auth_headers(client, "serviceadmin@test.com", "password123")
    response = client.get("/api/v1/readings", headers=headers)

    assert response.status_code == 200
    readings = response.json()

    # Debe ver solo el reading permitido
    reading_ids = [r["id"] for r in readings]
    assert test_reading.id in reading_ids
    assert forbidden_reading.id not in reading_ids


def test_technician_cannot_access_forbidden_reading_by_id(
    client: TestClient,
    db: Session,
    technician_user: User,
    second_location: Location
):
    """Técnico no puede acceder a reading de device prohibido por ID."""
    # Crear reading en location no permitida
    other_asset = Asset(
        location_id=second_location.id,
        name="Asset Prohibido",
        type="other"
    )
    db.add(other_asset)
    db.commit()

    other_device = Device(
        asset_id=other_asset.id,
        device_eui="FORBIDDEN_DEVICE_3",
        name="Device Prohibido 3",
        status="active"
    )
    db.add(other_device)
    db.commit()

    forbidden_reading = SensorReading(
        device_id=other_device.id,
        data_payload={"temp_c": 35.0},
        quality_score=0.8
    )
    db.add(forbidden_reading)
    db.commit()

    # Intentar acceder al reading prohibido
    headers = get_auth_headers(client, "technician@test.com", "password123")
    response = client.get(f"/api/v1/readings/{forbidden_reading.id}", headers=headers)

    assert response.status_code == 403
    assert "No tienes acceso" in response.json()["detail"]


# ============================================
# Tests: Gestión de Devices (POST/PATCH/DELETE)
# ============================================

def test_technician_cannot_create_device(
    client: TestClient,
    db: Session,
    technician_user: User,
    test_asset: Asset
):
    """Técnico no puede crear devices (requiere service_admin o super_admin)."""
    headers = get_auth_headers(client, "technician@test.com", "password123")
    response = client.post(
        "/api/v1/devices",
        headers=headers,
        json={
            "asset_id": test_asset.id,
            "device_eui": "NEW_DEVICE_001",
            "name": "Nuevo Device",
            "status": "active"
        }
    )

    # Debe ser rechazado (403 Forbidden)
    assert response.status_code == 403


def test_service_admin_can_create_device(
    client: TestClient,
    db: Session,
    service_admin_user: User,
    test_asset: Asset
):
    """Service admin puede crear devices en sus locations."""
    headers = get_auth_headers(client, "serviceadmin@test.com", "password123")
    response = client.post(
        "/api/v1/devices",
        headers=headers,
        json={
            "asset_id": test_asset.id,
            "device_eui": "NEW_DEVICE_002",
            "name": "Nuevo Device Admin",
            "status": "active"
        }
    )

    assert response.status_code == 201
    device = response.json()
    assert device["name"] == "Nuevo Device Admin"


# ============================================
# Tests: Filtrado de Locations
# ============================================

def test_super_admin_sees_all_locations(
    client: TestClient,
    db: Session,
    super_admin_user: User,
    test_location: Location,
    second_location: Location
):
    """Super admin ve todas las locations."""
    headers = get_auth_headers(client, "superadmin@test.com", "password123")
    response = client.get("/api/v1/locations", headers=headers)

    assert response.status_code == 200
    locations = response.json()
    location_ids = [loc["id"] for loc in locations]

    assert test_location.id in location_ids
    assert second_location.id in location_ids


def test_service_admin_sees_only_allowed_locations(
    client: TestClient,
    db: Session,
    service_admin_user: User,
    test_location: Location,
    second_location: Location
):
    """Service admin solo ve sus locations permitidas."""
    headers = get_auth_headers(client, "serviceadmin@test.com", "password123")
    response = client.get("/api/v1/locations", headers=headers)

    assert response.status_code == 200
    locations = response.json()
    location_ids = [loc["id"] for loc in locations]

    assert test_location.id in location_ids
    assert second_location.id not in location_ids
