"""
Tests para endpoints de Location Groups y Locations.

RBAC:
- Listar/leer: cualquier usuario autenticado (con scoping por location)
- Crear/actualizar: super_admin y service_admin
- Eliminar: solo super_admin
"""

from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.models.location import LocationGroup, Location


# ============================================================
# TESTS: Location Groups
# ============================================================

class TestLocationGroups:
    """Tests para /api/v1/location-groups"""

    def test_list_groups(
        self, client: TestClient, auth_headers_admin: dict, location_group: LocationGroup
    ):
        """Listar grupos retorna los existentes."""
        response = client.get("/api/v1/location-groups", headers=auth_headers_admin)

        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert any(g["name"] == "Test Hospital" for g in data)

    def test_list_groups_unauthorized(self, client: TestClient):
        """Listar grupos sin token retorna 403."""
        response = client.get("/api/v1/location-groups")
        assert response.status_code == 403

    def test_create_group_as_admin(self, client: TestClient, auth_headers_admin: dict):
        """Super admin puede crear un grupo."""
        response = client.post(
            "/api/v1/location-groups",
            json={"name": "Clinica Nueva", "description": "Grupo de prueba"},
            headers=auth_headers_admin,
        )

        assert response.status_code == 201
        data = response.json()
        assert data["name"] == "Clinica Nueva"
        assert data["id"] > 0

    def test_create_group_as_technician_forbidden(
        self, client: TestClient, auth_headers_technician: dict
    ):
        """Technician NO puede crear grupos (403)."""
        response = client.post(
            "/api/v1/location-groups",
            json={"name": "No deberia crearse"},
            headers=auth_headers_technician,
        )
        assert response.status_code == 403

    def test_get_group_by_id(
        self, client: TestClient, auth_headers_admin: dict, location_group: LocationGroup
    ):
        """Obtener grupo por ID."""
        response = client.get(
            f"/api/v1/location-groups/{location_group.id}", headers=auth_headers_admin
        )

        assert response.status_code == 200
        assert response.json()["name"] == "Test Hospital"

    def test_get_group_not_found(self, client: TestClient, auth_headers_admin: dict):
        """Grupo inexistente retorna 404."""
        response = client.get("/api/v1/location-groups/999999", headers=auth_headers_admin)
        assert response.status_code == 404

    def test_update_group(
        self, client: TestClient, auth_headers_admin: dict, location_group: LocationGroup
    ):
        """Actualizar nombre de un grupo."""
        response = client.patch(
            f"/api/v1/location-groups/{location_group.id}",
            json={"name": "Hospital Renombrado"},
            headers=auth_headers_admin,
        )

        assert response.status_code == 200
        assert response.json()["name"] == "Hospital Renombrado"

    def test_delete_group_as_admin(
        self, client: TestClient, auth_headers_admin: dict, db_session: Session
    ):
        """Super admin puede eliminar un grupo sin locations."""
        group = LocationGroup(name="Grupo a borrar")
        db_session.add(group)
        db_session.commit()
        db_session.refresh(group)

        response = client.delete(
            f"/api/v1/location-groups/{group.id}", headers=auth_headers_admin
        )
        assert response.status_code == 204

    def test_delete_group_as_technician_forbidden(
        self, client: TestClient, auth_headers_technician: dict, location_group: LocationGroup
    ):
        """Technician NO puede eliminar grupos (403)."""
        response = client.delete(
            f"/api/v1/location-groups/{location_group.id}",
            headers=auth_headers_technician,
        )
        assert response.status_code == 403


# ============================================================
# TESTS: Locations
# ============================================================

class TestLocations:
    """Tests para /api/v1/locations"""

    def test_list_locations(
        self, client: TestClient, auth_headers_admin: dict, location: Location
    ):
        """Listar locations retorna las existentes."""
        response = client.get("/api/v1/locations", headers=auth_headers_admin)

        assert response.status_code == 200
        data = response.json()
        assert any(loc["code"] == "LAB-TEST" for loc in data)

    def test_list_locations_filter_by_group(
        self,
        client: TestClient,
        auth_headers_admin: dict,
        location: Location,
        location_group: LocationGroup,
    ):
        """Filtrar locations por grupo."""
        response = client.get(
            f"/api/v1/locations?location_group_id={location_group.id}",
            headers=auth_headers_admin,
        )

        assert response.status_code == 200
        data = response.json()
        assert len(data) >= 1
        assert all(loc["location_group_id"] == location_group.id for loc in data)

    def test_create_location(
        self, client: TestClient, auth_headers_admin: dict, location_group: LocationGroup
    ):
        """Super admin puede crear una location."""
        response = client.post(
            "/api/v1/locations",
            json={
                "location_group_id": location_group.id,
                "name": "Deposito Nuevo",
                "code": "DEP-001",
                "address": "Calle Falsa 123",
            },
            headers=auth_headers_admin,
        )

        assert response.status_code == 201
        data = response.json()
        assert data["code"] == "DEP-001"

    def test_create_location_as_technician_forbidden(
        self, client: TestClient, auth_headers_technician: dict, location_group: LocationGroup
    ):
        """Technician NO puede crear locations (403)."""
        response = client.post(
            "/api/v1/locations",
            json={
                "location_group_id": location_group.id,
                "name": "No deberia crearse",
                "code": "NO-001",
            },
            headers=auth_headers_technician,
        )
        assert response.status_code == 403

    def test_get_location_by_id(
        self, client: TestClient, auth_headers_admin: dict, location: Location
    ):
        """Obtener location por ID."""
        response = client.get(
            f"/api/v1/locations/{location.id}", headers=auth_headers_admin
        )

        assert response.status_code == 200
        assert response.json()["name"] == "Laboratorio Test"

    def test_get_location_not_found(self, client: TestClient, auth_headers_admin: dict):
        """Location inexistente retorna 404."""
        response = client.get("/api/v1/locations/999999", headers=auth_headers_admin)
        assert response.status_code == 404

    def test_update_location(
        self, client: TestClient, auth_headers_admin: dict, location: Location
    ):
        """Actualizar una location."""
        response = client.patch(
            f"/api/v1/locations/{location.id}",
            json={"name": "Laboratorio Actualizado"},
            headers=auth_headers_admin,
        )

        assert response.status_code == 200
        assert response.json()["name"] == "Laboratorio Actualizado"

    def test_delete_location_as_technician_forbidden(
        self, client: TestClient, auth_headers_technician: dict, location: Location
    ):
        """Technician NO puede eliminar locations (403)."""
        response = client.delete(
            f"/api/v1/locations/{location.id}", headers=auth_headers_technician
        )
        assert response.status_code == 403
