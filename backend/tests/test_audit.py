"""
Tests para endpoints de Audit Log (/api/v1/audit).

RBAC:
- Listar/detalle/summary by-action: super_admin y service_admin
- Summary by-user: solo super_admin
- /me/activity: cualquier usuario autenticado
"""

from fastapi.testclient import TestClient


def _create_audited_action(client: TestClient, auth_headers_admin: dict) -> None:
    """Genera al menos un registro de auditoría creando un location group."""
    response = client.post(
        "/api/v1/location-groups",
        json={"name": "Grupo Auditado", "description": "genera audit log"},
        headers=auth_headers_admin,
    )
    assert response.status_code == 201


class TestListAuditLogs:
    """Tests para GET /api/v1/audit/"""

    def test_list_audit_logs_as_admin(
        self, client: TestClient, auth_headers_admin: dict
    ):
        """Super admin puede listar el audit log y ve acciones registradas."""
        _create_audited_action(client, auth_headers_admin)

        response = client.get("/api/v1/audit/", headers=auth_headers_admin)

        assert response.status_code == 200
        data = response.json()
        assert "items" in data
        assert "total" in data
        assert data["total"] >= 1

    def test_list_audit_logs_pagination_fields(
        self, client: TestClient, auth_headers_admin: dict
    ):
        """La respuesta incluye los campos de paginación."""
        response = client.get(
            "/api/v1/audit/?page=1&page_size=10", headers=auth_headers_admin
        )

        assert response.status_code == 200
        data = response.json()
        assert data["page"] == 1
        assert data["page_size"] == 10
        assert "total_pages" in data

    def test_list_audit_logs_as_technician_forbidden(
        self, client: TestClient, auth_headers_technician: dict
    ):
        """Technician NO puede ver el audit log global (403)."""
        response = client.get("/api/v1/audit/", headers=auth_headers_technician)
        assert response.status_code == 403

    def test_list_audit_logs_unauthorized(self, client: TestClient):
        """Audit log sin token retorna 403."""
        response = client.get("/api/v1/audit/")
        assert response.status_code == 403


class TestAuditDetail:
    """Tests para GET /api/v1/audit/{id}"""

    def test_get_audit_log_by_id(self, client: TestClient, auth_headers_admin: dict):
        """Obtener un registro de auditoría por ID."""
        _create_audited_action(client, auth_headers_admin)

        listing = client.get("/api/v1/audit/", headers=auth_headers_admin).json()
        first_id = listing["items"][0]["id"]

        response = client.get(f"/api/v1/audit/{first_id}", headers=auth_headers_admin)

        assert response.status_code == 200
        assert response.json()["id"] == first_id

    def test_get_audit_log_not_found(self, client: TestClient, auth_headers_admin: dict):
        """Registro inexistente retorna 404."""
        response = client.get("/api/v1/audit/999999", headers=auth_headers_admin)
        assert response.status_code == 404


class TestAuditSummaries:
    """Tests para los endpoints de resumen"""

    def test_summary_by_action(self, client: TestClient, auth_headers_admin: dict):
        """Resumen por tipo de acción."""
        _create_audited_action(client, auth_headers_admin)

        response = client.get(
            "/api/v1/audit/summary/by-action", headers=auth_headers_admin
        )

        assert response.status_code == 200
        assert isinstance(response.json(), list)

    def test_summary_by_user_as_admin(self, client: TestClient, auth_headers_admin: dict):
        """Resumen por usuario (solo super_admin)."""
        _create_audited_action(client, auth_headers_admin)

        response = client.get(
            "/api/v1/audit/summary/by-user", headers=auth_headers_admin
        )

        assert response.status_code == 200
        assert isinstance(response.json(), list)

    def test_summary_by_user_as_technician_forbidden(
        self, client: TestClient, auth_headers_technician: dict
    ):
        """Technician NO puede ver el resumen por usuario (403)."""
        response = client.get(
            "/api/v1/audit/summary/by-user", headers=auth_headers_technician
        )
        assert response.status_code == 403


class TestMyActivity:
    """Tests para GET /api/v1/audit/me/activity"""

    def test_my_activity_any_user(
        self, client: TestClient, auth_headers_technician: dict
    ):
        """Cualquier usuario autenticado puede ver su propia actividad."""
        response = client.get(
            "/api/v1/audit/me/activity", headers=auth_headers_technician
        )

        assert response.status_code == 200
        data = response.json()
        assert "items" in data
        assert "total" in data
