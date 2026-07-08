# Firmware ESP32 - Sistema de Monitoreo IoT

## 📌 Descripción

Firmware para ESP32 que lee datos de sensores (temperatura, humedad) y los envía a un backend API REST vía HTTP POST. Incluye portal de configuración Zero-Config para WiFi y parámetros del sistema.

## 🎯 Características

### Core
- ✅ **Zero-Config WiFi**: Portal cautivo para configuración sin código
- ✅ **Múltiples sensores**: Arquitectura OOP extensible
- ✅ **Envío automático**: POST al backend cada X segundos
- ✅ **Quality scoring**: Validación de lecturas
- ✅ **Auto-recovery**: Reconexión automática WiFi
- ✅ **Health monitoring**: Estadísticas de sistema y sensores
- ✅ **Low memory footprint**: Optimizado para ESP32

### Sensores Soportados
- ✅ **DS18B20**: Temperatura digital OneWire (-55°C a +125°C)
- ✅ **DHT22 (AM2302)**: Temperatura + Humedad (-40°C a +80°C, 0-100% RH)
- ✅ **MPX5700**: Presión analógica (0-700 kPa / 0-7 bar)
- ✅ **JSN-SR04T**: Distancia ultrasónica resistente al agua (25-600 cm) ⭐ **NUEVO**

### Networking
- ✅ **WiFi Manager**: Configuración vía portal web
- ✅ **HTTP Client**: POST JSON al backend
- ✅ **Retry logic**: Reintentos automáticos con backoff
- ✅ **Connection monitoring**: Detección de desconexión
- ✅ **OTA Updates**: Actualizaciones remotas vía WiFi ⭐ **NUEVO**
- 🔜 **HTTPS**: Certificados SSL (futuro)

## 🛠️ Stack Tecnológico

| Componente | Tecnología | Versión |
|------------|------------|---------|
| **MCU** | ESP32 | Cualquier variante |
| **Framework** | Arduino Core | Latest |
| **Build System** | PlatformIO | Latest |
| **WiFi Manager** | tzapu/WiFiManager | 2.0.16+ |
| **JSON Parser** | ArduinoJson | 6.21+ |
| **DS18B20 Driver** | DallasTemperature | 3.11+ |
| **DHT Driver** | Adafruit DHT | 1.4+ |

## 📁 Estructura del Proyecto

```
esp32-sensor/
├── platformio.ini           # Configuración de PlatformIO
├── src/
│   ├── main.cpp            # Loop principal
│   ├── config.h            # Configuración global
│   ├── sensors/
│   │   ├── Sensor.h        # Clase abstracta base
│   │   ├── DS18B20Sensor.h # Sensor de temperatura
│   │   ├── DHT22Sensor.h   # Sensor temp + humedad
│   │   ├── MPX5700Sensor.h # Sensor de presión
│   │   └── JSN_SR04TSensor.h # Sensor de distancia ultrasónico ⭐
│   ├── network/
│   │   ├── WiFiManager.h   # Zero-Config WiFi
│   │   └── APIClient.h     # Cliente HTTP
│   └── utils/
│       └── OTAUpdate.h     # Over-The-Air updates
├── examples/
│   ├── mpx5700_pressure_monitor.cpp  # Ejemplo MPX5700
│   └── jsn_sr04t_distance_monitor.cpp  # Ejemplo JSN-SR04T ⭐
└── README.md
```

## 🚀 Instalación

### Requisitos

- **PlatformIO** (recomendado) o Arduino IDE
- **ESP32 Dev Board** (cualquier modelo con WiFi)
- **Sensores**: DS18B20 y/o DHT22
- **Cables y resistencias**: Pull-up 4.7kΩ para DS18B20

### Setup con PlatformIO

1. **Clonar el repositorio**:
   ```bash
   cd firmware/esp32-sensor
   ```

2. **Instalar dependencias** (automático con PlatformIO):
   ```bash
   pio lib install
   ```

3. **Conectar el ESP32** vía USB

4. **Compilar y subir**:
   ```bash
   pio run -t upload
   ```

5. **Abrir Serial Monitor**:
   ```bash
   pio device monitor
   ```

### Setup con Arduino IDE

1. Instalar soporte para ESP32:
   - File → Preferences → Additional Boards Manager URLs:
   - `https://dl.espressif.com/dl/package_esp32_index.json`

2. Instalar librerías (Tools → Manage Libraries):
   - WiFiManager by tzapu
   - ArduinoJson by Benoit Blanchon
   - OneWire by Paul Stoffregen
   - DallasTemperature by Miles Burton
   - DHT sensor library by Adafruit

3. Abrir `src/main.cpp`

4. Seleccionar Board: ESP32 Dev Module

5. Upload

## ⚙️ Configuración

### Hardware - Conexiones de Pines

#### DS18B20 (Temperatura OneWire)

| Pin DS18B20 | ESP32 Pin | Notas |
|-------------|-----------|-------|
| VCC | 3.3V | Alimentación |
| GND | GND | Tierra |
| DQ (Data) | GPIO 4 | Requiere pull-up 4.7kΩ a 3.3V |

#### DHT22 (Temp + Humedad)

| Pin DHT22 | ESP32 Pin | Notas |
|-----------|-----------|-------|
| VCC | 3.3V | Alimentación |
| GND | GND | Tierra |
| DATA | GPIO 5 | Pull-up interno activado |

#### MPX5700 (Presión)

| Pin MPX5700 | ESP32 Pin | Notas |
|-------------|-----------|-------|
| VCC | 5V | Alimentación (requiere divisor de voltaje en Vout) |
| GND | GND | Tierra |
| Vout | GPIO 34 (ADC1_6) | Via divisor de voltaje 5V→3.3V |

**Divisor de voltaje necesario** (protección del ADC):
```
MPX5700 Vout (0-4.7V) → R1 (10kΩ) → GPIO34 (ADC) → R2 (4.7kΩ) → GND
```

#### JSN-SR04T (Distancia Ultrasónica) ⭐ **NUEVO**

| Pin JSN-SR04T | ESP32 Pin | Notas |
|---------------|-----------|-------|
| VCC | 5V | Alimentación (requiere 5V, consumo ~30mA) |
| GND | GND | Tierra |
| TRIG | GPIO 12 | Pin para enviar pulso de trigger |
| ECHO | GPIO 14 | Pin para recibir pulso de echo (5V tolerante) |

**Características:**
- Rango: 25 cm - 600 cm
- Resolución: 0.5 cm
- Ángulo de detección: 70°
- Resistente al agua (IP67)
- Cable de 2.5m incluido
- Tiempo mínimo entre lecturas: 50ms

**Nota sobre voltajes:**
El pin ECHO emite señal de 5V, pero el ESP32 es **5V tolerante** en la mayoría de sus pines GPIO (excepto ADC). GPIO 14 puede recibir 5V de forma segura. Si prefieres usar un divisor de voltaje para mayor seguridad:
```
JSN-SR04T ECHO (5V) → R1 (10kΩ) → GPIO14 → R2 (10kΩ) → GND
```

#### Diagrama Esquemático

```
         ESP32                 DS18B20
    +-----------+             +-------+
    |           |             |       |
    | 3.3V -----+-------------+ VCC   |
    |           |      4.7kΩ  |       |
    | GPIO4 ----+----/\/\/\---+ DQ    |
    |           |      |      |       |
    | GND ------+------+------+ GND   |
    +-----------+             +-------+

         ESP32                 DHT22
    +-----------+             +-------+
    |           |             |       |
    | 3.3V -----+-------------+ VCC   |
    |           |             |       |
    | GPIO5 ----+-------------+ DATA  |
    |           |             |       |
    | GND ------+-------------+ GND   |
    +-----------+             +-------+
```

### Software - Portal de Configuración

#### Primera vez (Zero-Config)

1. **Encender el ESP32** (primera vez o después de reset)

2. **El ESP32 crea un Access Point**:
   - SSID: `ESP32-IoT-XXXXXX` (últimos 6 dígitos de MAC)
   - Contraseña: `iot_setup_pass`

3. **Conectarse al AP** desde tu celular/PC

4. **Abrir navegador** en `http://192.168.4.1`

5. **Configurar parámetros**:
   - **WiFi SSID**: Red WiFi del hospital/empresa
   - **WiFi Password**: Contraseña de la red
   - **API URL**: URL del backend (ej: `http://192.168.1.100:8000/api/v1`)
   - **API Key**: Key de autenticación del dispositivo
   - **Device EUI**: ID único del dispositivo (ej: `ESP32_LAB_001`)
   - **Intervalo de Muestreo**: Segundos entre lecturas (ej: `300` = 5 min)

6. **Guardar**: El ESP32 se reinicia y conecta automáticamente

#### Resetear Configuración

Para borrar credenciales WiFi y volver al portal:

**Método 1: Botón físico** (si está conectado):
- Mantener presionado GPIO 0 durante 5 segundos al encender

**Método 2: Código**:
```cpp
// Descomentar temporalmente en main.cpp:
wifiManager.begin(true);  // true = forzar config
```

### Software - Configuración del Código

Editar `src/config.h`:

```cpp
// Configuración predeterminada (se sobrescribe con portal)
#define API_BASE_URL "http://192.168.1.100:8000/api/v1"
#define DEFAULT_API_KEY "esp32_device_key_change_me"
#define SAMPLING_INTERVAL_SEC 300  // 5 minutos

// Pines de sensores
#define PIN_DS18B20 4
#define PIN_DHT22 5

// Debug
#define ENABLE_SERIAL_DEBUG true
#define DEBUG_LEVEL 3  // 0-4 (0=none, 4=verbose)
```

## 🔍 Uso y Funcionamiento

### Flujo de Ejecución

1. **Boot** → Inicializa Serial, LED, WiFi Manager
2. **WiFi Connect** → Portal si no hay config, o conecta directo
3. **Sensor Init** → Inicializa DS18B20, DHT22
4. **Backend Test** → Verifica que el API responde
5. **Primera Lectura** → Lee sensores y envía inmediatamente
6. **Loop Infinito**:
   - Cada X segundos: Leer sensores → Enviar al backend
   - Cada 5 min: Health check
   - Continuo: Monitor WiFi (reconexión automática)

### Output Serial Esperado

```
========================================
  SISTEMA DE MONITOREO IoT - ESP32
========================================
Firmware Version: 1.0.0
Build Date: Oct 17 2025 14:30:00
========================================

[SETUP] Paso 1: Conectando a WiFi...
[WiFi] Conectando a: MiWiFi_5G
[WiFi] ✓ Conectado exitosamente
[WiFi] IP Address: 192.168.1.150
[WiFi] RSSI: -45 dBm

[SETUP] Paso 2: Inicializando sensores...
[DS18B20] Sensor inicializado. Dispositivos encontrados: 1
[DHT22] Sensor inicializado. Temp: 24.5°C, Humedad: 55.0%
[SENSORS] ✓ 2 sensores inicializados

[SETUP] Paso 3: Verificando conexión con backend...
[API] Testeando conexión al backend...
[API] ✓ Backend accesible

[SETUP] Paso 5: Primera lectura de sensores...

========================================
[READING] Iniciando lectura de sensores
========================================

[READING] Leyendo sensor: DS18B20
[DS18B20] Temperatura: 24.75°C
[READING]   temp_c: 24.75

[READING] Leyendo sensor: DHT22
[DHT22] Temperatura: 24.50°C
[DHT22] Humedad: 55.20%
[READING]   temp_c: 24.50
[READING]   humidity_pct: 55.20

[READING] Agregando metadata del dispositivo...
[READING]   rssi_dbm: -45
[READING]   uptime_sec: 8
[READING]   free_heap_bytes: 245632

[READING] Quality Score: 1.00
[READING] Tiempo de lectura: 1250 ms

========================================
[API] Enviando reading al backend
========================================
[API] URL: http://192.168.1.100:8000/api/v1/readings
[API] Payload JSON:
{"device_eui":"ESP32_LAB_001","data_payload":{"temp_c":24.75,"humidity_pct":55.2,"rssi_dbm":-45,"uptime_sec":8,"free_heap_bytes":245632}}
[API] HTTP Response Code: 201
[API] ✓ Reading enviado exitosamente
[API] Respuesta del servidor:
[API]   - Reading ID: 42
[API]   - Quality Score: 0.95
========================================

[BACKEND] ✓ Datos enviados exitosamente

========================================
  ✓ SETUP COMPLETADO EXITOSAMENTE
  Tiempo de boot: 8250 ms
========================================

Próxima lectura en 300 segundos...
```

## 📊 Formato de Datos Enviados

### Request JSON al Backend

```json
{
  "device_eui": "ESP32_LAB_001",
  "data_payload": {
    "temp_c": 24.75,
    "humidity_pct": 55.2,
    "rssi_dbm": -45,
    "uptime_sec": 3600,
    "free_heap_bytes": 245632
  }
}
```

### Response del Backend

```json
{
  "id": 12345,
  "device_id": 5,
  "quality_score": 0.95,
  "processed": false,
  "timestamp": "2025-10-17T14:30:00Z"
}
```

---

## 💓 Heartbeat (Devices sin Sensores)

### ¿Qué es el Heartbeat?

El **heartbeat** es un mecanismo que permite a los ESP32 reportar que están vivos aunque **no tengan sensores conectados** o no estén enviando readings de sensores.

### ¿Cuándo usar Heartbeat?

✅ **Usar heartbeat cuando:**
- ESP32 recién provisionado sin sensores conectados
- Device en mantenimiento que no envía readings
- Quieres monitorear conectividad WiFi sin sensores
- Necesitas actualizar metadata del sistema (RSSI, heap, uptime)

❌ **NO usar heartbeat si:**
- El ESP32 ya está enviando readings (los readings actualizan `last_seen_at` automáticamente)

### Request JSON Heartbeat

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

**Endpoint:** `POST /api/v1/devices/heartbeat`

### Response Heartbeat

```json
{
  "device_id": 5,
  "device_eui": "ESP32_LAB_001",
  "last_seen_at": "2025-10-24T01:30:00.000000",
  "is_online": true,
  "message": "Heartbeat recibido correctamente"
}
```

### Código de Ejemplo

```cpp
#include "network/APIClient.h"

// Crear cliente API
APIClient apiClient("http://192.168.1.100:8000/api/v1", "api_key");

void setup() {
    // ... inicialización WiFi ...
}

void loop() {
    // Enviar heartbeat cada 5 minutos (si NO hay sensores)
    static unsigned long lastHeartbeat = 0;
    unsigned long now = millis();

    if (now - lastHeartbeat >= 300000) {  // 5 minutos
        lastHeartbeat = now;

        // Opción 1: Heartbeat con metadata automática
        bool success = apiClient.sendHeartbeat("ESP32_LAB_001", "1.2.0");

        // Opción 2: Heartbeat con metadata personalizada
        StaticJsonDocument<256> doc;
        JsonObject metadata = doc.to<JsonObject>();
        metadata["rssi_dbm"] = WiFi.RSSI();
        metadata["free_heap_bytes"] = ESP.getFreeHeap();
        metadata["uptime_sec"] = millis() / 1000;
        metadata["custom_field"] = "valor_personalizado";

        bool success = apiClient.sendHeartbeat("ESP32_LAB_001", "1.2.0", metadata);

        // Opción 3: Heartbeat con retry automático
        bool success = apiClient.sendHeartbeatWithRetry("ESP32_LAB_001", "1.2.0");

        if (success) {
            Serial.println("✓ Heartbeat enviado");
        } else {
            Serial.println("✗ Error enviando heartbeat");
        }
    }

    delay(1000);
}
```

### Frecuencia Recomendada

| Escenario | Frecuencia Heartbeat | Frecuencia Readings |
|-----------|---------------------|---------------------|
| **ESP32 sin sensores** | Cada 1-5 minutos | N/A |
| **ESP32 con sensores activos** | No necesario | Cada 5-15 minutos |
| **ESP32 en mantenimiento** | Cada 1 minuto | Deshabilitado |

**Nota:** Si el ESP32 tiene sensores y está enviando readings, **NO es necesario** enviar heartbeats separados, porque los readings ya actualizan el campo `last_seen_at` automáticamente.

### Beneficios del Heartbeat

1. **Detección de offline:** El backend detecta devices sin heartbeat en 10+ minutos
2. **Monitoreo de WiFi:** Permite ver RSSI y calidad de señal aunque no haya sensores
3. **Metadata actualizada:** Firmware version, IP, uptime siempre actualizado
4. **Troubleshooting:** Facilita debugging de devices recién provisionados

---

## 🐛 Troubleshooting

### Problema: ESP32 no conecta a WiFi

**Síntomas**: LED parpadeando, portal AP se abre siempre

**Soluciones**:
1. Verificar SSID y contraseña en el portal
2. Verificar que el router esté en 2.4GHz (ESP32 no soporta 5GHz)
3. Acercarse al router (RSSI > -70 dBm)
4. Resetear configuración: `wifiManager.begin(true)`

### Problema: Sensor DS18B20 retorna -999

**Síntomas**: `[DS18B20] Sensor desconectado o sin respuesta`

**Soluciones**:
1. Verificar conexión física (VCC, GND, DQ)
2. Verificar resistor pull-up 4.7kΩ entre DQ y 3.3V
3. Cambiar el sensor (puede estar dañado)
4. Verificar que el pin en `config.h` coincide con el físico

### Problema: DHT22 retorna NaN

**Síntomas**: `[DHT22] Error al leer temperatura (NaN)`

**Soluciones**:
1. Esperar 2 segundos después de `begin()` antes de leer
2. Verificar alimentación estable (usar capacitor 100nF cerca del sensor)
3. No leer más de 1 vez cada 2 segundos
4. Verificar que el pin DATA esté en GPIO 5

### Problema: Backend no recibe datos

**Síntomas**: `[API] Error 404: Endpoint no encontrado`

**Soluciones**:
1. Verificar que el backend esté corriendo (`docker-compose up`)
2. Verificar URL del API en portal de configuración
3. Verificar que ESP32 y backend estén en la misma red
4. Ping al backend desde la terminal: `ping 192.168.1.100`
5. Verificar API Key correcta

### Problema: Error 401 Unauthorized

**Síntomas**: `[API] Error 401: No autorizado`

**Soluciones**:
1. Verificar API Key en el portal de configuración
2. Generar nueva API Key en el backend
3. Verificar que el device_eui existe en la base de datos

## 🔄 OTA Updates (Over-The-Air) ⭐ **NUEVO**

### ¿Qué es OTA?

OTA (Over-The-Air) permite actualizar el firmware del ESP32 **sin cable USB**, directamente vía WiFi. Esto es crucial para dispositivos instalados en lugares de difícil acceso (techos, salas limpias, etc.).

### Características Implementadas

- ✅ **ArduinoOTA** integrado (puerto 3232)
- ✅ **Password protection** (configurable en `config.h`)
- ✅ **Progress tracking** (logs de porcentaje)
- ✅ **Partition rollback** automático en caso de fallo
- ✅ **Validación de firmware** después del boot

### Configuración OTA

#### 1. Habilitar OTA (Ya habilitado por defecto)

En `src/config.h`:
```cpp
#define ENABLE_OTA true
#define OTA_PORT 3232
#define OTA_PASSWORD "CHANGE_ME_OTA_PASSWORD"  // ⚠️ CAMBIAR EN PRODUCCIÓN
```

#### 2. Primera Carga (USB)

El primer firmware **DEBE cargarse por USB**:

```bash
# Con PlatformIO
pio run -t upload

# Con Arduino IDE
Sketch → Upload
```

#### 3. Actualizaciones OTA (WiFi)

Una vez el ESP32 está en la red WiFi:

**Opción A: PlatformIO (Recomendado)**

1. Editar `platformio.ini`:
```ini
; Descomentar estas líneas:
upload_protocol = espota
upload_port = 192.168.1.XXX  ; IP del ESP32
upload_flags =
    --port=3232
    --auth=CHANGE_ME_OTA_PASSWORD
```

2. Subir firmware:
```bash
pio run -t upload
```

**Opción B: Arduino IDE**

1. Tools → Port → Network Port: `ESP32_LAB_001 at 192.168.1.150`
2. Tools → Upload

**Opción C: Manual con espota.py**

```bash
python ~/.platformio/packages/framework-arduinoespressif32/tools/espota.py \
  -i 192.168.1.150 \
  -p 3232 \
  -a CHANGE_ME_OTA_PASSWORD \
  -f .pio/build/esp32dev/firmware.bin
```

### ¿Cómo Funciona OTA?

1. **Particiones duales**: ESP32 tiene dos particiones de firmware (app0 y app1)
2. **Nueva versión** se escribe en la partición inactiva
3. **Después del update**, el ESP32 reinicia y arranca desde la nueva partición
4. **Si el boot falla**, automáticamente vuelve a la partición anterior (rollback)
5. **Si el boot es exitoso**, se marca la nueva partición como válida

### Logs OTA Esperados

```
========================================
  SISTEMA DE MONITOREO IoT - ESP32
========================================
Firmware Version: 1.1.0
Build Date: Oct 21 2025 20:30:00
========================================

[SETUP] Paso 2: Configurando OTA Updates...
✓ OTA Update habilitado
  Hostname: ESP32_LAB_001
  Port: 3232
  Password: ******

--- OTA Partition Info ---
Running partition: app0 (type 0, subtype 16)
--------------------------

✓ Partición actual marcada como válida
[SETUP] OTA Updates configurado correctamente

...

# Cuando se recibe un update:
🔄 OTA Update iniciado: sketch
⏳ Progreso: 10%
⏳ Progreso: 20%
⏳ Progreso: 30%
...
⏳ Progreso: 100%

✅ OTA Update completado exitosamente!
🔃 Reiniciando en 3 segundos...
```

### Seguridad OTA

⚠️ **IMPORTANTE**: En producción:

1. **Cambiar password OTA** en `config.h`:
```cpp
#define OTA_PASSWORD "tu_password_seguro_aqui"
```

2. **Validar firmware** antes de subir (testing completo)

3. **Backup de versión anterior** (guardar `.bin` funcional)

4. **Monitorear el update** vía Serial Monitor

5. **Considerar actualizar en ventanas de mantenimiento** (no durante operación crítica)

### Rollback Manual (Si es necesario)

Si un update causó problemas y el rollback automático no funcionó:

```cpp
// En main.cpp, agregar temporalmente:
#include <esp_ota_ops.h>

void setup() {
    // ... código existente ...

    // Forzar rollback
    esp_ota_mark_app_invalid_rollback_and_reboot();
}
```

### Futuras Mejoras OTA (Roadmap)

- [ ] Auto-update desde servidor backend (`GET /api/v1/firmware/latest`)
- [ ] Verificación de checksum MD5
- [ ] Firmado de firmware con clave privada
- [ ] Update scheduling (actualizar solo en horario específico)
- [ ] Notificación al backend cuando hay update disponible

---

## 📈 Próximas Funcionalidades (Roadmap)

### Sprint 5
- [ ] Sincronización de tiempo (NTP)
- [ ] HTTPS con validación de certificados
- [ ] Deep Sleep para bajo consumo
- [ ] Modo offline con buffer local

## 🔐 Seguridad

### Buenas Prácticas

✅ **Hacer**:
- Cambiar `WIFI_AP_PASSWORD` en producción
- Usar HTTPS cuando esté disponible
- Rotar API Keys periódicamente
- No hardcodear credenciales en el código

❌ **No hacer**:
- Commitear API Keys reales al repositorio
- Usar WiFi abierto (sin contraseña)
- Dejar debug serial habilitado en producción
- Exponer el backend directamente a Internet sin firewall

## 📝 Desarrollo y Contribución

### Agregar un Nuevo Sensor

1. **Crear clase heredando de `Sensor`**:

```cpp
// src/sensors/MiSensor.h
#ifndef MI_SENSOR_H
#define MI_SENSOR_H

#include "Sensor.h"

class MiSensor : public Sensor {
public:
    MiSensor(uint8_t pin) { this->pin = pin; }

    void begin() override {
        // Inicialización
    }

    String getType() override {
        return "MiSensor";
    }

    JsonObject read(JsonDocument& doc) override {
        JsonObject data = doc.createNestedObject();
        data["mi_variable"] = 123.45;
        return data;
    }

    bool isHealthy() override {
        return true;  // Lógica de health check
    }
};

#endif
```

2. **Registrar en `main.cpp`**:

```cpp
#include "sensors/MiSensor.h"

void setupSensors() {
    sensors.push_back(new MiSensor(PIN_MI_SENSOR));
}
```

3. **Definir pin en `config.h`**:

```cpp
#define PIN_MI_SENSOR 15
```

## 📚 Referencias

- [ESP32 Arduino Core](https://docs.espressif.com/projects/arduino-esp32/)
- [WiFiManager Library](https://github.com/tzapu/WiFiManager)
- [ArduinoJson](https://arduinojson.org/)
- [DallasTemperature](https://github.com/milesburton/Arduino-Temperature-Control-Library)
- [Adafruit DHT](https://github.com/adafruit/DHT-sensor-library)

---

## 🎉 Cambios Recientes

### v1.2.0 - 2025-10-23 ⭐ **ACTUAL**

**Nuevas Características:**
- ✅ **Sensor JSN-SR04T** - Soporte completo para distancia ultrasónica resistente al agua (25-600 cm)
  - Protocolo ultrasónico trigger/echo
  - Auto-retry con 3 intentos en caso de falla
  - Detección de lecturas fuera de rango
  - Cooldown de 50ms entre mediciones
  - Health monitoring con contador de errores consecutivos
  - Ejemplo de uso en `examples/jsn_sr04t_distance_monitor.cpp`

**Características Técnicas:**
- Resolución: 0.5 cm
- Ángulo de detección: 70°
- IP67 resistente al agua con cable de 2.5m
- Timeout automático para objetos muy lejanos
- Última lectura válida disponible durante errores

### v1.1.0 - 2025-10-21

**Nuevas Características:**
- ✅ **Sensor MPX5700** - Soporte completo para presión analógica (0-700 kPa)
  - Calibración automática con presión conocida
  - Conversión a kPa, bar y PSI
  - Promediado de 10 muestras para estabilidad
  - Ejemplo de uso en `examples/mpx5700_pressure_monitor.cpp`

- ✅ **OTA Updates** - Actualizaciones vía WiFi sin cable USB
  - ArduinoOTA integrado con password protection
  - Progress tracking y rollback automático
  - Soporte para particiones duales
  - Documentación completa de uso

**Mejoras:**
- Estructura de sensores más modular
- Mejor manejo de errores en ADC
- Logs más detallados para debugging

---

**Última actualización**: 2025-10-23
**Sprint**: 4 (En progreso)
**Versión**: 1.2.0
**Status**: ✅ OTA + MPX5700 + JSN-SR04T Implementados
