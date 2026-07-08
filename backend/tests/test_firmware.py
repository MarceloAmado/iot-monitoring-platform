"""
Tests para endpoints de Firmware OTA.

Cubre:
- Upload de firmware (admin)
- Listado de versiones
- Check de última versión (device API key)
- Actualización de metadata
- Eliminación de firmware
"""

import io
import os
import pytest
from unittest.mock import patch, MagicMock
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.models.firmware import Firmware
from app.models.device import Device
from app.models.user import User


# ============================================
# FIXTURES
# ============================================

DEVICE_API_KEY = "test_firmware_api_key_123"


@pytest.fixture
def device_with_api_key(db_session: Session, asset) -> Device:
    """Device con API key para tests de firmware OTA."""
    device_obj = Device(
        asset_id=asset.id,
        device_eui="ESP32_FW_001",
        name="ESP32 Firmware Test",
        status="active",
        api_key=DEVICE_API_KEY,
        firmware_version="1.0.0",
        config={},
        extra_data={}
    )
    db_session.add(device_obj)
    db_session.commit()
    db_session.refresh(device_obj)
    return device_obj


@pytest.fixture
def device_headers(device_with_api_key: Device) -> dict:
    """Headers de autenticación por API Key para device."""
    return {
        "X-API-Key": DEVICE_API_KEY,
        "X-Device-EUI": device_with_api_key.device_eui,
    }


@pytest.fixture
def firmware_v1(db_session: Session, super_admin_user: User) -> Firmware:
    """Firmware v1.0.0 en BD."""
    fw = Firmware(
        version="1.0.0",
        file_path="firmware/esp32_v1_0_0.bin",
        file_size_bytes=524288,
        md5_checksum="a" * 32,
        release_notes="Initial release",
        is_stable=True,
        is_latest=False,
        min_compatible_version=None,
        created_by_user_id=super_admin_user.id,
    )
    db_session.add(fw)
    db_session.commit()
    db_session.refresh(fw)
    return fw


@pytest.fixture
def firmware_v2(db_session: Session, super_admin_user: User) -> Firmware:
    """Firmware v2.0.0 marcado como latest."""
    fw = Firmware(
        version="2.0.0",
        file_path="firmware/esp32_v2_0_0.bin",
        file_size_bytes=1048576,
        md5_checksum="b" * 32,
        release_notes="Major update with new features",
        is_stable=True,
        is_latest=True,
        min_compatible_version="1.0.0",
        created_by_user_id=super_admin_user.id,
    )
    db_session.add(fw)
    db_session.commit()
    db_session.refresh(fw)
    return fw


@pytest.fixture
def firmware_beta(db_session: Session, super_admin_user: User) -> Firmware:
    """Firmware v3.0.0-beta (no estable)."""
    fw = Firmware(
        version="3.0.0-beta",
        file_path="firmware/esp32_v3_0_0_beta.bin",
        file_size_bytes=1572864,
        md5_checksum="c" * 32,
        release_notes="Beta with experimental features",
        is_stable=False,
        is_latest=False,
        min_compatible_version="2.0.0",
        created_by_user_id=super_admin_user.id,
    )
    db_session.add(fw)
    db_session.commit()
    db_session.refresh(fw)
    return fw


# ============================================
# TEST: LIST VERSIONS
# ============================================


class TestListFirmware:
    """Tests para GET /api/v1/firmware/versions."""

    def test_list_all_versions(
        self, client: TestClient, auth_headers_admin: dict,
        firmware_v1: Firmware, firmware_v2: Firmware, firmware_beta: Firmware
    ):
        """Listar todas las versiones de firmware."""
        response = client.get("/api/v1/firmware/versions", headers=auth_headers_admin)
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 3
        # Ordenadas por created_at DESC
        versions = [fw["version"] for fw in data]
        assert "1.0.0" in versions
        assert "2.0.0" in versions
        assert "3.0.0-beta" in versions

    def test_list_only_stable(
        self, client: TestClient, auth_headers_admin: dict,
        firmware_v1: Firmware, firmware_v2: Firmware, firmware_beta: Firmware
    ):
        """Filtrar solo versiones estables."""
        response = client.get(
            "/api/v1/firmware/versions",
            params={"only_stable": True},
            headers=auth_headers_admin
        )
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 2
        for fw in data:
            assert fw["is_stable"] is True

    def test_list_empty(self, client: TestClient, auth_headers_admin: dict):
        """Listar cuando no hay firmware."""
        response = client.get("/api/v1/firmware/versions", headers=auth_headers_admin)
        assert response.status_code == 200
        assert response.json() == []

    def test_list_unauthorized(self, client: TestClient):
        """No se puede listar sin autenticación."""
        response = client.get("/api/v1/firmware/versions")
        assert response.status_code in [401, 403]


# ============================================
# TEST: UPLOAD FIRMWARE
# ============================================


class TestUploadFirmware:
    """Tests para POST /api/v1/firmware/upload."""

    def test_upload_success(self, client: TestClient, auth_headers_admin: dict):
        """Subir firmware correctamente."""
        bin_content = b"\x00\x01\x02\x03" * 1024  # 4KB fake binary
        response = client.post(
            "/api/v1/firmware/upload",
            headers=auth_headers_admin,
            data={
                "version": "1.0.0",
                "release_notes": "First release",
                "is_stable": "true",
            },
            files={"file": ("firmware.bin", io.BytesIO(bin_content), "application/octet-stream")},
        )
        assert response.status_code == 201
        data = response.json()
        assert data["version"] == "1.0.0"
        assert data["is_stable"] is True
        assert data["release_notes"] == "First release"
        assert data["file_size_bytes"] == len(bin_content)
        assert len(data["md5_checksum"]) == 32
        # First firmware should be marked latest
        assert data["is_latest"] is True

    def test_upload_duplicate_version(
        self, client: TestClient, auth_headers_admin: dict, firmware_v1: Firmware
    ):
        """No se puede subir versión duplicada."""
        bin_content = b"\x00" * 1024
        response = client.post(
            "/api/v1/firmware/upload",
            headers=auth_headers_admin,
            data={"version": "1.0.0"},
            files={"file": ("firmware.bin", io.BytesIO(bin_content), "application/octet-stream")},
        )
        assert response.status_code == 400
        assert "ya existe" in response.json()["detail"]

    def test_upload_invalid_extension(self, client: TestClient, auth_headers_admin: dict):
        """No se puede subir archivo que no sea .bin."""
        response = client.post(
            "/api/v1/firmware/upload",
            headers=auth_headers_admin,
            data={"version": "1.0.0"},
            files={"file": ("firmware.hex", io.BytesIO(b"\x00"), "application/octet-stream")},
        )
        assert response.status_code == 400
        assert ".bin" in response.json()["detail"]

    def test_upload_non_admin_forbidden(
        self, client: TestClient, auth_headers_technician: dict
    ):
        """Technician no puede subir firmware."""
        bin_content = b"\x00" * 1024
        response = client.post(
            "/api/v1/firmware/upload",
            headers=auth_headers_technician,
            data={"version": "1.0.0"},
            files={"file": ("firmware.bin", io.BytesIO(bin_content), "application/octet-stream")},
        )
        assert response.status_code == 403

    def test_upload_with_min_compatible_version(
        self, client: TestClient, auth_headers_admin: dict
    ):
        """Subir firmware con versión mínima compatible."""
        bin_content = b"\x00" * 1024
        response = client.post(
            "/api/v1/firmware/upload",
            headers=auth_headers_admin,
            data={
                "version": "2.0.0",
                "min_compatible_version": "1.5.0",
                "is_stable": "true",
            },
            files={"file": ("firmware.bin", io.BytesIO(bin_content), "application/octet-stream")},
        )
        assert response.status_code == 201
        data = response.json()
        assert data["min_compatible_version"] == "1.5.0"


# ============================================
# TEST: GET LATEST (DEVICE OTA CHECK)
# ============================================


class TestGetLatestFirmware:
    """Tests para GET /api/v1/firmware/latest."""

    def test_update_available(
        self, client: TestClient, device_headers: dict,
        firmware_v1: Firmware, firmware_v2: Firmware
    ):
        """ESP32 con versión antigua recibe info de update."""
        response = client.get(
            "/api/v1/firmware/latest",
            params={"current_version": "1.0.0"},
            headers=device_headers,
        )
        assert response.status_code == 200
        data = response.json()
        assert data["update_available"] is True
        assert data["latest_version"] == "2.0.0"
        assert data["current_version"] == "1.0.0"
        assert data["is_compatible"] is True
        assert data["download_url"] is not None
        assert "2.0.0" in data["download_url"]

    def test_already_latest(
        self, client: TestClient, device_headers: dict,
        firmware_v2: Firmware
    ):
        """ESP32 ya con la última versión."""
        response = client.get(
            "/api/v1/firmware/latest",
            params={"current_version": "2.0.0"},
            headers=device_headers,
        )
        assert response.status_code == 200
        data = response.json()
        assert data["update_available"] is False
        assert data["download_url"] is None
        assert "más reciente" in data["message"]

    def test_incompatible_version(
        self, client: TestClient, device_headers: dict, db_session: Session,
        super_admin_user: User
    ):
        """ESP32 con versión demasiado antigua no puede actualizar."""
        # Crear firmware que requiere mínimo 1.5.0
        fw = Firmware(
            version="3.0.0",
            file_path="firmware/esp32_v3_0_0.bin",
            file_size_bytes=1048576,
            md5_checksum="d" * 32,
            is_stable=True,
            is_latest=True,
            min_compatible_version="1.5.0",
            created_by_user_id=super_admin_user.id,
        )
        db_session.add(fw)
        db_session.commit()

        response = client.get(
            "/api/v1/firmware/latest",
            params={"current_version": "1.0.0"},
            headers=device_headers,
        )
        assert response.status_code == 200
        data = response.json()
        assert data["update_available"] is True
        assert data["is_compatible"] is False
        assert data["download_url"] is None
        assert "no compatible" in data["message"].lower()

    def test_no_firmware_available(self, client: TestClient, device_headers: dict):
        """No hay firmware disponible."""
        response = client.get(
            "/api/v1/firmware/latest",
            params={"current_version": "1.0.0"},
            headers=device_headers,
        )
        assert response.status_code == 404

    def test_without_device_auth(self, client: TestClient):
        """No se puede consultar sin API Key."""
        response = client.get(
            "/api/v1/firmware/latest",
            params={"current_version": "1.0.0"},
        )
        assert response.status_code in [401, 403, 422]


# ============================================
# TEST: UPDATE METADATA
# ============================================


class TestUpdateFirmware:
    """Tests para PATCH /api/v1/firmware/{firmware_id}."""

    def test_update_release_notes(
        self, client: TestClient, auth_headers_admin: dict, firmware_v1: Firmware
    ):
        """Actualizar notas de release."""
        response = client.patch(
            f"/api/v1/firmware/{firmware_v1.id}",
            headers=auth_headers_admin,
            json={"release_notes": "Updated release notes"},
        )
        assert response.status_code == 200
        assert response.json()["release_notes"] == "Updated release notes"

    def test_mark_as_latest(
        self, client: TestClient, auth_headers_admin: dict,
        firmware_v1: Firmware, firmware_v2: Firmware, db_session: Session
    ):
        """Marcar una versión como latest desmarca las demás."""
        response = client.patch(
            f"/api/v1/firmware/{firmware_v1.id}",
            headers=auth_headers_admin,
            json={"is_latest": True},
        )
        assert response.status_code == 200
        assert response.json()["is_latest"] is True

        # Verificar que v2 ya no es latest
        db_session.refresh(firmware_v2)
        assert firmware_v2.is_latest is False

    def test_update_stability(
        self, client: TestClient, auth_headers_admin: dict, firmware_beta: Firmware
    ):
        """Cambiar beta a estable."""
        response = client.patch(
            f"/api/v1/firmware/{firmware_beta.id}",
            headers=auth_headers_admin,
            json={"is_stable": True},
        )
        assert response.status_code == 200
        assert response.json()["is_stable"] is True

    def test_update_not_found(self, client: TestClient, auth_headers_admin: dict):
        """Actualizar firmware que no existe."""
        response = client.patch(
            "/api/v1/firmware/99999",
            headers=auth_headers_admin,
            json={"release_notes": "test"},
        )
        assert response.status_code == 404

    def test_update_non_admin_forbidden(
        self, client: TestClient, auth_headers_technician: dict, firmware_v1: Firmware
    ):
        """Technician no puede actualizar firmware."""
        response = client.patch(
            f"/api/v1/firmware/{firmware_v1.id}",
            headers=auth_headers_technician,
            json={"release_notes": "hacked"},
        )
        assert response.status_code == 403


# ============================================
# TEST: DELETE FIRMWARE
# ============================================


class TestDeleteFirmware:
    """Tests para DELETE /api/v1/firmware/{firmware_id}."""

    def test_delete_success(
        self, client: TestClient, auth_headers_admin: dict, firmware_v1: Firmware
    ):
        """Eliminar firmware correctamente."""
        response = client.delete(
            f"/api/v1/firmware/{firmware_v1.id}",
            headers=auth_headers_admin,
        )
        assert response.status_code == 204

        # Verificar que no existe más
        response = client.get("/api/v1/firmware/versions", headers=auth_headers_admin)
        versions = [fw["version"] for fw in response.json()]
        assert "1.0.0" not in versions

    def test_delete_not_found(self, client: TestClient, auth_headers_admin: dict):
        """Eliminar firmware que no existe."""
        response = client.delete(
            "/api/v1/firmware/99999",
            headers=auth_headers_admin,
        )
        assert response.status_code == 404

    def test_delete_non_admin_forbidden(
        self, client: TestClient, auth_headers_technician: dict, firmware_v1: Firmware
    ):
        """Technician no puede eliminar firmware."""
        response = client.delete(
            f"/api/v1/firmware/{firmware_v1.id}",
            headers=auth_headers_technician,
        )
        assert response.status_code == 403
