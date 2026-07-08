"""
Endpoints de Devices (GET, POST, PATCH, DELETE, schema).
"""

from typing import List
from fastapi import APIRouter, Depends, HTTPException, status, Request
from sqlalchemy.orm import Session, joinedload

from app.api.deps import get_db, get_current_active_user, require_admin
from app.models.device import Device
from app.models.asset import Asset
from app.models.user import User
from app.schemas.device import (
    Device as DeviceSchema,
    DeviceCreate,
    DeviceUpdate,
    DeviceCreateResponse,
    DeviceSchema as DeviceSchemaResponse,
    DeviceVariableSchema,
    DeviceHeartbeat,
    DeviceHeartbeatResponse,
    DeviceHealthDashboard,
    DeviceHealthMetrics
)
from app.core.permissions import filter_devices_by_permission, require_device_access, can_manage_devices
from app.services.audit_service import AuditService
from app.core.security import encrypt_api_key


router = APIRouter(prefix="/devices", tags=["Devices"])


@router.get("", response_model=List[DeviceSchema], summary="Listar devices")
def list_devices(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Lista todos los devices accesibles por el usuario.

    **RBAC aplicado:**
    - super_admin: Ve todos los devices
    - otros roles: Solo devices cuyo asset esté en sus allowed_location_ids

    Args:
        skip: Numero de registros a saltar (paginacion)
        limit: Numero maximo de registros a retornar
        db: Sesion de base de datos
        current_user: Usuario autenticado

    Returns:
        List[DeviceSchema]: Lista de devices filtrados por permisos
    """
    from app.services.cache_service import cache, CacheTTL

    # Intentar cache (solo para super_admin - otros roles tienen filtros dinámicos)
    cache_key = f"devices:list:skip:{skip}:limit:{limit}"
    if current_user.role == "super_admin":
        cached_data = cache.get(cache_key)
        if cached_data:
            return [DeviceSchema(**d) for d in cached_data]

    # Aplicar filtro RBAC con eager loading para evitar N+1 queries
    query = filter_devices_by_permission(current_user, db)

    # OPTIMIZACIÓN: Eager load de relaciones asset (y su location)
    query = query.options(
        joinedload(Device.asset).joinedload(Asset.location)
    )

    devices = query.offset(skip).limit(limit).all()

    # Guardar en cache solo para super_admin
    if current_user.role == "super_admin":
        try:
            cache.set(cache_key, [DeviceSchema.model_validate(d).model_dump() for d in devices], ttl=CacheTTL.DEVICE_LIST)
        except Exception:
            pass  # No fallar si el cache falla

    return devices


@router.get("/{device_id}", response_model=DeviceSchema, summary="Obtener device por ID")
def get_device(
    device_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Obtiene un device por su ID.

    **RBAC aplicado:**
    - Verifica que el usuario tenga acceso al device según sus allowed_location_ids

    Args:
        device_id: ID del device
        db: Sesion de base de datos
        current_user: Usuario autenticado

    Returns:
        DeviceSchema: Device encontrado

    Raises:
        HTTPException 404: Si el device no existe
        HTTPException 403: Si no tiene permiso para ver este device
    """
    device = db.query(Device).filter(Device.id == device_id).first()

    if not device:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Device con ID {device_id} no encontrado"
        )

    # Verificar permisos RBAC
    require_device_access(current_user, device, db)

    return device


@router.post("", response_model=DeviceCreateResponse, status_code=status.HTTP_201_CREATED, summary="Crear device")
def create_device(
    device_data: DeviceCreate,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin)
):
    """
    Crea un nuevo device (solo admins).

    **IMPORTANTE:** Si se provee api_key, será encriptada automáticamente y
    solo se mostrará en plaintext en esta respuesta (única vez).

    Args:
        device_data: Datos del device a crear
        request: FastAPI Request (para audit log)
        db: Sesion de base de datos
        current_user: Usuario admin

    Returns:
        DeviceCreateResponse: Device creado (incluye api_key en plaintext una sola vez)

    Raises:
        HTTPException 400: Si el device_eui ya existe
    """
    # Verificar que el device_eui no exista
    existing_device = db.query(Device).filter(Device.device_eui == device_data.device_eui).first()
    if existing_device:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Device con EUI '{device_data.device_eui}' ya existe"
        )

    # Guardar la API key en plaintext para retornarla (solo esta vez)
    plaintext_api_key = device_data.api_key

    # Crear device
    device_dict = device_data.model_dump()

    # Encriptar API key si fue provista
    if device_data.api_key:
        device_dict["api_key_encrypted"] = encrypt_api_key(device_data.api_key)
        # Mantener plaintext temporalmente (backward compatibility)
        device_dict["api_key"] = device_data.api_key

    device = Device(**device_dict)
    db.add(device)
    db.commit()
    db.refresh(device)

    # Registrar creación de device (SIN incluir la API key en el audit log)
    AuditService.log_from_request(
        db=db,
        request=request,
        action_type="DEVICE_CREATED",
        current_user=current_user,
        device_id=device.id,
        entity_type="device",
        entity_id=device.id,
        changes={
            "after": {
                "device_eui": device.device_eui,
                "name": device.name,
                "status": device.status,
                "asset_id": device.asset_id,
                "has_api_key": device.api_key_encrypted is not None  # Solo registrar existencia
            }
        }
    )

    # OPTIMIZACIÓN: Invalidar caché de listado de devices
    from app.services.cache_service import cache
    cache.delete_pattern("devices:list:*")
    cache.delete_pattern("health:dashboard:*")  # Nuevo device afecta dashboard

    # Retornar device con api_key en plaintext (solo esta vez)
    # Forzar el atributo api_key para que aparezca en la respuesta
    device.api_key = plaintext_api_key
    return device


@router.patch("/{device_id}", response_model=DeviceSchema, summary="Actualizar device")
def update_device(
    device_id: int,
    device_data: DeviceUpdate,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin)
):
    """
    Actualiza un device existente (solo admins).

    Args:
        device_id: ID del device a actualizar
        device_data: Datos a actualizar
        request: FastAPI Request (para audit log)
        db: Sesion de base de datos
        current_user: Usuario admin

    Returns:
        DeviceSchema: Device actualizado

    Raises:
        HTTPException 404: Si el device no existe
    """
    device = db.query(Device).filter(Device.id == device_id).first()

    if not device:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Device con ID {device_id} no encontrado"
        )

    # Guardar estado anterior para audit log
    before_state = {
        "device_eui": device.device_eui,
        "name": device.name,
        "status": device.status,
        "asset_id": device.asset_id,
        "firmware_version": device.firmware_version
    }

    # Actualizar campos
    update_data = device_data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(device, field, value)

    db.commit()
    db.refresh(device)

    # Guardar estado posterior para audit log
    after_state = {
        "device_eui": device.device_eui,
        "name": device.name,
        "status": device.status,
        "asset_id": device.asset_id,
        "firmware_version": device.firmware_version
    }

    # Registrar actualización de device
    AuditService.log_from_request(
        db=db,
        request=request,
        action_type="DEVICE_UPDATED",
        current_user=current_user,
        device_id=device.id,
        entity_type="device",
        entity_id=device.id,
        changes={
            "before": before_state,
            "after": after_state
        }
    )

    # OPTIMIZACIÓN: Invalidar caché relacionado con este device
    from app.services.cache_service import cache, CacheKeys
    cache.delete(CacheKeys.device_schema(device_id))
    cache.delete(CacheKeys.device_health(device_id))
    cache.delete_pattern("health:dashboard:*")  # Invalidar todos los dashboards
    cache.delete_pattern("devices:list:*")  # Invalidar listado de devices

    return device


@router.delete("/{device_id}", status_code=status.HTTP_204_NO_CONTENT, summary="Eliminar device")
def delete_device(
    device_id: int,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin)
):
    """
    Elimina un device (solo admins).

    IMPORTANTE: Las readings del device NO se eliminan, quedan como "huérfanas"
    con el campo deleted_device_name indicando que el device fue eliminado.

    Args:
        device_id: ID del device a eliminar
        request: FastAPI Request (para audit log)
        db: Sesion de base de datos
        current_user: Usuario admin

    Raises:
        HTTPException 404: Si el device no existe
    """
    from app.models.sensor_reading import SensorReading
    from datetime import datetime

    device = db.query(Device).filter(Device.id == device_id).first()

    if not device:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Device con ID {device_id} no encontrado"
        )

    # Guardar info del device para audit log antes de eliminarlo
    device_info = {
        "device_eui": device.device_eui,
        "name": device.name,
        "status": device.status,
        "asset_id": device.asset_id
    }

    # Marcar todas las readings como huérfanas antes de eliminar el device
    deleted_name = f"Dispositivo Eliminado el {datetime.now().strftime('%d/%m/%Y')}"
    db.query(SensorReading).filter(SensorReading.device_id == device_id).update({
        "deleted_device_name": deleted_name
    })

    db.delete(device)
    db.commit()

    # Registrar eliminación de device
    AuditService.log_from_request(
        db=db,
        request=request,
        action_type="DEVICE_DELETED",
        current_user=current_user,
        entity_type="device",
        entity_id=device_id,
        changes={
            "before": device_info
        }
    )

    return None


@router.get("/{device_id}/schema", response_model=DeviceSchemaResponse, summary="Obtener schema del device")
def get_device_schema(
    device_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Obtiene el schema de variables que el device envia (auto-discovery).

    Este endpoint permite al frontend auto-generar graficos sin conocer
    de antemano que variables envia cada device.

    El schema se auto-descubre del ultimo reading del device.

    **Optimización:**
    - Caché Redis con TTL de 1 hora (schema cambia raramente)
    - Invalidación automática al crear/actualizar device

    Args:
        device_id: ID del device
        db: Sesion de base de datos
        current_user: Usuario autenticado

    Returns:
        DeviceSchemaResponse: Schema de variables

    Raises:
        HTTPException 404: Si el device no existe o no tiene readings
    """
    from app.models.sensor_reading import SensorReading
    from app.services.cache_service import cache, CacheKeys, CacheTTL

    # Intentar obtener del caché primero
    cache_key = CacheKeys.device_schema(device_id)
    cached_schema = cache.get(cache_key)

    if cached_schema:
        # Cache hit
        return DeviceSchemaResponse(**cached_schema)

    # Cache miss: consultar BD
    device = db.query(Device).filter(Device.id == device_id).first()

    if not device:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Device con ID {device_id} no encontrado"
        )

    # Obtener el ultimo reading para auto-descubrir el schema
    last_reading = db.query(SensorReading)\
        .filter(SensorReading.device_id == device_id)\
        .order_by(SensorReading.timestamp.desc())\
        .first()

    if not last_reading or not last_reading.data_payload:
        # Si no hay readings, retornar schema vacio (NO cachear)
        return DeviceSchemaResponse(
            device_id=device.id,
            variables=[]
        )

    # Auto-descubrir variables del data_payload
    variables = _discover_variables_from_payload(last_reading.data_payload)

    schema = DeviceSchemaResponse(
        device_id=device.id,
        variables=variables
    )

    # Guardar en caché (1 hora - el schema cambia raramente)
    cache.set(cache_key, schema.model_dump(), ttl=CacheTTL.DEVICE_SCHEMA)

    return schema


def _discover_variables_from_payload(payload: dict) -> List[DeviceVariableSchema]:
    """
    Auto-descubre variables del data_payload de un reading.

    Args:
        payload: Diccionario JSONB del data_payload

    Returns:
        Lista de DeviceVariableSchema
    """
    # Mapeo de keys conocidas a configuracion
    KNOWN_VARIABLES = {
        "temp_c": {
            "label": "Temperatura",
            "unit": "°C",
            "type": "float",
            "color": "#ff6b6b"
        },
        "humidity_pct": {
            "label": "Humedad Relativa",
            "unit": "%",
            "type": "float",
            "color": "#4ecdc4"
        },
        "pressure_bar": {
            "label": "Presión",
            "unit": "bar",
            "type": "float",
            "color": "#f9ca24"
        },
        "battery_v": {
            "label": "Batería",
            "unit": "V",
            "type": "float",
            "color": "#6ab04c"
        },
        "battery_mv": {
            "label": "Batería",
            "unit": "mV",
            "type": "int",
            "color": "#6ab04c"
        },
        "rssi_dbm": {
            "label": "Señal WiFi (RSSI)",
            "unit": "dBm",
            "type": "int",
            "color": "#686de0"
        },
        "uptime_sec": {
            "label": "Uptime",
            "unit": "seg",
            "type": "int",
            "color": "#95afc0"
        },
        "free_heap_bytes": {
            "label": "Memoria Libre",
            "unit": "bytes",
            "type": "int",
            "color": "#95afc0"
        },
    }

    variables = []

    for key, value in payload.items():
        # Determinar el tipo
        if isinstance(value, bool):
            var_type = "bool"
        elif isinstance(value, int):
            var_type = "int"
        elif isinstance(value, float):
            var_type = "float"
        elif isinstance(value, str):
            var_type = "string"
        else:
            var_type = "unknown"

        # Si la key es conocida, usar configuracion predefinida
        if key in KNOWN_VARIABLES:
            config = KNOWN_VARIABLES[key]
            variables.append(DeviceVariableSchema(
                key=key,
                label=config["label"],
                unit=config["unit"],
                type=config["type"],
                color=config["color"]
            ))
        else:
            # Variable desconocida, crear configuracion basica
            label = key.replace("_", " ").title()
            variables.append(DeviceVariableSchema(
                key=key,
                label=label,
                unit="",  # Sin unidad conocida
                type=var_type,
                color="#95a5a6"  # Color gris por defecto
            ))

    return variables


@router.get("/health/summary", summary="Resumen de salud de todos los devices")
def get_devices_health_summary(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Obtiene un resumen de salud de todos los devices accesibles.

    **RBAC aplicado:** Solo muestra devices según permisos del usuario

    **Métricas retornadas:**
    - total_devices: Total de devices
    - online_devices: Devices que reportaron en últimos 10 minutos
    - offline_devices: Devices sin reportar en 10+ minutos
    - warning_devices: Devices con señal débil (RSSI < -80 dBm)
    - critical_devices: Devices con batería baja (< 3.0V)

    Returns:
        dict: Métricas de salud agregadas
    """
    from datetime import datetime, timedelta
    from app.models.sensor_reading import SensorReading

    # Aplicar filtro RBAC
    query = filter_devices_by_permission(current_user, db)
    devices = query.all()

    total = len(devices)
    online = 0
    offline = 0
    warning = 0
    critical = 0

    now = datetime.utcnow()
    online_threshold = now - timedelta(minutes=10)

    for device in devices:
        # Check online status
        if device.last_seen_at and device.last_seen_at >= online_threshold:
            online += 1

            # Get last reading for additional metrics
            last_reading = db.query(SensorReading)\
                .filter(SensorReading.device_id == device.id)\
                .order_by(SensorReading.timestamp.desc())\
                .first()

            if last_reading and last_reading.data_payload:
                # Check RSSI (señal WiFi)
                rssi = last_reading.data_payload.get('rssi_dbm')
                if rssi and rssi < -80:
                    warning += 1

                # Check battery
                battery = last_reading.data_payload.get('battery_v')
                if battery and battery < 3.0:
                    critical += 1
        else:
            offline += 1

    return {
        "total_devices": total,
        "online_devices": online,
        "offline_devices": offline,
        "warning_devices": warning,
        "critical_devices": critical,
        "last_updated": now.isoformat()
    }


@router.get("/{device_id}/health", summary="Salud detallada de un device")
def get_device_health(
    device_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Obtiene métricas de salud detalladas de un device específico.

    **RBAC aplicado:** Verifica acceso al device

    **Métricas retornadas:**
    - status: online/offline/unknown
    - last_seen: Última vez que reportó
    - uptime_hours: Tiempo desde primer reading
    - total_readings: Total de lecturas recibidas
    - avg_interval_minutes: Intervalo promedio entre lecturas
    - last_rssi_dbm: Última señal WiFi
    - last_battery_v: Último voltaje de batería
    - quality_score_avg: Promedio de calidad de datos
    - alerts_triggered: Alertas disparadas (últimas 24h)

    Returns:
        dict: Métricas de salud del device
    """
    from datetime import datetime, timedelta
    from sqlalchemy import func
    from app.models.sensor_reading import SensorReading
    from app.models.alert import AlertHistory

    # Verificar que el device existe y tenemos acceso
    device = db.query(Device).filter(Device.id == device_id).first()
    if not device:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Device con ID {device_id} no encontrado"
        )

    require_device_access(current_user, device, db)

    # Status (online/offline)
    now = datetime.utcnow()
    online_threshold = now - timedelta(minutes=10)

    if device.last_seen_at and device.last_seen_at >= online_threshold:
        status = "online"
    elif device.last_seen_at:
        status = "offline"
    else:
        status = "unknown"

    # Total readings
    total_readings = db.query(func.count(SensorReading.id))\
        .filter(SensorReading.device_id == device_id)\
        .scalar()

    # First and last reading timestamps
    first_reading = db.query(SensorReading.timestamp)\
        .filter(SensorReading.device_id == device_id)\
        .order_by(SensorReading.timestamp.asc())\
        .first()

    last_reading = db.query(SensorReading)\
        .filter(SensorReading.device_id == device_id)\
        .order_by(SensorReading.timestamp.desc())\
        .first()

    # Calculate uptime
    uptime_hours = None
    if first_reading and first_reading[0]:
        uptime_delta = now - first_reading[0]
        uptime_hours = round(uptime_delta.total_seconds() / 3600, 2)

    # Average interval between readings
    avg_interval_minutes = None
    if total_readings and total_readings > 1 and uptime_hours:
        avg_interval_minutes = round((uptime_hours * 60) / total_readings, 2)

    # Average quality score
    avg_quality = db.query(func.avg(SensorReading.quality_score))\
        .filter(SensorReading.device_id == device_id)\
        .scalar()

    avg_quality = round(avg_quality, 3) if avg_quality else None

    # Extract last metrics from payload
    last_rssi = None
    last_battery = None
    last_temp = None
    last_humidity = None

    if last_reading and last_reading.data_payload:
        payload = last_reading.data_payload
        last_rssi = payload.get('rssi_dbm')
        last_battery = payload.get('battery_v')
        last_temp = payload.get('temp_c')
        last_humidity = payload.get('humidity_pct')

    # Alerts triggered in last 24h
    alerts_24h = db.query(func.count(AlertHistory.id))\
        .filter(
            AlertHistory.device_id == device_id,
            AlertHistory.triggered_at >= now - timedelta(hours=24)
        )\
        .scalar()

    return {
        "device_id": device_id,
        "device_name": device.name,
        "device_eui": device.device_eui,
        "status": status,
        "last_seen": device.last_seen_at.isoformat() if device.last_seen_at else None,
        "uptime_hours": uptime_hours,
        "total_readings": total_readings,
        "avg_interval_minutes": avg_interval_minutes,
        "avg_quality_score": avg_quality,
        "last_rssi_dbm": last_rssi,
        "last_battery_v": last_battery,
        "last_temp_c": last_temp,
        "last_humidity_pct": last_humidity,
        "alerts_triggered_24h": alerts_24h,
        "firmware_version": device.firmware_version,
        "created_at": device.created_at.isoformat()
    }


@router.post("/heartbeat", response_model=DeviceHeartbeatResponse, status_code=status.HTTP_200_OK, summary="Heartbeat de device")
def device_heartbeat(
    heartbeat_data: DeviceHeartbeat,
    db: Session = Depends(get_db)
):
    """
    Endpoint de heartbeat para dispositivos ESP32.

    **Propósito:**
    Permite a los ESP32 reportar que están vivos aunque no tengan sensores
    conectados o no estén enviando readings. Actualiza el campo `last_seen_at`
    y opcionalmente `extra_data` y `firmware_version`.

    **Casos de uso:**
    1. ESP32 recién provisionado sin sensores conectados
    2. Device en mantenimiento que no envía readings
    3. Monitoreo de conectividad WiFi
    4. Actualización de metadata del sistema (RSSI, heap, uptime)

    **Frecuencia recomendada:**
    - Si NO hay sensores: Cada 1-5 minutos
    - Si HAY sensores: No es necesario (readings ya actualizan last_seen_at)

    **NOTA:**
    Este endpoint NO requiere autenticación para simplificar el firmware.
    En producción se podría agregar validación de X-API-Key header.

    Args:
        heartbeat_data: Datos del heartbeat (device_eui, firmware_version, metadata)
        db: Sesión de base de datos

    Returns:
        DeviceHeartbeatResponse: Confirmación del heartbeat con estado del device

    Raises:
        HTTPException 404: Si el device con ese EUI no existe

    Example Request:
        ```json
        {
            "device_eui": "ESP32_LAB_001",
            "firmware_version": "1.2.0",
            "metadata": {
                "rssi_dbm": -65,
                "free_heap_bytes": 245000,
                "uptime_sec": 3600,
                "wifi_ssid": "MiWiFi_5G",
                "ip_address": "192.168.1.150"
            }
        }
        ```

    Example Response:
        ```json
        {
            "device_id": 5,
            "device_eui": "ESP32_LAB_001",
            "last_seen_at": "2025-10-24T01:30:00.000000",
            "is_online": true,
            "message": "Heartbeat recibido correctamente"
        }
        ```
    """
    from datetime import datetime

    # Buscar device por EUI
    device = db.query(Device).filter(Device.device_eui == heartbeat_data.device_eui).first()

    if not device:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Device con EUI '{heartbeat_data.device_eui}' no encontrado. Debe crear el device primero."
        )

    # Actualizar last_seen_at (timestamp del heartbeat)
    device.last_seen_at = datetime.utcnow()

    # Actualizar firmware_version si se provee
    if heartbeat_data.firmware_version:
        device.firmware_version = heartbeat_data.firmware_version

    # Actualizar/merge metadata en extra_data si se provee
    if heartbeat_data.metadata:
        if device.extra_data is None:
            device.extra_data = {}

        # Merge metadata con extra_data existente
        # Mantener claves anteriores y agregar/actualizar nuevas
        device.extra_data.update(heartbeat_data.metadata)

        # Agregar timestamp del heartbeat a metadata
        device.extra_data["last_heartbeat_at"] = datetime.utcnow().isoformat()

        # Marcar como modificado para que SQLAlchemy lo detecte (JSONB inmutabilidad)
        from sqlalchemy.orm.attributes import flag_modified
        flag_modified(device, "extra_data")

    # Commit cambios
    db.commit()
    db.refresh(device)

    # Emitir evento WebSocket de status update
    try:
        import asyncio
        from app.services.websocket_service import emit_device_status
        loop = asyncio.new_event_loop()
        loop.run_until_complete(emit_device_status(device.id, {
            "device_eui": device.device_eui,
            "is_online": device.is_online,
            "last_seen_at": device.last_seen_at.isoformat() if device.last_seen_at else None,
            "firmware_version": device.firmware_version,
        }))
        loop.close()
    except Exception:
        pass  # WebSocket emit no es crítico

    # Construir respuesta
    response = DeviceHeartbeatResponse(
        device_id=device.id,
        device_eui=device.device_eui,
        last_seen_at=device.last_seen_at,
        is_online=device.is_online,
        message="Heartbeat recibido correctamente"
    )

    return response


@router.get("/health/dashboard", response_model=DeviceHealthDashboard, summary="Dashboard de salud de devices")
def get_devices_health_dashboard(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Obtiene dashboard completo de salud de todos los devices accesibles por el usuario.

    **Métricas incluidas:**
    - Total de devices, online/offline
    - RSSI promedio, señal débil
    - Uptime, memoria, batería
    - Total de readings, readings últimas 24h
    - Alertas activas por device

    **RBAC aplicado:**
    - super_admin: Ve todos los devices
    - otros roles: Solo devices de sus allowed_location_ids

    **Optimización:**
    - Usa eager loading con joinedload para evitar N+1 queries
    - Agrega readings y alertas en queries separadas pero eficientes
    - Reduce queries de O(N) a O(1) para conteos
    - **Caché Redis con TTL de 60 segundos** (datos frescos pero reduce carga DB)

    Args:
        db: Sesión de base de datos
        current_user: Usuario autenticado

    Returns:
        DeviceHealthDashboard: Dashboard con métricas de todos los devices
    """
    from datetime import datetime, timedelta
    from app.models.sensor_reading import SensorReading
    from app.models.alert import AlertHistory
    from app.models.asset import Asset
    from app.models.location import Location
    from sqlalchemy import func
    from sqlalchemy.orm import joinedload
    from app.services.cache_service import cache, CacheKeys, CacheTTL

    # Intentar obtener del caché primero
    cache_key = f"{CacheKeys.health_dashboard()}:user:{current_user.id}"
    cached_data = cache.get(cache_key)

    if cached_data:
        # Cache hit: retornar datos cacheados
        return DeviceHealthDashboard(**cached_data)

    # Aplicar filtro RBAC con eager loading de asset y location
    devices_query = filter_devices_by_permission(current_user, db)
    devices_query = devices_query.options(
        joinedload(Device.asset).joinedload(Asset.location)
    )
    devices = devices_query.all()

    if not devices:
        # No hay devices, retornar dashboard vacío
        return DeviceHealthDashboard(
            total_devices=0,
            devices_online=0,
            devices_offline=0,
            devices_with_alerts=0,
            avg_rssi=None,
            devices_poor_signal=0,
            devices=[]
        )

    # Extraer device_ids para queries agregadas
    device_ids = [d.id for d in devices]

    # OPTIMIZACIÓN: Hacer queries agregadas en una sola vez (elimina N+1)
    # Query 1: Contar total de readings por device
    readings_total_query = db.query(
        SensorReading.device_id,
        func.count(SensorReading.id).label('total_count')
    ).filter(
        SensorReading.device_id.in_(device_ids)
    ).group_by(SensorReading.device_id).all()

    readings_total_map = {device_id: count for device_id, count in readings_total_query}

    # Query 2: Contar readings de últimas 24h por device
    yesterday = datetime.utcnow() - timedelta(hours=24)
    readings_24h_query = db.query(
        SensorReading.device_id,
        func.count(SensorReading.id).label('count_24h')
    ).filter(
        SensorReading.device_id.in_(device_ids),
        SensorReading.timestamp >= yesterday
    ).group_by(SensorReading.device_id).all()

    readings_24h_map = {device_id: count for device_id, count in readings_24h_query}

    # Query 3: Contar alertas activas por device
    alerts_query = db.query(
        AlertHistory.device_id,
        func.count(AlertHistory.id).label('alerts_count')
    ).filter(
        AlertHistory.device_id.in_(device_ids),
        AlertHistory.acknowledged_by.is_(None)
    ).group_by(AlertHistory.device_id).all()

    alerts_map = {device_id: count for device_id, count in alerts_query}

    # Inicializar estadísticas generales
    total_devices = len(devices)
    devices_online = 0
    devices_offline = 0
    devices_with_alerts = 0
    devices_poor_signal = 0
    rssi_values = []

    # Lista de métricas por device
    device_metrics_list = []

    # Procesar cada device (ahora sin queries adicionales)
    for device in devices:
        # Determinar si está online (reportó en últimos 10 minutos)
        is_online = False
        if device.last_seen_at:
            time_diff = datetime.utcnow() - device.last_seen_at
            is_online = time_diff < timedelta(minutes=10)

        if is_online:
            devices_online += 1
        else:
            devices_offline += 1

        # Extraer metadata del extra_data JSON
        rssi_dbm = None
        wifi_quality = None
        free_heap_bytes = None
        battery_mv = None
        battery_percentage = None
        uptime_hours = None

        if device.extra_data:
            rssi_dbm = device.extra_data.get("rssi_dbm")
            free_heap_bytes = device.extra_data.get("free_heap_bytes") or device.extra_data.get("free_heap")
            battery_mv = device.extra_data.get("battery_mv")

            # Calcular uptime si existe uptime_sec o uptime_ms
            uptime_sec = device.extra_data.get("uptime_sec") or device.extra_data.get("uptime_ms", 0) / 1000
            if uptime_sec:
                uptime_hours = round(uptime_sec / 3600, 2)

            # Calcular calidad WiFi según RSSI
            if rssi_dbm:
                rssi_values.append(rssi_dbm)
                if rssi_dbm >= -50:
                    wifi_quality = "Excellent"
                elif rssi_dbm >= -60:
                    wifi_quality = "Good"
                elif rssi_dbm >= -70:
                    wifi_quality = "Fair"
                elif rssi_dbm >= -80:
                    wifi_quality = "Poor"
                else:
                    wifi_quality = "Very Poor"
                    devices_poor_signal += 1

            # Calcular porcentaje de batería (estimación lineal 3000-4200 mV)
            if battery_mv:
                if battery_mv >= 4200:
                    battery_percentage = 100
                elif battery_mv <= 3000:
                    battery_percentage = 0
                else:
                    battery_percentage = int(((battery_mv - 3000) / 1200) * 100)

        # OPTIMIZACIÓN: Obtener datos de los mapas pre-calculados (sin queries adicionales)
        total_readings = readings_total_map.get(device.id, 0)
        readings_last_24h = readings_24h_map.get(device.id, 0)
        active_alerts_count = alerts_map.get(device.id, 0)

        # Calcular promedio de readings por día
        if device.created_at:
            days_since_creation = (datetime.utcnow() - device.created_at).days or 1
            avg_readings_per_day = round(total_readings / days_since_creation, 2)
        else:
            avg_readings_per_day = 0.0

        if active_alerts_count > 0:
            devices_with_alerts += 1

        # OPTIMIZACIÓN: asset y location ya están cargados por joinedload (no lazy loading)
        location_name = None
        asset_name = None
        if device.asset:
            asset_name = device.asset.name
            if device.asset.location:
                location_name = device.asset.location.name

        # Construir métricas del device
        device_metrics = DeviceHealthMetrics(
            device_id=device.id,
            device_eui=device.device_eui,
            name=device.name,
            status=device.status,
            is_online=is_online,
            last_seen_at=device.last_seen_at,
            created_at=device.created_at,
            uptime_hours=uptime_hours,
            rssi_dbm=rssi_dbm,
            wifi_quality=wifi_quality,
            free_heap_bytes=free_heap_bytes,
            battery_mv=battery_mv,
            battery_percentage=battery_percentage,
            firmware_version=device.firmware_version,
            total_readings=total_readings,
            readings_last_24h=readings_last_24h,
            avg_readings_per_day=avg_readings_per_day,
            active_alerts_count=active_alerts_count,
            location_name=location_name,
            asset_name=asset_name
        )

        device_metrics_list.append(device_metrics)

    # Calcular RSSI promedio
    avg_rssi = None
    if rssi_values:
        avg_rssi = round(sum(rssi_values) / len(rssi_values), 1)

    # Construir dashboard
    dashboard = DeviceHealthDashboard(
        total_devices=total_devices,
        devices_online=devices_online,
        devices_offline=devices_offline,
        devices_with_alerts=devices_with_alerts,
        avg_rssi=avg_rssi,
        devices_poor_signal=devices_poor_signal,
        devices=device_metrics_list
    )

    # Guardar en caché (60 segundos)
    cache.set(cache_key, dashboard.model_dump(), ttl=CacheTTL.HEALTH_DASHBOARD)

    return dashboard
