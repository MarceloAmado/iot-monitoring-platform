# 🚀 Guía Rápida: Actualizar Firmware v1.2.0 con Heartbeat vía OTA

**Fecha:** 2025-10-23
**Versión Nueva:** 1.2.0 (Heartbeat Support)
**ESP32:** ESP32_20251023_2224_37D0
**WiFi:** MARCELO / queso123
**Backend IP:** YOUR_SERVER_IP:8000

---

## 📋 Cambios en esta versión

✅ **Funcionalidad Heartbeat agregada:**
- El ESP32 ahora envía heartbeats cada 60 segundos si NO tiene sensores
- Actualiza `last_seen_at` en el backend automáticamente
- Envía metadata: RSSI, WiFi SSID, IP, Free Heap, Uptime
- El device aparecerá como "Online" en el dashboard

✅ **Archivos modificados:**
- `src/main.cpp` - Agregada función `sendHeartbeat()` y lógica en loop
- `src/network/APIClient.h` - Métodos `sendHeartbeat()` y `sendHeartbeatWithRetry()`
- `src/config.h` - IP del backend actualizada a `YOUR_SERVER_IP`

---

## 🔧 Opción 1: Compilar y Subir vía PlatformIO (RECOMENDADO)

### Paso 1: Abrir el Proyecto en VS Code

1. Abrir VS Code
2. `File → Open Folder`
3. Seleccionar: `e:\Documentos\Marcelo\Trabajos Idea\Python\Idea_IoT\firmware\esp32-sensor`
4. PlatformIO debería detectar el proyecto automáticamente

### Paso 2: Compilar el Firmware

1. Presionar `Ctrl+Shift+P` para abrir Command Palette
2. Escribir: `PlatformIO: Build`
3. Presionar Enter
4. Esperar a que compile (~1-2 minutos)

**Salida esperada:**
```
Building...
Compiling .pio\build\esp32dev\src\main.cpp.o
Linking .pio\build\esp32dev\firmware.elf
Building .pio\build\esp32dev\firmware.bin
========================= [SUCCESS] Took 45.23 seconds =========================
```

### Paso 3: Encontrar la IP del ESP32

**Opción A: Desde el Router**
1. Acceder al router en `http://YOUR_ROUTER_IP`
2. Buscar dispositivos conectados
3. Buscar "ESP32" o la MAC address
4. Anotar la IP (ej: `192.168.1.150`)

**Opción B: Desde el Serial Monitor** (si tienes acceso USB)
1. Conectar ESP32 via USB
2. En VS Code: Click en "Serial Monitor" (barra inferior)
3. Buscar línea: `[WIFI] IP asignada: 192.168.1.XXX`

### Paso 4: Configurar OTA en `platformio.ini`

Editar el archivo `platformio.ini` y **descomentar/agregar** estas líneas:

```ini
[env:esp32dev]
platform = espressif32
board = esp32dev
framework = arduino
monitor_speed = 115200

; Agregar estas líneas para OTA:
upload_protocol = espota
upload_port = 192.168.1.XXX  ; <--- CAMBIAR POR LA IP DE TU ESP32
upload_flags =
    --port=3232
    --auth=CHANGE_ME_OTA_PASSWORD
```

**Importante:** Reemplazar `192.168.1.XXX` por la IP real de tu ESP32.

### Paso 5: Subir Firmware vía OTA

1. En VS Code, presionar `Ctrl+Shift+P`
2. Escribir: `PlatformIO: Upload`
3. Presionar Enter
4. PlatformIO subirá el firmware via WiFi

**Salida esperada:**
```
Uploading .pio\build\esp32dev\firmware.bin
Sending invitation to 192.168.1.150...
Authenticating...OK
Sending firmware (xxx bytes)...
Upload progress: [########################################] 100%
Firmware uploaded successfully!
```

### Paso 6: Verificar en Serial Monitor

Si tienes acceso USB, abrir Serial Monitor para ver los logs:

```
========================================
  SISTEMA DE MONITOREO IoT - ESP32
========================================
Firmware Version: 1.2.0 (Heartbeat Support)
Build Date: Oct 23 2025 22:45:00
========================================

[SETUP] Paso 1: Conectando a WiFi...
[WIFI] Conectando a: MARCELO
[WIFI] ✓ Conectado exitosamente
[WIFI] IP asignada: 192.168.1.150

...

========================================
[HEARTBEAT] Enviando heartbeat al backend
========================================
[API] URL: http://YOUR_SERVER_IP:8000/api/v1/devices/heartbeat
[API] Heartbeat JSON:
{"device_eui":"ESP32_20251023_2224_37D0","firmware_version":"1.2.0","metadata":{"rssi_dbm":-58,"wifi_ssid":"MyWiFi","ip_address":"192.168.1.150","free_heap_bytes":250000,"uptime_sec":120,"sensors_count":0,"sampling_interval_sec":300}}
[API] HTTP Response Code: 200
[API] ✓ Heartbeat enviado exitosamente
[API]   - Device ID: 3
[API]   - Is Online: true
[API]   - Message: Heartbeat recibido correctamente
========================================
```

---

## 🔧 Opción 2: Compilar con Arduino IDE (Alternativa)

### Paso 1: Abrir el Proyecto

1. Abrir Arduino IDE
2. `File → Open`
3. Navegar a: `e:\Documentos\Marcelo\Trabajos Idea\Python\Idea_IoT\firmware\esp32-sensor\src\main.cpp`
4. Abrir el archivo

### Paso 2: Configurar la Placa

1. `Tools → Board → ESP32 Arduino → NodeMCU-32S`
2. `Tools → Upload Speed → 921600`
3. `Tools → Port → Network Port`
4. Seleccionar: `ESP32_20251023_2224_37D0 at 192.168.1.XXX`

**Nota:** Si no aparece "Network Port", significa que OTA no está disponible. Usar USB.

### Paso 3: Subir Firmware

1. Click en "Upload" (ícono de flecha →)
2. Esperar a que compile y suba (~2 minutos)

---

## 🔧 Opción 3: Subir vía USB (Si OTA no funciona)

Si OTA no está disponible o falla, usar USB:

### Paso 1: Conectar ESP32 via USB-C

1. Conectar ESP32 a tu PC via USB-C
2. Verificar puerto COM en Device Manager (ej: COM3)

### Paso 2: Compilar y Subir

**Con PlatformIO:**
1. En `platformio.ini`, comentar las líneas de OTA:
   ```ini
   ; upload_protocol = espota
   ; upload_port = 192.168.1.XXX
   ```
2. `PlatformIO: Upload`

**Con Arduino IDE:**
1. `Tools → Port → COMx` (tu puerto USB)
2. Click en "Upload"

---

## ✅ Verificación Post-Update

### 1. Verificar en el Dashboard

1. Abrir: `http://localhost:3000`
2. Login: `admin@iot-monitoring.com` / `admin123`
3. Ir a "Devices"
4. Buscar: `ESP32_20251023_2224_37D0`
5. Debería mostrar:
   - **Estado:** Online 🟢
   - **Firmware Version:** 1.2.0
   - **Last Seen:** Hace menos de 2 minutos
   - **RSSI:** -XX dBm (señal WiFi)

### 2. Verificar Metadata en Backend

Ejecutar en terminal:
```bash
docker-compose exec backend python -c "
from app.core.database import SessionLocal
from app.models.device import Device
import json

db = SessionLocal()
device = db.query(Device).filter(Device.device_eui == 'ESP32_20251023_2224_37D0').first()

print('\n=== DEVICE INFO ===')
print(f'Name: {device.name}')
print(f'Firmware: {device.firmware_version}')
print(f'Last Seen: {device.last_seen_at}')
print(f'Is Online: {device.is_online}')
print('\n=== METADATA ===')
print(json.dumps(device.extra_data, indent=2))

db.close()
"
```

**Salida esperada:**
```
=== DEVICE INFO ===
Name: esp32prueba
Firmware: 1.2.0
Last Seen: 2025-10-23 22:50:15.123456
Is Online: True

=== METADATA ===
{
  "rssi_dbm": -58,
  "wifi_ssid": "MARCELO",
  "ip_address": "192.168.1.150",
  "free_heap_bytes": 250000,
  "uptime_sec": 180,
  "sensors_count": 0,
  "sampling_interval_sec": 300,
  "last_heartbeat_at": "2025-10-23T22:50:15.123456"
}
```

---

## 🐛 Troubleshooting

### Problema: "Error: Firmware upload failed"

**Causa:** ESP32 no responde en la IP configurada

**Soluciones:**
1. Verificar IP del ESP32 (puede haber cambiado)
2. Ping al ESP32: `ping 192.168.1.XXX`
3. Verificar firewall de Windows (debe permitir puerto 3232)
4. Usar USB si OTA no funciona

---

### Problema: "Network port not found"

**Causa:** ArduinoOTA no está funcionando en el ESP32

**Soluciones:**
1. Verificar que el firmware anterior tenía OTA habilitado
2. Si es la primera vez, usar USB para flashear
3. Después del primer flasheo USB, OTA estará disponible

---

### Problema: ESP32 no se conecta a WiFi MARCELO

**Causa:** Credenciales WiFi no guardadas o incorrectas

**Soluciones:**
1. Resetear configuración WiFi:
   - Mantener presionado GPIO0 al arrancar el ESP32
   - O desconectar/reconectar alimentación
2. Conectarse al portal AP: `ESP32-IoT-XXXXXX` (password: `iot_setup_pass`)
3. Configurar WiFi:
   - SSID: `MARCELO`
   - Password: `queso123`
   - API URL: `http://YOUR_SERVER_IP:8000/api/v1`
   - Device EUI: `ESP32_20251023_2224_37D0`

---

### Problema: Heartbeat no llega al backend

**Logs en ESP32:**
```
[HEARTBEAT] Error al enviar heartbeat
[API] HTTP Response Code: 404
```

**Causa:** Device no existe en la base de datos

**Solución:**
Crear el device manualmente via frontend o API:
```bash
curl -X POST "http://localhost:8000/api/v1/devices" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_JWT_TOKEN" \
  -d '{
    "device_eui": "ESP32_20251023_2224_37D0",
    "name": "esp32prueba",
    "status": "active"
  }'
```

---

## 📊 Frecuencia de Heartbeat

**Configuración actual:**
- **Heartbeat:** Cada 60 segundos
- **Condición:** Solo si NO hay sensores O si `samplingIntervalSec > 120`

**Para cambiar la frecuencia:**

Editar en `src/main.cpp`:
```cpp
// Línea 60
#define HEARTBEAT_INTERVAL_SEC 60  // Cambiar a 30, 120, etc.
```

**Recomendaciones:**
- Sin sensores: 30-120 segundos
- Con sensores: No necesario (readings actualizan last_seen_at)

---

## 🎯 Próximos Pasos

Una vez que el heartbeat esté funcionando:

1. **Conectar sensores** (DS18B20, DHT22) al ESP32
2. **Ajustar intervalo de muestreo** vía portal WiFi
3. **Configurar alertas** en el dashboard
4. **Agregar más ESP32** al sistema

---

**¿Necesitas ayuda?**
- Revisar Serial Monitor (115200 baud)
- Ver logs del backend: `docker-compose logs -f backend`
- Verificar red: `ping YOUR_SERVER_IP`

---

**Versión:** 1.0
**Última actualización:** 2025-10-23
**Autor:** Sistema IoT - IdeaMakers
