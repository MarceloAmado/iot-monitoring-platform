"""
Tests para endpoints de Assets (/api/v1/assets).

RBAC:
- Listar/leer: cualquier usuario autenticado (con scoping por location)
- Crear/actualizar: super_admin y service_admin
- Eliminar: solo super_admin
"""

from fastapi.testclient import TestClient

from app.models.asset import Asset
from app.models.location import Location


class TestListAssets:
    """Tests para GET /api/v1/assets"""

    def test_list_assets(self, client: TestClient, auth_headers_admin: dict, asset: Asset):
        """Listar assets retorna los existentes."""
        response = client.get("/api/v1/assets", headers=auth_headers_admin)

        assert response.status_code == 200
        data = response.json()
        assert any(a["name"] == "Heladera_Test_001" for a in data)

    def test_list_assets_filter_by_location(
        self, client: TestClient, auth_headers_admin: dict, asset: Asset, location: Location
    ):
        """Filtrar assets por location."""
        response = client.get(
            f"/api/v1/assets?location_id={location.id}", headers=auth_headers_admin
        )

        assert response.status_code == 200
        data = response.json()
        assert len(data) >= 1
        assert all(a["location_id"] == location.id for a in data)

    def test_list_assets_filter_by_type(
        self, client: TestClient, auth_headers_admin: dict, asset: Asset
    ):
        """Filtrar assets por tipo."""
        response = client.get(
            "/api/v1/assets?asset_type=refrigerator", headers=auth_headers_admin
        )

        assert response.status_code == 200
        assert all(a["type"] == "refrigerator" for a in response.json())

    def test_list_assets_unauthorized(self, client: TestClient):
        """Listar assets sin token retorna 403."""
        response = client.get("/api/v1/assets")
        assert response.status_code == 403


class TestCreateAsset:
    """Tests para POST /api/v1/assets"""

    def test_create_asset_as_admin(
        self, client: TestClient, auth_headers_admin: dict, location: Location
    ):
        """Super admin puede crear un asset."""
        response = client.post(
            "/api/v1/assets",
            json={
                "location_id": location.id,
                "name": "Freezer_Test_002",
                "type": "freezer",
                "description": "Freezer de prueba",
            },
            headers=auth_headers_admin,
        )

        assert response.status_code == 201
        data = response.json()
        assert data["name"] == "Freezer_Test_002"
        assert data["type"] == "freezer"

    def test_create_asset_as_technician_forbidden(
        self, client: TestClient, auth_headers_technician: dict, location: Location
    ):
        """Technician NO puede crear assets (403)."""
        response = client.post(
            "/api/v1/assets",
            json={"location_id": location.id, "name": "No", "type": "freezer"},
            headers=auth_headers_technician,
        )
        assert response.status_code == 403


class TestAssetDetail:
    """Tests para GET/PATCH/DELETE /api/v1/assets/{id}"""

    def test_get_asset_by_id(
        self, client: TestClient, auth_headers_admin: dict, asset: Asset
    ):
        """Obtener asset por ID."""
        response = client.get(f"/api/v1/assets/{asset.id}", headers=auth_headers_admin)

        assert response.status_code == 200
        assert response.json()["name"] == "Heladera_Test_001"

    def test_get_asset_not_found(self, client: TestClient, auth_headers_admin: dict):
        """Asset inexistente retorna 404."""
        response = client.get("/api/v1/assets/999999", headers=auth_headers_admin)
        assert response.status_code == 404

    def test_update_asset(self, client: TestClient, auth_headers_admin: dict, asset: Asset):
        """Actualizar un asset."""
        response = client.patch(
            f"/api/v1/assets/{asset.id}",
            json={"description": "Descripción actualizada"},
            headers=auth_headers_admin,
        )

        assert response.status_code == 200
        assert response.json()["description"] == "Descripción actualizada"

    def test_delete_asset_as_admin(
        self, client: TestClient, auth_headers_admin: dict, asset: Asset
    ):
        """Super admin puede eliminar un asset."""
        response = client.delete(f"/api/v1/assets/{asset.id}", headers=auth_headers_admin)
        assert response.status_code == 204

        # Verificar que ya no existe
        response = client.get(f"/api/v1/assets/{asset.id}", headers=auth_headers_admin)
        assert response.status_code == 404

    def test_delete_asset_as_technician_forbidden(
        self, client: TestClient, auth_headers_technician: dict, asset: Asset
    ):
        """Technician NO puede eliminar assets (403)."""
        response = client.delete(
            f"/api/v1/assets/{asset.id}", headers=auth_headers_technician
        )
        assert response.status_code == 403
