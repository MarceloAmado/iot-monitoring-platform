"""
Sistema de Monitoreo IoT
Entry Point de la Aplicación FastAPI

Este es el archivo principal que arranca la aplicación.
Configura FastAPI, middlewares, CORS, y registra los routers.
"""

from contextlib import asynccontextmanager

from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from sqlalchemy.exc import SQLAlchemyError
import time
import logging

from app.core.config import settings
from app.core.database import check_db_connection

# Configurar logging
logging.basicConfig(
    level=getattr(logging, settings.log_level),
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


# ============================================================
# Lifespan (startup / shutdown)
# ============================================================

@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Ciclo de vida de la aplicación (reemplaza on_event, deprecado).

    Al iniciar verifica la base de datos, arranca el scheduler de jobs,
    el cliente MQTT y monta el WebSocket. Al cerrar detiene los servicios.
    """
    # ---------- Startup ----------
    logger.info("=" * 60)
    logger.info(f"Iniciando {settings.project_name} v{settings.version}")
    logger.info(f"Entorno: {settings.environment}")
    logger.info("=" * 60)

    # Verificar conexión a base de datos
    if check_db_connection():
        logger.info("✓ Conexión a PostgreSQL exitosa")
    else:
        logger.error("✗ No se pudo conectar a PostgreSQL")
        if settings.environment == "production":
            raise Exception("Fallo crítico: No hay conexión a base de datos")

    # Iniciar scheduler de jobs periódicos
    try:
        from app.jobs import start_scheduler
        start_scheduler()
        logger.info("✓ Scheduler de jobs iniciado (chequeo offline cada 5 min)")
    except Exception as e:
        logger.error(f"✗ Error al iniciar scheduler: {str(e)}")

    # Iniciar cliente MQTT (SCADA Fase 1.3)
    try:
        from app.services.mqtt_client import mqtt_service
        mqtt_service.start()
        logger.info("✓ Cliente MQTT iniciado para telemetría de devices")
    except Exception as e:
        logger.error(f"✗ Error al iniciar cliente MQTT: {str(e)}")
        logger.warning("La aplicación continuará sin MQTT (telemetría deshabilitada)")

    # Montar Socket.IO para WebSocket en tiempo real
    try:
        from app.services.websocket_service import socket_app
        app.mount("/ws", socket_app)
        logger.info("✓ WebSocket (Socket.IO) montado en /ws")
    except Exception as e:
        logger.error(f"✗ Error al montar WebSocket: {str(e)}")
        logger.warning("La aplicación continuará sin WebSocket")

    logger.info("✓ Servidor escuchando en http://0.0.0.0:8000")
    logger.info(f"✓ Documentación disponible en http://localhost:8000{settings.api_v1_prefix}/docs")

    yield

    # ---------- Shutdown ----------
    logger.info("Cerrando aplicación...")

    try:
        from app.jobs import stop_scheduler
        stop_scheduler()
        logger.info("✓ Scheduler de jobs detenido")
    except Exception as e:
        logger.error(f"✗ Error al detener scheduler: {str(e)}")

    try:
        from app.services.mqtt_client import mqtt_service
        mqtt_service.stop()
        logger.info("✓ Cliente MQTT detenido")
    except Exception as e:
        logger.error(f"✗ Error al detener cliente MQTT: {str(e)}")

    logger.info("✓ Aplicación cerrada correctamente")


# ============================================================
# Crear Instancia de FastAPI
# ============================================================

app = FastAPI(
    title=settings.project_name,
    description=settings.description,
    version=settings.version,
    docs_url=f"{settings.api_v1_prefix}/docs",
    redoc_url=f"{settings.api_v1_prefix}/redoc",
    openapi_url=f"{settings.api_v1_prefix}/openapi.json",
    lifespan=lifespan,
)


# ============================================================
# Configurar CORS
# ============================================================

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],  # Permitir todos los métodos (GET, POST, PUT, DELETE, etc.)
    allow_headers=["*"],  # Permitir todos los headers
)


# ============================================================
# Middleware de Logging de Requests
# ============================================================

@app.middleware("http")
async def log_requests(request: Request, call_next):
    """
    Middleware que loguea cada request HTTP.

    Registra:
    - Método HTTP y path
    - Tiempo de procesamiento
    - Status code de respuesta
    """
    start_time = time.time()

    # Procesar el request
    response = await call_next(request)

    # Calcular tiempo de procesamiento
    process_time = time.time() - start_time

    # Loguear
    logger.info(
        f"{request.method} {request.url.path} "
        f"- Status: {response.status_code} "
        f"- Time: {process_time:.3f}s"
    )

    # Agregar header custom con tiempo de procesamiento
    response.headers["X-Process-Time"] = str(process_time)

    return response


# ============================================================
# Exception Handlers Globales
# ============================================================

@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    """
    Handler para errores de validación de Pydantic.

    Retorna un JSON amigable con los errores de validación.
    """
    errors = []
    for error in exc.errors():
        errors.append({
            "field": " -> ".join(str(loc) for loc in error["loc"]),
            "message": error["msg"],
            "type": error["type"],
        })

    logger.warning(f"Validation error en {request.url.path}: {errors}")

    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={
            "detail": "Error de validación",
            "errors": errors
        }
    )


@app.exception_handler(SQLAlchemyError)
async def sqlalchemy_exception_handler(request: Request, exc: SQLAlchemyError):
    """
    Handler para errores de SQLAlchemy (base de datos).

    En producción, no exponer detalles del error de DB.
    """
    logger.error(f"Database error en {request.url.path}: {exc}")

    if settings.environment == "production":
        error_detail = "Error interno del servidor"
    else:
        error_detail = str(exc)

    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "detail": error_detail,
            "type": "database_error"
        }
    )


def _check_redis() -> str:
    """Verifica conexión a Redis."""
    try:
        from app.services.cache_service import cache
        if cache._is_available() and cache.client.ping():
            return "healthy"
        return "unhealthy"
    except Exception:
        return "unhealthy"


# ============================================================
# Endpoints de Health Check
# ============================================================

@app.get(
    f"{settings.api_v1_prefix}/health",
    tags=["Health"],
    summary="Health Check",
    description="Endpoint para verificar que el servidor está funcionando"
)
async def health_check():
    """
    Health check básico.

    Returns:
        dict: Estado del servidor y servicios
    """
    db_status = "healthy" if check_db_connection() else "unhealthy"

    return {
        "status": "online",
        "environment": settings.environment,
        "version": settings.version,
        "services": {
            "database": db_status,
            "redis": _check_redis()
        }
    }


@app.get(
    "/",
    tags=["Root"],
    summary="Root Endpoint",
    description="Redirige a la documentación de la API"
)
async def root():
    """
    Endpoint raíz que da información básica de la API.
    """
    return {
        "message": f"Bienvenido a {settings.project_name}",
        "version": settings.version,
        "docs": f"{settings.api_v1_prefix}/docs",
        "health": f"{settings.api_v1_prefix}/health"
    }


# ============================================================
# Registrar Routers (API v1)
# ============================================================

from app.api.v1 import auth, devices, readings, alerts, users, sensors, uploads, audit, firmware, locations, assets

# Auth endpoints (login, logout, me)
app.include_router(
    auth.router,
    prefix=settings.api_v1_prefix
)

# Device endpoints (CRUD + schema)
app.include_router(
    devices.router,
    prefix=settings.api_v1_prefix
)

# Sensor readings endpoints (POST desde ESP32, GET con filtros)
app.include_router(
    readings.router,
    prefix=settings.api_v1_prefix
)

# Alert rules and alert history endpoints
app.include_router(
    alerts.router,
    prefix=settings.api_v1_prefix
)

# Users endpoints (CRUD, solo para super_admin)
app.include_router(
    users.router,
    prefix=settings.api_v1_prefix
)

# Sensor catalog endpoints (CRUD para catálogo de sensores)
app.include_router(
    sensors.router,
    prefix=settings.api_v1_prefix
)

# Uploads endpoints (manejo de archivos, imágenes de perfil)
app.include_router(
    uploads.router,
    prefix=settings.api_v1_prefix + "/uploads",
    tags=["Uploads"]
)

# Audit log endpoints (SCADA - Fase 1.1)
app.include_router(
    audit.router,
    prefix=settings.api_v1_prefix + "/audit",
    tags=["Audit Log"]
)

# Firmware OTA endpoints (Sprint 4)
app.include_router(
    firmware.router,
    prefix=settings.api_v1_prefix,
    tags=["Firmware OTA"]
)

# Locations y LocationGroups endpoints (CRUD con RBAC)
app.include_router(
    locations.router,
    prefix=settings.api_v1_prefix
)

# Assets endpoints (CRUD con RBAC)
app.include_router(
    assets.router,
    prefix=settings.api_v1_prefix
)


# ============================================================
# Entry Point para Ejecución Directa (Desarrollo)
# ============================================================

if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,  # Hot reload en desarrollo
        log_level=settings.log_level.lower()
    )
