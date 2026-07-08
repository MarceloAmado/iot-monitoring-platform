"""
Endpoints de SensorReadings (POST desde ESP32, GET con filtros).
"""

import logging
from datetime import datetime, timedelta
from typing import List, Optional
from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, status, Query
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
import pandas as pd
import io

from app.api.deps import get_db, get_current_active_user, validate_device_api_key
from app.models.device import Device
from app.models.sensor_reading import SensorReading
from app.models.user import User
from app.schemas.sensor_reading import SensorReadingCreate, SensorReading as SensorReadingSchema

logger = logging.getLogger(__name__)


router = APIRouter(prefix="/readings", tags=["Sensor Readings"])


@router.post("", response_model=SensorReadingSchema, status_code=status.HTTP_201_CREATED, summary="Crear reading (ESP32)")
def create_reading(
    reading_data: SensorReadingCreate,
    background_tasks: BackgroundTasks,
    device: Device = Depends(validate_device_api_key),
    db: Session = Depends(get_db)
):
    """
    Crea un nuevo sensor reading (usado por ESP32).

    Este es el endpoint CRITICO que los devices ESP32 llaman cada vez
    que toman una medición. Debe ser rápido y eficiente.

    **Autenticación requerida:**
    - Header `X-API-Key`: API Key del device (en plaintext)
    - Header `X-Device-EUI`: Device EUI (ej: ESP32_LAB_001)

    La API Key será validada contra la versión encriptada almacenada en la DB.

    Args:
        reading_data: Datos de la medición (data_payload, timestamp)
        device: Device autenticado mediante API Key (inyectado por middleware)
        db: Sesión de base de datos

    Returns:
        SensorReadingSchema: Reading creado

    Raises:
        HTTPException 401: Si la API Key es inválida
        HTTPException 404: Si el device no existe
    """
    # El device ya fue validado por el middleware validate_device_api_key
    # Verificar que el device_eui en el body coincida con el del header (opcional, seguridad extra)
    if reading_data.device_eui != device.device_eui:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Device EUI en body ({reading_data.device_eui}) no coincide con header ({device.device_eui})"
        )

    # Calcular quality_score basico (en produccion seria mas sofisticado)
    quality_score = calculate_quality_score(reading_data.data_payload)

    # Crear reading
    reading = SensorReading(
        device_id=device.id,
        data_payload=reading_data.data_payload,
        quality_score=quality_score,
        timestamp=reading_data.timestamp or datetime.utcnow(),
        processed=False
    )

    db.add(reading)

    # Actualizar last_seen_at del device
    device.last_seen_at = datetime.utcnow()

    db.commit()
    db.refresh(reading)

    # Evaluar alertas en background para no bloquear la respuesta al ESP32
    background_tasks.add_task(_evaluate_and_notify_alerts, reading.id)

    # Emitir evento WebSocket en background para no bloquear respuesta
    background_tasks.add_task(_emit_ws_new_reading, device.id, reading)

    return reading


@router.get("", response_model=List[SensorReadingSchema], summary="Listar readings")
def list_readings(
    device_id: Optional[int] = Query(None, description="Filtrar por device ID"),
    date_from: Optional[datetime] = Query(None, description="Fecha desde (UTC)"),
    date_to: Optional[datetime] = Query(None, description="Fecha hasta (UTC)"),
    skip: int = Query(0, ge=0, description="Registros a saltar"),
    limit: int = Query(100, ge=1, le=1000, description="Registros a retornar"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Lista sensor readings con filtros opcionales.

    **RBAC aplicado:**
    - super_admin: Ve todos los readings
    - otros roles: Solo readings de devices en sus allowed_location_ids

    Args:
        device_id: Filtrar por device ID
        date_from: Fecha desde (UTC)
        date_to: Fecha hasta (UTC)
        skip: Registros a saltar (paginacion)
        limit: Registros a retornar (max 1000)
        db: Sesion de base de datos
        current_user: Usuario autenticado

    Returns:
        List[SensorReadingSchema]: Lista de readings filtrados por permisos
    """
    from app.models.device import Device
    from app.models.asset import Asset
    from app.core.permissions import is_super_admin
    from sqlalchemy.orm import joinedload

    # Query base con joins necesarios para RBAC
    query = db.query(SensorReading).join(Device).join(Asset)

    # OPTIMIZACIÓN: Eager load del device para evitar N+1 queries
    query = query.options(joinedload(SensorReading.device))

    # Aplicar filtro RBAC: solo readings de devices permitidos
    if not is_super_admin(current_user):
        if current_user.allowed_location_ids:
            query = query.filter(Asset.location_id.in_(current_user.allowed_location_ids))
        else:
            # Sin locations permitidas: sin datos
            query = query.filter(SensorReading.id == -1)

    # Aplicar filtros adicionales
    if device_id:
        query = query.filter(SensorReading.device_id == device_id)

    if date_from:
        query = query.filter(SensorReading.timestamp >= date_from)

    if date_to:
        query = query.filter(SensorReading.timestamp <= date_to)
    else:
        # Por defecto, solo ultimas 24 horas si no se especifica date_to
        if not date_from:
            date_from = datetime.utcnow() - timedelta(days=1)
            query = query.filter(SensorReading.timestamp >= date_from)

    # Ordenar por timestamp descendente (mas recientes primero)
    query = query.order_by(SensorReading.timestamp.desc())

    # Aplicar paginacion
    readings = query.offset(skip).limit(limit).all()

    return readings


@router.get("/export", summary="Exportar readings a CSV/Excel")
def export_readings(
    device_id: Optional[int] = Query(None, description="Filtrar por device ID"),
    date_from: Optional[datetime] = Query(None, description="Fecha desde (UTC)"),
    date_to: Optional[datetime] = Query(None, description="Fecha hasta (UTC)"),
    format: str = Query("csv", pattern="^(csv|excel)$", description="Formato de exportación: csv o excel"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Exporta sensor readings a CSV o Excel con filtros opcionales.

    **Formatos soportados:**
    - `csv`: Archivo CSV con separador de comas
    - `excel`: Archivo XLSX con formato Excel

    **Filtros:**
    - `device_id`: Filtra por device específico
    - `date_from`: Fecha desde (UTC) - Si no se especifica, últimos 7 días
    - `date_to`: Fecha hasta (UTC) - Si no se especifica, ahora
    - `format`: csv o excel (default: csv)

    **Columnas incluidas:**
    - id: ID del reading
    - device_id: ID del device
    - device_eui: EUI del device
    - device_name: Nombre amigable del device
    - timestamp: Fecha y hora de la medición (UTC)
    - quality_score: Score de calidad del reading
    - processed: Si fue procesado por el sistema de alertas
    - data_payload: Datos del sensor (columnas dinámicas por variable)

    **Ejemplo de uso:**
    ```
    GET /api/v1/readings/export?device_id=1&format=csv&date_from=2025-11-01&date_to=2025-11-23
    ```

    Args:
        device_id: Filtrar por device ID
        date_from: Fecha desde (UTC)
        date_to: Fecha hasta (UTC)
        format: Formato de exportación (csv o excel)
        db: Sesión de base de datos
        current_user: Usuario autenticado

    Returns:
        StreamingResponse: Archivo descargable en el formato especificado
    """
    # Construir query base
    query = db.query(SensorReading).join(Device)

    # Aplicar filtros
    if device_id:
        query = query.filter(SensorReading.device_id == device_id)

    if date_from:
        query = query.filter(SensorReading.timestamp >= date_from)
    else:
        # Por defecto, últimos 7 días
        date_from = datetime.utcnow() - timedelta(days=7)
        query = query.filter(SensorReading.timestamp >= date_from)

    if date_to:
        query = query.filter(SensorReading.timestamp <= date_to)

    # Ordenar por timestamp ascendente (más antiguos primero para el export)
    query = query.order_by(SensorReading.timestamp.asc())

    # Ejecutar query (sin límite para exportación completa)
    readings = query.all()

    if not readings:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No se encontraron readings con los filtros especificados"
        )

    # Preparar datos para DataFrame
    data = []
    for reading in readings:
        # Datos base
        row = {
            'id': reading.id,
            'device_id': reading.device_id,
            'device_eui': reading.device.device_eui,
            'device_name': reading.device.name,
            'timestamp': reading.timestamp,
            'quality_score': reading.quality_score,
            'processed': reading.processed,
        }

        # Expandir data_payload (JSONB) en columnas separadas
        if reading.data_payload:
            for key, value in reading.data_payload.items():
                row[f'data_{key}'] = value

        data.append(row)

    # Crear DataFrame
    df = pd.DataFrame(data)

    # Formatear columna timestamp
    df['timestamp'] = pd.to_datetime(df['timestamp']).dt.strftime('%Y-%m-%d %H:%M:%S')

    # Generar archivo según formato
    if format == "csv":
        # Generar CSV
        output = io.StringIO()
        df.to_csv(output, index=False, encoding='utf-8')
        output.seek(0)

        # Generar nombre de archivo
        filename = f"sensor_readings_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}.csv"

        return StreamingResponse(
            iter([output.getvalue()]),
            media_type="text/csv",
            headers={
                "Content-Disposition": f"attachment; filename={filename}",
                "Cache-Control": "no-cache"
            }
        )

    elif format == "excel":
        # Generar Excel
        output = io.BytesIO()

        # Usar ExcelWriter para más control
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            df.to_excel(writer, index=False, sheet_name='Sensor Readings')

            # Acceder al worksheet para formateo adicional
            worksheet = writer.sheets['Sensor Readings']

            # Auto-ajustar ancho de columnas
            for column in worksheet.columns:
                max_length = 0
                column_letter = column[0].column_letter
                for cell in column:
                    try:
                        if len(str(cell.value)) > max_length:
                            max_length = len(str(cell.value))
                    except:
                        pass
                adjusted_width = min(max_length + 2, 50)  # Max 50 caracteres
                worksheet.column_dimensions[column_letter].width = adjusted_width

        output.seek(0)

        # Generar nombre de archivo
        filename = f"sensor_readings_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}.xlsx"

        return StreamingResponse(
            output,
            media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            headers={
                "Content-Disposition": f"attachment; filename={filename}",
                "Cache-Control": "no-cache"
            }
        )


# NOTA: esta ruta debe registrarse DESPUES de /export; si no, FastAPI intenta
# parsear "export" como reading_id y /readings/export devuelve 422.
@router.get("/{reading_id}", response_model=SensorReadingSchema, summary="Obtener reading por ID")
def get_reading(
    reading_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Obtiene un reading por su ID.

    **RBAC aplicado:**
    - Verifica que el usuario tenga acceso al device asociado al reading

    Args:
        reading_id: ID del reading
        db: Sesion de base de datos
        current_user: Usuario autenticado

    Returns:
        SensorReadingSchema: Reading encontrado

    Raises:
        HTTPException 404: Si el reading no existe
        HTTPException 403: Si no tiene permiso para ver este reading
    """
    reading = db.query(SensorReading).filter(SensorReading.id == reading_id).first()

    if not reading:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Reading con ID {reading_id} no encontrado"
        )

    # Verificar permisos RBAC: el usuario debe tener acceso al device del reading
    from app.core.permissions import has_device_access

    if not has_device_access(current_user, reading.device, db):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="No tienes acceso a este reading"
        )

    return reading


def _evaluate_and_notify_alerts(reading_id: int):
    """
    Background task: evalúa alertas y envía notificaciones para un reading.
    Usa su propia sesión de DB para no depender de la sesión del request.
    """
    from app.core.database import SessionLocal
    from app.services.alert_service import evaluate_reading_alerts
    from app.services.notification_service import send_multiple_alert_notifications

    db = SessionLocal()
    try:
        reading = db.query(SensorReading).filter(SensorReading.id == reading_id).first()
        if not reading:
            logger.warning(f"Reading {reading_id} no encontrado para evaluar alertas")
            return

        alerts_triggered = evaluate_reading_alerts(db, reading)

        if alerts_triggered:
            alert_ids = [alert.id for alert in alerts_triggered]
            send_multiple_alert_notifications(db, alert_ids)

            # Push en tiempo real al frontend (best-effort)
            from app.services.websocket_service import emit_alerts_triggered_sync
            emit_alerts_triggered_sync(alerts_triggered)

    except Exception as e:
        logger.error(f"Error al evaluar alertas para reading {reading_id}: {str(e)}")
    finally:
        db.close()


def _emit_ws_new_reading(device_id: int, reading):
    """Background task: emite evento WebSocket con la nueva lectura."""
    import asyncio
    try:
        from app.services.websocket_service import emit_new_reading
        loop = asyncio.new_event_loop()
        loop.run_until_complete(emit_new_reading(device_id, {
            "id": reading.id,
            "timestamp": reading.timestamp.isoformat() if reading.timestamp else None,
            "data_payload": reading.data_payload,
            "quality_score": reading.quality_score,
        }))
        loop.close()
    except Exception as e:
        logger.debug(f"WebSocket emit falló (no crítico): {e}")


def calculate_quality_score(data_payload: dict) -> float:
    """
    Calcula un score de calidad basico para el reading.

    En produccion, esto seria mas sofisticado:
    - Detectar valores fuera de rango fisico
    - Detectar cambios bruscos sospechosos
    - Verificar timestamp valido
    - etc.

    Args:
        data_payload: Datos del sensor

    Returns:
        float: Score entre 0.0 y 1.0
    """
    score = 1.0

    # Verificar que haya al menos una variable
    if not data_payload or len(data_payload) == 0:
        return 0.0

    # Detectar valores de error (-999)
    for key, value in data_payload.items():
        if isinstance(value, (int, float)):
            if value == -999 or value == -999.0:
                score -= 0.3

    # Asegurar que el score este entre 0 y 1
    return max(0.0, min(1.0, score))
