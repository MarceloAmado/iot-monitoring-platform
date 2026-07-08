# Simulador ESP32

## 📌 Descripción

Simulador de ESP32 en Python que permite testear el backend sin necesidad de hardware físico. Genera datos realistas de sensores y los envía al API REST.

## 🎯 Características

- ✅ Genera datos simulados de temperatura, humedad, RSSI, uptime
- ✅ Envío HTTP POST al backend con la misma estructura que el ESP32 real
- ✅ Soporte para API Key authentication
- ✅ Estadísticas de envíos (éxito/fallos)
- ✅ Configurable vía argumentos de línea de comandos
- ✅ Útil para testing del backend sin hardware

## 🚀 Instalación

### Requisitos

- Python 3.8+
- Librería `requests`

### Setup

```bash
# Instalar dependencias
pip install requests

# O usando el requirements del backend (ya incluye requests)
cd backend
pip install -r requirements.txt
```

## 📖 Uso

### Uso Básico

```bash
# Ejecutar con configuración por defecto
python esp32_simulator.py
```

**Configuración por defecto:**
- Device EUI: `ESP32_SIMULATOR_001`
- API URL: `http://localhost:8000/api/v1`
- API Key: `esp32_device_key_change_me`
- Intervalo: 60 segundos

### Uso Avanzado

```bash
# Personalizar todos los parámetros
python esp32_simulator.py \
  --device ESP32_LAB_002 \
  --url http://192.168.1.100:8000/api/v1 \
  --key mi_api_key_secreta \
  --interval 10 \
  --iterations 20
```

### Parámetros Disponibles

| Parámetro | Descripción | Default |
|-----------|-------------|---------|
| `--device` | Device EUI único | `ESP32_SIMULATOR_001` |
| `--url` | URL base del API | `http://localhost:8000/api/v1` |
| `--key` | API Key para autenticación | `esp32_device_key_change_me` |
| `--interval` | Intervalo de envío (seg) | `60` |
| `--iterations` | Máximo de iteraciones | `None` (infinito) |

### Ejemplos

#### Ejemplo 1: Testing rápido (10 lecturas cada 5 segundos)

```bash
python esp32_simulator.py --interval 5 --iterations 10
```

#### Ejemplo 2: Simulación de múltiples dispositivos

Terminal 1:
```bash
python esp32_simulator.py --device ESP32_LAB_001 --interval 30
```

Terminal 2:
```bash
python esp32_simulator.py --device ESP32_LAB_002 --interval 45
```

Terminal 3:
```bash
python esp32_simulator.py --device ESP32_WAREHOUSE_001 --interval 60
```

#### Ejemplo 3: Testing de backend remoto

```bash
python esp32_simulator.py \
  --device ESP32_PROD_001 \
  --url http://192.168.1.50:8000/api/v1 \
  --key prod_api_key_xyz123 \
  --interval 300
```

## 📊 Output Esperado

```
============================================================
ESP32 SIMULATOR
============================================================
Device EUI: ESP32_SIMULATOR_001
API URL: http://localhost:8000/api/v1
Interval: 60 seconds
============================================================

[14:30:15] Enviando reading #1
Temperatura: 24.75°C
Humedad: 58.3%
RSSI: -55 dBm
✓ Enviado exitosamente
  - Reading ID: 123
  - Quality Score: 0.95

Próxima lectura en 60 segundos...

[14:31:15] Enviando reading #2
Temperatura: 25.20°C
Humedad: 59.1%
RSSI: -52 dBm
✓ Enviado exitosamente
  - Reading ID: 124
  - Quality Score: 0.95

Próxima lectura en 60 segundos...

^C
⚠ Simulador detenido por el usuario (Ctrl+C)

============================================================
ESTADÍSTICAS
============================================================
Total de requests: 2
Exitosos: 2
Fallidos: 0
Tasa de éxito: 100.0%
============================================================
```

## 🔍 Datos Generados

### Estructura del JSON Enviado

```json
{
  "device_eui": "ESP32_SIMULATOR_001",
  "data_payload": {
    "temp_c": 24.75,
    "humidity_pct": 58.3,
    "rssi_dbm": -55,
    "uptime_sec": 60,
    "free_heap_bytes": 235421,
    "battery_v": 3.68
  }
}
```

### Lógica de Generación

| Variable | Lógica |
|----------|--------|
| **temp_c** | Base 25°C ± 2°C de variación aleatoria |
| **humidity_pct** | Base 60% ± 5% de variación aleatoria |
| **rssi_dbm** | Rango -70 a -40 dBm (random) |
| **uptime_sec** | Incrementa con cada lectura (iterations * interval) |
| **free_heap_bytes** | Rango 200,000 - 250,000 bytes (random) |
| **battery_v** | Simula descarga: 3.7V - 0.2V por día |

## 🐛 Troubleshooting

### Error: "No se pudo conectar al backend"

**Causa**: El backend no está corriendo o la URL es incorrecta

**Solución**:
1. Verificar que el backend esté corriendo:
   ```bash
   docker-compose ps
   ```

2. Verificar que el endpoint esté accesible:
   ```bash
   curl http://localhost:8000/api/v1/health
   ```

3. Verificar la URL del simulador

### Error: "Error HTTP 401"

**Causa**: API Key incorrecta o no configurada

**Solución**:
1. Verificar que el device existe en la base de datos
2. Verificar que la API Key es correcta
3. En desarrollo, usar la API Key por defecto: `esp32_device_key_change_me`

### Error: "Error HTTP 404"

**Causa**: Endpoint no encontrado

**Solución**:
1. Verificar que la URL base es correcta (debe terminar en `/api/v1`)
2. Verificar que el backend tenga el endpoint `/readings`

## 🧪 Testing

### Test 1: Verificar que el backend acepta readings

```bash
# Enviar 1 reading
python esp32_simulator.py --iterations 1

# Verificar en el backend
curl http://localhost:8000/api/v1/readings | jq
```

### Test 2: Stress test (múltiples readings rápidos)

```bash
# 100 readings cada 2 segundos
python esp32_simulator.py --interval 2 --iterations 100
```

### Test 3: Verificar persistencia en DB

```bash
# Enviar varios readings
python esp32_simulator.py --interval 5 --iterations 5

# Verificar en PostgreSQL
docker exec -it iot_postgres psql -U iot_admin -d iot_monitoring \
  -c "SELECT COUNT(*) FROM sensor_readings WHERE device_id = (SELECT id FROM devices WHERE device_eui = 'ESP32_SIMULATOR_001');"
```

## 📝 Notas

- **No reemplaza el ESP32 real**: Este simulador es solo para testing del backend
- **Datos sintéticos**: Los valores son simulados, no reflejan condiciones reales
- **Útil para desarrollo**: Permite desarrollar y testear sin hardware
- **Compatibilidad**: Genera el mismo formato JSON que el ESP32 real

## 🚀 Próximas Mejoras

- [ ] Simular errores de sensor (valores -999)
- [ ] Simular pérdida de conexión WiFi
- [ ] Configuración vía archivo JSON
- [ ] Modo replay (repetir readings guardados)
- [ ] GUI opcional con Streamlit

---

**Última actualización**: 2025-10-17
**Versión**: 1.0.0
