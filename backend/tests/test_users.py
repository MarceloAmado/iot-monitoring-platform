"""
Tests para endpoints de Users (/api/v1/users).

RBAC: TODOS los endpoints de users son solo para super_admin.
"""

from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.models.user import User


class TestListUsers:
    """Tests para GET /api/v1/users"""

    def test_list_users_as_admin(
        self, client: TestClient, auth_headers_admin: dict, technician_user: User
    ):
        """Super admin puede listar usuarios."""
        response = client.get("/api/v1/users", headers=auth_headers_admin)

        assert response.status_code == 200
        emails = [u["email"] for u in response.json()]
        assert "admin@test.com" in emails
        assert "tech@test.com" in emails

    def test_list_users_as_technician_forbidden(
        self, client: TestClient, auth_headers_technician: dict
    ):
        """Technician NO puede listar usuarios (403)."""
        response = client.get("/api/v1/users", headers=auth_headers_technician)
        assert response.status_code == 403

    def test_list_users_unauthorized(self, client: TestClient):
        """Listar usuarios sin token retorna 403."""
        response = client.get("/api/v1/users")
        assert response.status_code == 403


class TestCreateUser:
    """Tests para POST /api/v1/users"""

    def test_create_user_as_admin(self, client: TestClient, auth_headers_admin: dict):
        """Super admin puede crear un usuario."""
        response = client.post(
            "/api/v1/users",
            json={
                "email": "nuevo@test.com",
                "password": "Password123!",
                "first_name": "Nuevo",
                "last_name": "Usuario",
                "role": "technician",
            },
            headers=auth_headers_admin,
        )

        assert response.status_code == 201
        data = response.json()
        assert data["email"] == "nuevo@test.com"
        assert data["role"] == "technician"
        assert "password_hash" not in data

    def test_create_user_duplicate_email(
        self, client: TestClient, auth_headers_admin: dict, technician_user: User
    ):
        """Crear usuario con email duplicado falla."""
        response = client.post(
            "/api/v1/users",
            json={
                "email": "tech@test.com",
                "password": "Password123!",
                "first_name": "Duplicado",
                "last_name": "Test",
                "role": "technician",
            },
            headers=auth_headers_admin,
        )
        assert response.status_code in (400, 409)

    def test_create_user_as_technician_forbidden(
        self, client: TestClient, auth_headers_technician: dict
    ):
        """Technician NO puede crear usuarios (403)."""
        response = client.post(
            "/api/v1/users",
            json={
                "email": "otro@test.com",
                "password": "Password123!",
                "first_name": "Otro",
                "last_name": "Usuario",
                "role": "guest",
            },
            headers=auth_headers_technician,
        )
        assert response.status_code == 403


class TestUserDetail:
    """Tests para GET/PATCH /api/v1/users/{id}"""

    def test_get_user_by_id(
        self, client: TestClient, auth_headers_admin: dict, technician_user: User
    ):
        """Obtener usuario por ID."""
        response = client.get(
            f"/api/v1/users/{technician_user.id}", headers=auth_headers_admin
        )

        assert response.status_code == 200
        assert response.json()["email"] == "tech@test.com"

    def test_get_user_not_found(self, client: TestClient, auth_headers_admin: dict):
        """Usuario inexistente retorna 404."""
        response = client.get("/api/v1/users/999999", headers=auth_headers_admin)
        assert response.status_code == 404

    def test_update_user(
        self, client: TestClient, auth_headers_admin: dict, technician_user: User
    ):
        """Actualizar datos de un usuario."""
        response = client.patch(
            f"/api/v1/users/{technician_user.id}",
            json={"first_name": "Renombrado"},
            headers=auth_headers_admin,
        )

        assert response.status_code == 200
        assert response.json()["first_name"] == "Renombrado"

    def test_update_allowed_location_ids(
        self, client: TestClient, auth_headers_admin: dict, technician_user: User
    ):
        """Actualizar las ubicaciones permitidas de un usuario."""
        response = client.patch(
            f"/api/v1/users/{technician_user.id}",
            json={"allowed_location_ids": [1, 2, 3]},
            headers=auth_headers_admin,
        )

        assert response.status_code == 200
        assert response.json()["allowed_location_ids"] == [1, 2, 3]


class TestUserLifecycle:
    """Tests para activate/deactivate/archive/reset-password"""

    def test_deactivate_and_activate_user(
        self, client: TestClient, auth_headers_admin: dict, technician_user: User
    ):
        """Desactivar y reactivar un usuario."""
        response = client.patch(
            f"/api/v1/users/{technician_user.id}/deactivate", headers=auth_headers_admin
        )
        assert response.status_code == 200
        assert response.json()["is_active"] is False

        response = client.patch(
            f"/api/v1/users/{technician_user.id}/activate", headers=auth_headers_admin
        )
        assert response.status_code == 200
        assert response.json()["is_active"] is True

    def test_archive_user(
        self, client: TestClient, auth_headers_admin: dict, technician_user: User
    ):
        """Archivar un usuario."""
        response = client.patch(
            f"/api/v1/users/{technician_user.id}/archive", headers=auth_headers_admin
        )
        assert response.status_code == 200
        assert response.json()["archived"] is True

    def test_reset_password_does_not_leak_password(
        self,
        client: TestClient,
        auth_headers_admin: dict,
        technician_user: User,
        db_session: Session,
    ):
        """El blanqueo de contraseña no debe exponerla salvo fallback dev sin SMTP."""
        response = client.post(
            f"/api/v1/users/{technician_user.id}/reset-password",
            headers=auth_headers_admin,
        )

        assert response.status_code == 200
        data = response.json()
        assert data["email"] == "tech@test.com"
        assert "email_sent" in data
        # Si el email salió, la contraseña NUNCA viaja en la respuesta
        if data["email_sent"]:
            assert "temp_password" not in data

    def test_reset_password_as_technician_forbidden(
        self, client: TestClient, auth_headers_technician: dict, super_admin_user: User
    ):
        """Technician NO puede blanquear contraseñas (403)."""
        response = client.post(
            f"/api/v1/users/{super_admin_user.id}/reset-password",
            headers=auth_headers_technician,
        )
        assert response.status_code == 403
