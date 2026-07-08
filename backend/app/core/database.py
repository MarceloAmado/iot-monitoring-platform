"""
Sistema de Monitoreo IoT
Configuración de Base de Datos (PostgreSQL + SQLAlchemy)

Este módulo configura la conexión a PostgreSQL usando SQLAlchemy 2.0.
Proporciona el engine, sessionmaker y la base declarativa para los modelos.
"""

from typing import Generator
from sqlalchemy import create_engine, event, text
from sqlalchemy.orm import sessionmaker, Session, declarative_base
from sqlalchemy.pool import QueuePool

from app.core.config import settings


# ============================================================
# Configuración del Engine de SQLAlchemy
# ============================================================

# Engine con pool de conexiones configurado para producción
engine = create_engine(
    settings.database_url,
    # Pool de conexiones
    poolclass=QueuePool,
    pool_size=10,  # Número de conexiones mantenidas en el pool
    max_overflow=20,  # Conexiones adicionales si el pool está lleno
    pool_timeout=30,  # Timeout para obtener una conexión del pool (segundos)
    pool_recycle=3600,  # Reciclar conexiones cada 1 hora (evita "gone away")
    pool_pre_ping=True,  # Verificar conexión antes de usarla
    # Echo SQL queries en desarrollo (solo para debugging)
    echo=settings.debug and settings.environment == "development",
)


# ============================================================
# Event Listeners para Optimización de PostgreSQL
# ============================================================

@event.listens_for(engine, "connect")
def receive_connect(dbapi_conn, connection_record):
    """
    Event listener que se ejecuta al establecer una conexión.
    Configura parámetros de optimización para PostgreSQL.
    """
    # Establecer timezone a UTC
    cursor = dbapi_conn.cursor()
    cursor.execute("SET timezone TO 'UTC'")
    cursor.close()


# ============================================================
# SessionLocal Factory
# ============================================================

# SessionLocal: Factory para crear sesiones de base de datos
# IMPORTANTE: No usar SessionLocal directamente, usar get_db()
SessionLocal = sessionmaker(
    autocommit=False,  # Transacciones manuales (más control)
    autoflush=False,   # No hacer flush automático
    bind=engine,
)


# ============================================================
# Base Declarativa para Modelos ORM
# ============================================================

# Base: Clase base para todos los modelos SQLAlchemy
# Todos los modelos deben heredar de esta clase
Base = declarative_base()


# ============================================================
# Dependency Injection para FastAPI
# ============================================================

def get_db() -> Generator[Session, None, None]:
    """
    Dependency para obtener una sesión de base de datos.

    Esta función se usa como dependencia en los endpoints de FastAPI
    para inyectar automáticamente una sesión de DB.

    Yields:
        Session: Sesión de SQLAlchemy

    Example:
        ```python
        @router.get("/devices")
        def get_devices(db: Session = Depends(get_db)):
            devices = db.query(Device).all()
            return devices
        ```

    Notas:
        - La sesión se cierra automáticamente al terminar el request
        - Si hay una excepción, se hace rollback automático
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# ============================================================
# Funciones Helper para Gestión de DB
# ============================================================

def init_db() -> None:
    """
    Inicializa la base de datos creando todas las tablas.

    IMPORTANTE: Esta función solo se debe usar en desarrollo inicial.
    En producción, usar Alembic para migraciones.

    Raises:
        Exception: Si no se puede conectar a la base de datos
    """
    try:
        # Importar todos los modelos para que SQLAlchemy los registre
        from app.models import (
            location,
            asset,
            device,
            sensor_reading,
            user,
            alert,
        )

        # Crear todas las tablas
        Base.metadata.create_all(bind=engine)
        print("✓ Base de datos inicializada correctamente")

    except Exception as e:
        print(f"✗ Error al inicializar base de datos: {e}")
        raise


def check_db_connection() -> bool:
    """
    Verifica que la conexión a la base de datos esté funcionando.

    Returns:
        bool: True si la conexión es exitosa, False en caso contrario

    Example:
        ```python
        if not check_db_connection():
            raise Exception("No se puede conectar a la base de datos")
        ```
    """
    try:
        # Intentar obtener una sesión y hacer una query simple
        db = SessionLocal()
        db.execute(text("SELECT 1"))
        db.close()
        return True
    except Exception as e:
        print(f"✗ Error de conexión a base de datos: {e}")
        return False


def drop_all_tables() -> None:
    """
    PELIGRO: Elimina TODAS las tablas de la base de datos.

    Esta función solo debe usarse en desarrollo/testing.
    NUNCA ejecutar en producción.

    Raises:
        RuntimeError: Si se intenta ejecutar en producción
    """
    if settings.environment == "production":
        raise RuntimeError(
            "⚠️  PROHIBIDO: No se puede ejecutar drop_all_tables() en producción"
        )

    confirmation = input(
        "⚠️  ADVERTENCIA: Esto eliminará TODAS las tablas. "
        "Escribir 'CONFIRMAR' para continuar: "
    )

    if confirmation != "CONFIRMAR":
        print("Operación cancelada")
        return

    Base.metadata.drop_all(bind=engine)
    print("✓ Todas las tablas han sido eliminadas")


# ============================================================
# Context Manager para Sesiones Manuales
# ============================================================

class db_session:
    """
    Context manager para usar sesiones de DB fuera de FastAPI.

    Útil para scripts, background jobs, o testing.

    Example:
        ```python
        from app.core.database import db_session
        from app.models.device import Device

        with db_session() as db:
            devices = db.query(Device).filter(Device.status == 'active').all()
            print(f"Devices activos: {len(devices)}")
        ```
    """

    def __enter__(self) -> Session:
        """Crear y retornar una sesión."""
        self.db = SessionLocal()
        return self.db

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Cerrar la sesión al salir del context."""
        if exc_type is not None:
            # Si hubo una excepción, hacer rollback
            self.db.rollback()
        self.db.close()
