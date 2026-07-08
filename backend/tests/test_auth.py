"""
Tests para endpoints de autenticacion (POST /login, GET /me).
"""

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.models.user import User


class TestLogin:
    """Tests para POST /api/v1/auth/login"""

    def test_login_success(self, client: TestClient, super_admin_user: User):
        """Test de login exitoso con credenciales validas."""
        response = client.post(
            "/api/v1/auth/login",
            json={
                "email": "admin@test.com",
                "password": "admin123"
            }
        )

        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert data["token_type"] == "bearer"
        assert isinstance(data["access_token"], str)
        assert len(data["access_token"]) > 0

    def test_login_invalid_email(self, client: TestClient, super_admin_user: User):
        """Test de login con email incorrecto."""
        response = client.post(
            "/api/v1/auth/login",
            json={
                "email": "wrong@test.com",
                "password": "admin123"
            }
        )

        assert response.status_code == 401
        assert "detail" in response.json()

    def test_login_invalid_password(self, client: TestClient, super_admin_user: User):
        """Test de login con contrasena incorrecta."""
        response = client.post(
            "/api/v1/auth/login",
            json={
                "email": "admin@test.com",
                "password": "wrongpassword"
            }
        )

        assert response.status_code == 401
        assert "detail" in response.json()

    def test_login_inactive_user(self, client: TestClient, db_session: Session):
        """Test de login con usuario inactivo."""
        from app.core.security import hash_password

        # Crear usuario inactivo
        inactive_user = User(
            email="inactive@test.com",
            password_hash=hash_password("test123"),
            role="guest",
            first_name="Inactive",
            last_name="User",
            is_active=False
        )
        db_session.add(inactive_user)
        db_session.commit()

        response = client.post(
            "/api/v1/auth/login",
            json={
                "email": "inactive@test.com",
                "password": "test123"
            }
        )

        assert response.status_code == 400
        assert "inactivo" in response.json()["detail"].lower()

    def test_login_missing_fields(self, client: TestClient):
        """Test de login con campos faltantes."""
        response = client.post(
            "/api/v1/auth/login",
            json={"email": "admin@test.com"}
        )

        assert response.status_code == 422  # Validation error

    def test_login_invalid_email_format(self, client: TestClient):
        """Test de login con formato de email invalido."""
        response = client.post(
            "/api/v1/auth/login",
            json={
                "email": "not-an-email",
                "password": "test123"
            }
        )

        assert response.status_code == 422  # Validation error


class TestGetCurrentUser:
    """Tests para GET /api/v1/auth/me"""

    def test_get_current_user_success(
        self,
        client: TestClient,
        auth_headers_admin: dict,
        super_admin_user: User
    ):
        """Test de obtener usuario actual con token valido."""
        response = client.get("/api/v1/auth/me", headers=auth_headers_admin)

        assert response.status_code == 200
        data = response.json()
        assert data["email"] == "admin@test.com"
        assert data["role"] == "super_admin"
        assert data["first_name"] == "Test"
        assert data["last_name"] == "Admin"
        assert data["is_active"] is True
        assert "password_hash" not in data  # No debe exponer el hash

    def test_get_current_user_no_token(self, client: TestClient):
        """Test de obtener usuario actual sin token."""
        response = client.get("/api/v1/auth/me")

        assert response.status_code == 403  # Forbidden

    def test_get_current_user_invalid_token(self, client: TestClient):
        """Test de obtener usuario actual con token invalido."""
        response = client.get(
            "/api/v1/auth/me",
            headers={"Authorization": "Bearer invalid_token_xyz"}
        )

        assert response.status_code == 401  # Unauthorized

    def test_get_current_user_expired_token(self, client: TestClient):
        """Test de obtener usuario actual con token expirado."""
        from app.core.security import create_access_token
        from datetime import timedelta

        # Crear token que ya expiro (expires_delta negativo)
        expired_token = create_access_token(
            data={"sub": "admin@test.com", "user_id": 1},
            expires_delta=timedelta(minutes=-10)
        )

        response = client.get(
            "/api/v1/auth/me",
            headers={"Authorization": f"Bearer {expired_token}"}
        )

        assert response.status_code == 401  # Unauthorized


class TestRoleBasedAccess:
    """Tests de control de acceso basado en roles."""

    def test_technician_can_login(
        self,
        client: TestClient,
        technician_user: User
    ):
        """Test de que un technician puede hacer login."""
        response = client.post(
            "/api/v1/auth/login",
            json={
                "email": "tech@test.com",
                "password": "tech123"
            }
        )

        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data

    def test_technician_get_profile(
        self,
        client: TestClient,
        auth_headers_technician: dict,
        technician_user: User
    ):
        """Test de que un technician puede obtener su perfil."""
        response = client.get("/api/v1/auth/me", headers=auth_headers_technician)

        assert response.status_code == 200
        data = response.json()
        assert data["email"] == "tech@test.com"
        assert data["role"] == "technician"
        assert data["allowed_location_ids"] == [1]


class TestTokenStructure:
    """Tests de estructura del token JWT."""

    def test_token_contains_correct_claims(
        self,
        client: TestClient,
        super_admin_user: User
    ):
        """Test de que el token contiene los claims correctos."""
        from app.core.security import decode_access_token

        # Login
        response = client.post(
            "/api/v1/auth/login",
            json={
                "email": "admin@test.com",
                "password": "admin123"
            }
        )

        token = response.json()["access_token"]

        # Decodificar token
        token_data = decode_access_token(token)

        assert token_data is not None
        assert token_data.get("sub") == "admin@test.com"
        assert token_data.get("user_id") == super_admin_user.id

    def test_multiple_logins_generate_different_tokens(
        self,
        client: TestClient,
        super_admin_user: User
    ):
        """Test de que multiples logins generan tokens diferentes (por iat timestamp)."""
        import time

        # Primer login
        response1 = client.post(
            "/api/v1/auth/login",
            json={
                "email": "admin@test.com",
                "password": "admin123"
            }
        )
        token1 = response1.json()["access_token"]

        # Esperar 1 segundo para que el timestamp cambie
        time.sleep(1)

        # Segundo login
        response2 = client.post(
            "/api/v1/auth/login",
            json={
                "email": "admin@test.com",
                "password": "admin123"
            }
        )
        token2 = response2.json()["access_token"]

        assert token1 != token2  # Los tokens deben ser diferentes
