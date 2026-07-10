# Sistema de Monitoreo IoT

**[English version →](README.md)**

[![CI](https://github.com/MarceloAmado/iot-monitoring-platform/actions/workflows/ci.yml/badge.svg)](https://github.com/MarceloAmado/iot-monitoring-platform/actions/workflows/ci.yml)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.104+-009688?logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com)
[![PostgreSQL](https://img.shields.io/badge/PostgreSQL-15+-336791?logo=postgresql&logoColor=white)](https://www.postgresql.org)
[![React](https://img.shields.io/badge/React-18+-61DAFB?logo=react&logoColor=black)](https://react.dev)
[![Python](https://img.shields.io/badge/Python-3.11+-3776AB?logo=python&logoColor=white)](https://www.python.org)
[![Tests](https://img.shields.io/badge/Tests-235%20backend%20%2B%2012%20frontend-brightgreen)](backend/tests/)
[![License](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)

> Plataforma SCADA-lite modular y escalable para monitoreo en tiempo real de sensores IoT con alertas automáticas, RBAC por ubicación y visualización dinámica de datos.

## Capturas de Pantalla

![Dashboard](docs/screenshots/dashboard.png)

| Detalle de dispositivo en tiempo real | Reglas e historial de alertas |
|---|---|
| ![Detalle de dispositivo](docs/screenshots/device-detail.png) | ![Alertas](docs/screenshots/alerts.png) |

| Gestión de firmware OTA | Ubicaciones y activos |
|---|---|
| ![Firmware OTA](docs/screenshots/firmware-ota.png) | ![Ubicaciones](docs/screenshots/locations.png) |

## Descripcion

Sistema genérico y reutilizable para monitoreo de sensores en entornos industriales, hospitalarios, comerciales y residenciales. Arquitectura moderna basada en FastAPI + React + PostgreSQL + Redis + MQTT + ESP32.

### Características Principales

- **Autenticación JWT + RBAC** - 4 roles (super_admin, service_admin, technician, guest) con permisos por ubicación
- **Gestión de Usuarios** - CRUD completo con filtros, estadísticas, activar/desactivar, archivar, reset password
- **Ubicaciones y Activos** - Jerarquía Grupos > Ubicaciones > Activos con RBAC integrado
- **Visualización Dinámica** - Gráficos que se auto-generan según las variables del sensor (auto-discovery)
- **Alertas Configurables** - 6 tipos de reglas con notificaciones Email/Telegram/Webhook (evaluación en background)
- **Health Monitoring** - Dashboard de salud con métricas de dispositivos en tiempo real
- **Cache Redis** - Cache inteligente para queries frecuentes con invalidación automática
- **MQTT Broker** - Mosquitto con autenticación y ACL para telemetría en tiempo real
- **Exportación de Datos** - Descarga de readings a CSV con columnas dinámicas
- **Catálogo de Sensores** - Gestión de sensores personalizados con calibración y validaciones
- **Email Transaccional** - Templates HTML para password reset y welcome emails
- **API REST Completa** - 50+ endpoints con documentación automática Swagger UI
- **IoT Ready** - Endpoint optimizado para ESP32 con autenticación por API Key
- **OTA Updates** - Actualización de firmware ESP32 (ArduinoOTA local + backend HTTP)
- **Audit Log** - Registro de acciones con trazabilidad completa
- **JSONB Flexible** - Base de datos que se adapta a cualquier sensor sin migraciones
- **Docker Compose** - 5 servicios desplegados en un solo comando

## Arquitectura

```
┌─────────────┐     ┌──────────────┐     ┌──────────────┐
│   ESP32     │────▶│   FastAPI    │────▶│ PostgreSQL   │
│  (Sensores) │ HTTP│   Backend    │ SQL │   + JSONB    │
└─────────────┘     └──────┬───────┘     └──────────────┘
       │                   │
       │ MQTT        ┌─────┴─────┐
       ▼             │           │
┌─────────────┐  ┌───▼───┐  ┌───▼───┐
│  Mosquitto  │  │ Redis │  │ React │
│   Broker    │  │ Cache │  │ Front │
└─────────────┘  └───────┘  └───────┘
```

**Docker Compose:** 5 servicios — PostgreSQL 15, Redis 7, Mosquitto 2.0, Backend (FastAPI), Frontend (Nginx)

### Modelo de Datos

```
location_groups (Organizaciones)
    ↓ 1:N
locations (Áreas/Zonas)
    ↓ 1:N
assets (Equipos Físicos)
    ↓ 1:N
devices (Hardware ESP32)
    ↓ 1:N
sensor_readings (Mediciones JSONB)
```

## Inicio Rápido

### Prerrequisitos

- Docker & Docker Compose 24+
- Python 3.11+ (para desarrollo local)
- Node.js 18+ (para desarrollo frontend)
- Git

### Instalación

```bash
# 1. Clonar repositorio
git clone https://github.com/MarceloAmado/iot-monitoring-platform.git
cd monitoreo

# 2. Crear archivo .env
cp .env.example .env
# Editar .env con tus credenciales

# 3. Levantar con Docker Compose
docker-compose up -d

# 4. Ejecutar migraciones
docker exec -it iot_backend alembic upgrade head

# 5. Cargar datos iniciales
docker exec -it iot_backend python scripts/seed.py
```

### Acceso

- **Frontend:** http://localhost:3000
- **API Backend:** http://localhost:8000
- **Documentación Swagger:** http://localhost:8000/api/v1/docs
- **Producción:** https://iot.example.com

**Credenciales de prueba:**
- Email: `admin@iot-monitoring.com`
- Password: `admin123`

## Guía de Uso

### Roles y Permisos

| Rol | Permisos | Descripción |
|-----|----------|-------------|
| **Super Admin** | Acceso completo | Ve y gestiona todo el sistema |
| **Service Admin** | CRUD en sus locations | Administra solo sus áreas asignadas |
| **Technician** | Solo lectura | Ve datos pero no puede modificar |
| **Guest** | Dashboard público | Acceso limitado a visualización básica |

### Flujo de Trabajo

1. **Login** - Accede al frontend, el sistema redirige al Dashboard según tu rol
2. **Dashboard** - Vista general de todos los devices accesibles con estados (Activo/Inactivo/Mantenimiento/Error)
3. **Detalle de Device** - Gráficos dinámicos, selector de rango temporal, tabla de lecturas, exportación CSV
4. **Alertas** (Admins) - Configurar reglas con 6 tipos de chequeo, cooldown y notificaciones multi-canal
5. **Salud** - Métricas en tiempo real: devices online/offline, señal, batería
6. **Ubicaciones** (Admins) - Gestionar grupos, ubicaciones y activos

## Documentación de la API

### Autenticación

```http
POST /api/v1/auth/login
GET  /api/v1/auth/me
POST /api/v1/auth/logout
POST /api/v1/auth/forgot-password
POST /api/v1/auth/reset-password
```

### Devices

```http
GET    /api/v1/devices                    # Listar (RBAC)
GET    /api/v1/devices/{id}               # Detalle
GET    /api/v1/devices/{id}/schema        # Auto-discovery de variables
POST   /api/v1/devices                    # Crear (admin)
PATCH  /api/v1/devices/{id}               # Actualizar (admin)
DELETE /api/v1/devices/{id}               # Eliminar (super_admin)
POST   /api/v1/devices/heartbeat          # Heartbeat ESP32
GET    /api/v1/devices/health/summary     # Resumen de salud
GET    /api/v1/devices/health/dashboard   # Dashboard de salud
GET    /api/v1/devices/{id}/health        # Salud individual
```

### Sensor Readings (ESP32)

```http
POST /api/v1/readings                     # Crear lectura (API Key)
GET  /api/v1/readings                     # Listar con filtros
GET  /api/v1/readings/{id}               # Detalle
GET  /api/v1/readings/export             # Exportar CSV
```

**Ejemplo desde ESP32:**

```http
POST /api/v1/readings
Content-Type: application/json
X-API-Key: {device_api_key}
X-Device-EUI: ESP32_LAB_001

{
  "device_eui": "ESP32_LAB_001",
  "data_payload": {
    "temp_c": 25.5,
    "humidity_pct": 62.3,
    "battery_mv": 3750
  }
}
```

### Locations y Assets

```http
# Location Groups
GET/POST   /api/v1/location-groups
PATCH/DEL  /api/v1/location-groups/{id}

# Locations
GET/POST   /api/v1/locations
PATCH/DEL  /api/v1/locations/{id}

# Assets
GET/POST   /api/v1/assets
PATCH/DEL  /api/v1/assets/{id}
```

### Alertas

```http
GET/POST   /api/v1/alerts/rules
PATCH/DEL  /api/v1/alerts/rules/{id}
GET        /api/v1/alerts/history
```

### Firmware OTA

```http
GET    /api/v1/firmware                   # Listar versiones
POST   /api/v1/firmware/upload            # Subir firmware
GET    /api/v1/firmware/latest            # Última versión
GET    /api/v1/firmware/{id}/download     # Descargar binario
```

### Otros

```http
GET  /api/v1/users                        # CRUD usuarios (admin)
GET  /api/v1/audit                        # Logs de auditoría
GET  /api/v1/health                       # Health check (DB + Redis)
```

## Stack Tecnológico

### Backend
- **FastAPI** 0.104+ - Framework web async
- **SQLAlchemy** 2.0+ - ORM con JSONB support
- **PostgreSQL** 15+ - Base de datos con índices de performance
- **Redis** 7+ - Cache inteligente con invalidación
- **Mosquitto** 2.0 - Broker MQTT con autenticación
- **Alembic** 1.12+ - Migraciones de base de datos
- **Pydantic** 2.5+ - Validación de datos
- **APScheduler** - Jobs periódicos (detección offline)

### Frontend
- **React** 18+ con TypeScript
- **Vite** - Build tool
- **TanStack Query** - Server state management
- **Recharts** - Gráficos dinámicos
- **Tailwind CSS** - Estilos (IdeaMakers Design System)
- **React Router** v6 - Navegación SPA

### Hardware
- **ESP32** - Microcontrolador WiFi
- **DS18B20** - Temperatura
- **DHT22** - Temperatura + Humedad
- **JSN-SR04T** - Distancia ultrasónica
- **MPX5700** - Presión (0-700 kPa)

## Estructura del Proyecto

```
Idea_IoT/
├── backend/
│   ├── app/
│   │   ├── core/           # Config, DB, Security, Permissions
│   │   ├── models/         # Modelos SQLAlchemy (10+ tablas)
│   │   ├── schemas/        # Schemas Pydantic
│   │   ├── api/v1/         # Endpoints REST (9 routers)
│   │   ├── services/       # Servicios (alertas, cache, MQTT, audit)
│   │   └── main.py         # Entry point
│   ├── alembic/            # Migraciones (7 aplicadas)
│   ├── mosquitto/          # Config Mosquitto (ACL + passwords)
│   ├── scripts/            # Scripts (seed, backup, restore)
│   └── tests/              # Tests pytest (8 archivos, 111 tests)
├── frontend/
│   ├── src/
│   │   ├── components/     # Componentes reutilizables (Design System IM*)
│   │   ├── pages/          # Páginas (Dashboard, Devices, Alerts, etc.)
│   │   ├── services/       # API clients (Axios)
│   │   ├── hooks/          # Custom hooks (useAuth, usePermissions)
│   │   └── types/          # TypeScript definitions
│   └── public/
├── firmware/
│   └── esp32-sensor/       # Código ESP32 (PlatformIO)
│       └── src/
│           ├── sensors/    # DS18B20, DHT22, JSN-SR04T, MPX5700
│           └── utils/      # WiFiManager, APIClient, OTAUpdate
├── docs/claude/            # Documentación de desarrollo
├── docker-compose.yml      # 5 servicios
└── .env.example
```

## Seguridad

- Passwords hasheadas con bcrypt (cost factor 12)
- JWT con expiración configurable
- RBAC con permisos por ubicación
- API Keys encriptadas (Fernet) para dispositivos ESP32
- Validación de inputs con Pydantic
- SQL Injection protection (SQLAlchemy ORM)
- CORS configurado
- MQTT con autenticación y ACL
- Audit logging de acciones administrativas

## Testing

```bash
# Ejecutar todos los tests (235 tests backend)
docker exec -it iot_backend pytest -v

# Con cobertura
docker exec -it iot_backend pytest --cov=app --cov-report=html

# Test específico
docker exec -it iot_backend pytest tests/test_auth.py -v
docker exec -it iot_backend pytest tests/test_readings.py -v
docker exec -it iot_backend pytest tests/test_devices.py -v
```

### Cobertura de Tests

| Área | Tests | Estado |
|------|-------|--------|
| Auth + JWT | 17 | Passing |
| Readings + Export (X-API-Key) | 26 | Passing |
| Devices CRUD | 25 | Passing |
| Firmware OTA | 22 | Passing |
| Cache Redis | 33 | Passing |
| RBAC + Locations | 11 | Passing |
| Location Groups + Locations | 17 | Passing |
| Assets CRUD | 10 | Passing |
| Users CRUD + lifecycle | 13 | Passing |
| Sensor Catalog | 13 | Passing |
| Audit Log | 10 | Passing |
| Alert Evaluation | 12 | Passing |
| Notifications | 12 | Passing |
| Alert Checker Job | 6 | Passing |
| MQTT Auth | 6 | Passing |
| **Total backend** | **235** | **Passing** |
| **Frontend (vitest)** | **12** | **Passing** |

Frontend: `npm test` (vitest + testing-library), `npm run typecheck`, `npm run lint`.
CI: GitHub Actions corre backend (pytest + PostgreSQL + Redis), frontend (lint/typecheck/tests/build) y firmware (PlatformIO) en cada push.

## Comandos Útiles

```bash
# Ver logs del backend
docker-compose logs -f backend

# Recrear base de datos
docker-compose down -v
docker-compose up -d

# Ejecutar migraciones
docker exec -it iot_backend alembic upgrade head

# Acceder a PostgreSQL
docker exec -it iot_postgres psql -U iot_admin -d iot_monitoring

# Generar nueva migración
docker exec -it iot_backend alembic revision --autogenerate -m "descripcion"

# Ver Redis cache
docker exec -it iot_redis redis-cli KEYS "*"

# Ver logs MQTT
docker-compose logs -f mosquitto
```

## Estado del Proyecto

### Sprint 1-4: Core System (Completado)

Backend MVP, Frontend completo, Firmware ESP32 con 4 sensores, Sistema RBAC, Alertas multi-canal, Health Dashboard, Export CSV, OTA local (ArduinoOTA).

### Sprint 5: Login UX (Completado)

Password recovery flow, show/hide password toggle.

### Sprint 6: Email + Sensores (Completado)

Email transaccional con templates HTML, Catálogo de sensores con calibración.

### Sprint 7: UX/UI Redesign (Completado)

Rediseño completo con IdeaMakers Design System (componentes IM*).

### Sprint 8: RBAC + Cache + Locations (Completado)

- Cache Redis con invalidación automática
- Health dashboard consolidado
- CRUD Locations/Groups/Assets con RBAC
- Background tasks para evaluación de alertas
- Deploy a producción

### Post-Sprint 8 (feb 2026, Completado)

- OTA HTTP desde backend (el ESP32 se actualiza remotamente, con verificación MD5 y rollback)
- UI de gestión de firmware (Firmware.tsx)
- WebSocket para updates en tiempo real (Socket.IO en Dashboard y DeviceDetail)
- Sensor analógico genérico en firmware (AnalogSensor.h)
- Auditoría filtrada por ubicación
- Test suite ampliada: 166 tests passing (firmware, cache, devices)

### Pendiente (plan de completado 2026-07-06 — ver docs/claude/PLAN_TRABAJO.md)

- [ ] Corrección de bugs de auditoría (export de readings, migración firmware_versions)
- [ ] Features menores: persistencia de Settings, campana de notificaciones, edición de Locations
- [ ] CI/CD con GitHub Actions + tests de frontend
- [ ] Cliente MQTT en firmware ESP32 + notificaciones push
- [ ] Validación 48hs con hardware real + video demo

## Contribución

Este es un proyecto de portafolio. Pull requests son bienvenidos.

1. Fork el proyecto
2. Crea tu feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit tus cambios (`git commit -m 'Add: nueva funcionalidad'`)
4. Push al branch (`git push origin feature/AmazingFeature`)
5. Abre un Pull Request

## Licencia

Este proyecto está bajo la Licencia MIT. Ver `LICENSE` para más detalles.

## Autor

**Marcelo Amado**

- GitHub: [@MarceloAmado](https://github.com/MarceloAmado)

## Agradecimientos

- [FastAPI](https://fastapi.tiangolo.com) por el excelente framework
- [PostgreSQL](https://www.postgresql.org) por el soporte JSONB
- Comunidad ESP32 por el ecosistema IoT

---

Si te gustó el proyecto, dale una estrella en GitHub!
