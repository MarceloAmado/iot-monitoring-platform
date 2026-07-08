"""
Configuracion de pytest - Fixtures globales.

Este archivo define fixtures reutilizables para todos los tests.
"""

import pytest
from typing import Generator
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import StaticPool

from app.core.database import Base, get_db
from app.core.security import hash_password
from app.main import app
from app.models.user import User
from app.models.location import LocationGroup, Location
from app.models.asset import Asset
from app.models.device import Device


# Database de prueba (PostgreSQL)
# Usa la misma DB de development pero con un schema diferente para tests
import os

SQLALCHEMY_TEST_DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql://iot_admin:change_me_in_production_123!"
    "@postgres:5432/iot_monitoring"
)

engine = create_engine(
    SQLALCHEMY_TEST_DATABASE_URL,
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


@pytest.fixture(scope="function")
def db_session() -> Generator[Session, None, None]:
    """
    Fixture que provee una sesion de DB para cada test.

    Crea las tablas antes del test y las limpia despues.
    """
    # Crear todas las tablas
    Base.metadata.create_all(bind=engine)

    session = TestingSessionLocal()
    try:
        yield session
    finally:
        session.close()
        # Limpiar todas las tablas
        Base.metadata.drop_all(bind=engine)


@pytest.fixture(scope="function")
def db(db_session: Session) -> Generator[Session, None, None]:
    """Alias de db_session para compatibilidad con test_rbac.py."""
    yield db_session


@pytest.fixture(scope="function")
def client(db_session: Session) -> Generator[TestClient, None, None]:
    """
    Fixture que provee un TestClient de FastAPI.

    Sobrescribe la dependencia get_db para usar la DB de prueba.
    """
    def override_get_db():
        try:
            yield db_session
        finally:
            pass

    app.dependency_overrides[get_db] = override_get_db

    with TestClient(app) as test_client:
        yield test_client

    app.dependency_overrides.clear()


@pytest.fixture(scope="function")
def super_admin_user(db_session: Session) -> User:
    """
    Fixture que crea un usuario Super Admin para tests.
    """
    user = User(
        email="admin@test.com",
        password_hash=hash_password("admin123"),
        role="super_admin",
        first_name="Test",
        last_name="Admin",
        is_active=True
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user


@pytest.fixture(scope="function")
def technician_user(db_session: Session) -> User:
    """
    Fixture que crea un usuario Technician para tests.
    """
    user = User(
        email="tech@test.com",
        password_hash=hash_password("tech123"),
        role="technician",
        first_name="Test",
        last_name="Technician",
        is_active=True,
        allowed_location_ids=[1]  # Solo puede ver location 1
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user


@pytest.fixture(scope="function")
def location_group(db_session: Session) -> LocationGroup:
    """
    Fixture que crea un LocationGroup para tests.
    """
    group = LocationGroup(
        name="Test Hospital",
        description="Hospital de prueba"
    )
    db_session.add(group)
    db_session.commit()
    db_session.refresh(group)
    return group


@pytest.fixture(scope="function")
def location(db_session: Session, location_group: LocationGroup) -> Location:
    """
    Fixture que crea una Location para tests.
    """
    loc = Location(
        location_group_id=location_group.id,
        name="Laboratorio Test",
        code="LAB-TEST"
    )
    db_session.add(loc)
    db_session.commit()
    db_session.refresh(loc)
    return loc


@pytest.fixture(scope="function")
def asset(db_session: Session, location: Location) -> Asset:
    """
    Fixture que crea un Asset para tests.
    """
    asset_obj = Asset(
        location_id=location.id,
        name="Heladera_Test_001",
        type="refrigerator",
        description="Heladera de prueba",
        extra_data={"capacidad": "500L", "marca": "Test"}
    )
    db_session.add(asset_obj)
    db_session.commit()
    db_session.refresh(asset_obj)
    return asset_obj


@pytest.fixture(scope="function")
def device(db_session: Session, asset: Asset) -> Device:
    """
    Fixture que crea un Device para tests.
    """
    device_obj = Device(
        asset_id=asset.id,
        device_eui="ESP32_TEST_001",
        name="ESP32 Test 001",
        status="active",
        firmware_version="v1.0.0",
        config={"sampling_interval_sec": 300},
        extra_data={"mac_address": "AA:BB:CC:DD:EE:FF"}
    )
    db_session.add(device_obj)
    db_session.commit()
    db_session.refresh(device_obj)
    return device_obj


@pytest.fixture(scope="function")
def auth_headers_admin(client: TestClient, super_admin_user: User) -> dict:
    """
    Fixture que retorna headers de autenticacion para Super Admin.
    """
    response = client.post(
        "/api/v1/auth/login",
        json={
            "email": "admin@test.com",
            "password": "admin123"
        }
    )
    assert response.status_code == 200
    token = response.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture(scope="function")
def auth_headers_technician(client: TestClient, technician_user: User) -> dict:
    """
    Fixture que retorna headers de autenticacion para Technician.
    """
    response = client.post(
        "/api/v1/auth/login",
        json={
            "email": "tech@test.com",
            "password": "tech123"
        }
    )
    assert response.status_code == 200
    token = response.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}
