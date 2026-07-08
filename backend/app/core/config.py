"""
Sistema de Monitoreo IoT
Configuración Global de la Aplicación

Este módulo maneja todas las variables de entorno y configuraciones
usando Pydantic Settings para validación automática.
"""

from typing import List, Optional
from pydantic import field_validator, Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """
    Configuración global de la aplicación.

    Lee las variables de entorno del archivo .env y las valida.
    Utiliza Pydantic Settings para type-safety y validación automática.
    """

    # ============================================================
    # Información del Proyecto
    # ============================================================
    project_name: str = "IoT Monitoring System"
    version: str = "1.0.0"
    description: str = "Sistema de Monitoreo IoT Genérico y Escalable"
    api_v1_prefix: str = "/api/v1"

    # ============================================================
    # Entorno de Ejecución
    # ============================================================
    environment: str = "development"  # development | production
    debug: bool = True

    @field_validator("debug", mode="before")
    def set_debug_mode(cls, v: bool, info) -> bool:
        """Desactivar debug automáticamente en producción."""
        if info.data.get("environment") == "production":
            return False
        return v

    # ============================================================
    # Base de Datos PostgreSQL
    # ============================================================
    db_name: str
    db_user: str
    db_password: str
    db_host: str = "localhost"
    db_port: int = 5432

    @property
    def database_url(self) -> str:
        """
        Construye la URL de conexión a PostgreSQL.

        Returns:
            str: URL en formato postgresql://user:password@host:port/database
        """
        return (
            f"postgresql://{self.db_user}:{self.db_password}"
            f"@{self.db_host}:{self.db_port}/{self.db_name}"
        )

    # ============================================================
    # Redis (Cache y Sesiones)
    # ============================================================
    redis_host: str = "localhost"
    redis_port: int = 6379
    redis_db: int = 0

    @property
    def redis_url(self) -> str:
        """
        Construye la URL de conexión a Redis.

        Returns:
            str: URL en formato redis://host:port/db
        """
        return f"redis://{self.redis_host}:{self.redis_port}/{self.redis_db}"

    # ============================================================
    # Autenticación JWT
    # ============================================================
    jwt_secret_key: str
    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = 60

    @field_validator("jwt_secret_key")
    def validate_jwt_secret(cls, v: str) -> str:
        """Validar que la clave JWT sea suficientemente fuerte."""
        if len(v) < 32:
            raise ValueError(
                "JWT_SECRET_KEY debe tener al menos 32 caracteres. "
                "Generar con: openssl rand -hex 32"
            )
        return v

    # ============================================================
    # Encriptación de Datos Sensibles (Fernet)
    # ============================================================
    encryption_key: str

    @field_validator("encryption_key")
    def validate_encryption_key(cls, v: str) -> str:
        """
        Validar que la clave de encriptación sea válida para Fernet.

        La clave debe ser de 44 caracteres (32 bytes base64-encoded).
        Generar con: python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"
        """
        if len(v) != 44:
            raise ValueError(
                "ENCRYPTION_KEY debe tener exactamente 44 caracteres (32 bytes base64). "
                "Generar con: python -c \"from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())\""
            )
        # Intentar crear una instancia de Fernet para validar el formato
        try:
            from cryptography.fernet import Fernet
            Fernet(v.encode())
        except Exception as e:
            raise ValueError(f"ENCRYPTION_KEY inválida: {e}")
        return v

    # ============================================================
    # CORS (Cross-Origin Resource Sharing)
    # ============================================================
    cors_origins: str = "http://localhost:3000"

    @property
    def cors_origins_list(self) -> List[str]:
        """
        Convierte la string de origins separada por comas en una lista.

        Returns:
            List[str]: Lista de origins permitidos
        """
        return [origin.strip() for origin in self.cors_origins.split(",")]

    # ============================================================
    # Logging
    # ============================================================
    log_level: str = "INFO"  # DEBUG | INFO | WARNING | ERROR | CRITICAL

    # ============================================================
    # Seguridad de Devices
    # ============================================================
    device_api_key_salt: str

    # ============================================================
    # Notificaciones - Email (SMTP)
    # ============================================================
    smtp_enabled: bool = False
    smtp_host: Optional[str] = None
    smtp_port: Optional[int] = 587
    smtp_user: Optional[str] = None
    smtp_password: Optional[str] = None
    smtp_from_email: Optional[str] = None
    smtp_from_name: Optional[str] = None
    smtp_tls: bool = True  # Use TLS/STARTTLS

    # ============================================================
    # Notificaciones - Telegram
    # ============================================================
    telegram_enabled: bool = False
    telegram_bot_token: Optional[str] = None
    telegram_chat_id: Optional[str] = None

    # ============================================================
    # MQTT Broker (Mosquitto) - SCADA Fase 1.3/1.4
    # ============================================================
    mqtt_broker_host: str = Field(default="mosquitto")
    mqtt_broker_port: int = Field(default=1883)
    mqtt_broker_ws_port: int = Field(default=9001)
    mqtt_username: Optional[str] = Field(default=None)
    mqtt_password: Optional[str] = Field(default=None)
    mqtt_client_id: str = Field(default="iot_backend_main")

    # ============================================================
    # Configuración de Pydantic Settings
    # ============================================================
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore"
    )


# ============================================================
# Instancia Global de Settings
# ============================================================
# Esta instancia se importa en toda la aplicación
settings = Settings()


# ============================================================
# Función Helper para Debugging
# ============================================================
def print_settings() -> None:
    """
    Imprime la configuración actual (para debugging).
    ADVERTENCIA: No usar en producción, expone secretos.
    """
    if settings.environment != "development":
        print("⚠️  print_settings() solo disponible en desarrollo")
        return

    print("\n" + "=" * 60)
    print("CONFIGURACIÓN DEL SISTEMA")
    print("=" * 60)
    print(f"Proyecto: {settings.project_name} v{settings.version}")
    print(f"Entorno: {settings.environment}")
    print(f"Debug: {settings.debug}")
    print(f"Database URL: {settings.database_url}")
    print(f"Redis URL: {settings.redis_url}")
    print(f"CORS Origins: {settings.cors_origins_list}")
    print(f"JWT Algorithm: {settings.jwt_algorithm}")
    print(f"Token Expiration: {settings.access_token_expire_minutes} min")
    print(f"Log Level: {settings.log_level}")
    print(f"SMTP Enabled: {settings.smtp_enabled}")
    print(f"Telegram Enabled: {settings.telegram_enabled}")
    print("=" * 60 + "\n")
