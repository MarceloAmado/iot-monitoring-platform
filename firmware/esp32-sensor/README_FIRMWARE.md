# 📡 Firmware ESP32 - Sistema de Monitoreo IoT

## 📋 Descripción

Firmware modular para ESP32 con arquitectura orientada a objetos que soporta múltiples sensores y actualización OTA (Over-The-Air).

## ✨ Características

- 🔌 **Zero-Config WiFi** - Portal cautivo para configuración inicial
- 📊 **Arquitectura POO** - Clase abstracta `Sensor` con polimorfismo
- 🌡️ **3 Tipos de Sensores** - DS18B20, DHT22, MPX5700
- 📡 **HTTP Client** - Envío automático de datos al backend
- 🔄 **OTA Updates** - Actualización de firmware vía WiFi
- 🔋 **Health Monitoring** - Auto-detección de fallas de sensores
- 📈 **Quality Score** - Evaluación de calidad de lecturas

## 🛠️ Sensores Soportados

### 1. DS18B20 - Temperatura Digital (OneWire)

**Características:**
- Protocolo: OneWire (1-Wire)
- Rango: -55°C a +125°C
- Precisión: ±0.5°C (-10°C a +85°C)
- Resolución: 9 a 12 bits (configurable)

**Conexión:**
```
DS18B20          ESP32
--------         -----
VCC    ────────> 3.3V
GND    ────────> GND
DATA   ────────> GPIO4 (PIN_DS18B20)
       (con resistencia pull-up 4.7kΩ a VCC)
```

**Variables exportadas:**
- `temp_c`: Temperatura en grados Celsius

---

### 2. DHT22 - Temperatura + Humedad

**Características:**
- Rango Temp: -40°C a +80°C
- Precisión Temp: ±0.5°C
- Rango Humedad: 0% a 100%
- Precisión Humedad: ±2%

**Conexión:**
```
DHT22            ESP32
-----            -----
VCC    ────────> 3.3V (o 5V)
GND    ────────> GND
DATA   ────────> GPIO5 (PIN_DHT22)
       (con resistencia pull-up 10kΩ a VCC)
```

**Variables exportadas:**
- `temp_c`: Temperatura en grados Celsius
- `humidity_pct`: Humedad relativa en porcentaje

---

### 3. MPX5700AP - Presión Absoluta (Analógico)

**Características:**
- Rango: 15 kPa a 700 kPa (0.15 bar a 7 bar)
- Salida: 0.2V a 4.7V (lineal)
- Precisión: ±2.5% del rango completo
- Temperatura operativa: -40°C a 125°C

**Conexión:**
```
MPX5700          ESP32
-------          -----
Vcc    ────────> 5V (alimentación)
GND    ────────> GND
Vout   ────────> GPIO34 (PIN_PRESSURE_ANALOG)
       (a través de divisor de voltaje 5V→3.3V)
```

**Divisor de Voltaje (IMPORTANTE):**
El ADC del ESP32 solo soporta 0-3.3V. Como el MPX5700 puede generar hasta 4.7V, se requiere un divisor:

```
5V ──┬── R1 (10kΩ) ──┬── ADC_ESP32
     │                │
     └── Vout_MPX ────┘
                      │
                      R2 (6.8kΩ) ── GND
```

**Variables exportadas:**
- `voltage_v`: Voltaje leído por el ADC (V)
- `pressure_kpa`: Presión en kiloPascales
- `pressure_bar`: Presión en bar
- `pressure_psi`: Presión en PSI

---

## 📦 Instalación

### Requisitos

- PlatformIO (recomendado) o Arduino IDE
- ESP32 Dev Board (cualquier variante)
- Cable USB para programación inicial

### Pasos

1. **Clonar repositorio**
```bash
cd firmware/esp32-sensor
```

2. **Instalar dependencias con PlatformIO**
```bash
pio lib install
```

3. **Configurar `config.h`**

Edita `src/config.h` y ajusta:
```cpp
#define API_BASE_URL "http://192.168.1.100:8000/api/v1"
#define DEFAULT_API_KEY "esp32_device_key_change_me"
#define SAMPLING_INTERVAL_SEC 300  // 5 minutos
#define OTA_PASSWORD "CHANGE_ME_OTA_PASSWORD"  // Cambiar en producción
```

4. **Compilar y subir**
```bash
pio run -t upload
```

5. **Monitorear Serial**
```bash
pio device monitor
```

---

## 🔧 Configuración Inicial (Zero-Config)

### Primera vez que se enciende el ESP32:

1. El ESP32 crea un Access Point con nombre `ESP32-IoT-XXXXXX` (donde XXXXXX son los últimos 6 dígitos de la MAC)

2. Conéctate a ese WiFi desde tu celular/PC
   - Password del AP: `iot_setup_pass`

3. Se abrirá automáticamente un portal cautivo (si no, ve a `http://192.168.4.1`)

4. Completa los datos:
   - **SSID WiFi:** Red WiFi del hospital/empresa
   - **Password WiFi:** Contraseña de la red
   - **API URL:** URL del backend (ej: `http://192.168.1.100:8000/api/v1`)
   - **API Key:** Key de autenticación del device
   - **Device EUI:** ID único del dispositivo (ej: `ESP32_LAB_001`)
   - **Sampling Interval:** Intervalo de muestreo en segundos (ej: `300`)

5. Click en "Save" → El ESP32 se reinicia y se conecta automáticamente

6. ✅ Configuración completa! El ESP32 ahora envía datos al backend cada 5 minutos.

---

## 🔄 OTA Updates (Over-The-Air)

### ¿Qué es OTA?

OTA permite actualizar el firmware del ESP32 **sin cable USB**, solo a través de WiFi.

### Habilitado por Defecto

El firmware viene con OTA habilitado por defecto:
```cpp
#define ENABLE_OTA true
#define OTA_PASSWORD "CHANGE_ME_OTA_PASSWORD"  // Cambiar en producción!!!
```

### Actualizar firmware vía OTA

#### Opción A: Arduino IDE

1. Compilar el nuevo firmware
2. Ir a `Tools > Port`
3. Verás el ESP32 disponible en la red (ej: `ESP32_LAB_001 at 192.168.1.123`)
4. Seleccionarlo
5. Click en "Upload"
6. Ingresa el password OTA cuando se solicite

#### Opción B: PlatformIO

1. Editar `platformio.ini`:
```ini
upload_protocol = espota
upload_port = 192.168.1.123  ; IP del ESP32
upload_flags =
    --auth=CHANGE_ME_OTA_PASSWORD      ; Password OTA
```

2. Ejecutar:
```bash
pio run -t upload
```

#### Opción C: Python esptool (comando)

```bash
python espota.py -i 192.168.1.123 -p 3232 -a CHANGE_ME_OTA_PASSWORD -f .pio/build/esp32dev/firmware.bin
```

### Rollback Automático

El firmware tiene rollback automático:
- Si el nuevo firmware falla al arrancar, el ESP32 vuelve automáticamente a la versión anterior.
- La partición actual se marca como "válida" después de un boot exitoso.

### Seguridad OTA

⚠️ **IMPORTANTE:** El password OTA por defecto es `CHANGE_ME_OTA_PASSWORD`. **DEBES cambiarlo en producción** en `config.h`:

```cpp
#define OTA_PASSWORD "tu_password_seguro_aqui"
```

---

## 📊 Payload de Datos

El ESP32 envía un JSON al backend cada X minutos:

```json
{
  "device_eui": "ESP32_LAB_001",
  "data_payload": {
    "temp_c": 25.5,           // DS18B20 o DHT22
    "humidity_pct": 62.3,     // DHT22
    "pressure_kpa": 101.3,    // MPX5700
    "pressure_bar": 1.013,    // MPX5700
    "pressure_psi": 14.7,     // MPX5700
    "voltage_v": 2.8,         // MPX5700 (voltaje raw)
    "rssi_dbm": -65,          // Señal WiFi
    "battery_mv": 3750,       // Voltaje batería (si aplica)
    "uptime_sec": 3600,       // Tiempo de funcionamiento
    "free_heap_kb": 180       // Memoria libre
  },
  "timestamp": "2025-10-20T14:30:00Z"
}
```

**Nota:** Las variables exactas dependen de qué sensores estén conectados.

---

## 🧪 Testing sin Hardware

### Simulador Python

El proyecto incluye un simulador ESP32 en Python:

```bash
cd firmware/simulator
python esp32_simulator.py --device ESP32_LAB_001 --interval 10 --iterations 20
```

Esto envía datos simulados al backend sin necesidad de hardware físico.

---

## 🐛 Debugging

### Serial Monitor

```bash
pio device monitor
```

Output esperado:
```
========================================
  SISTEMA DE MONITOREO IoT - ESP32
========================================
Firmware Version: 1.1.0
Build Date: Oct 20 2025 14:30:00
========================================

[SETUP] Paso 1: Conectando a WiFi...
✓ Conectado a WiFi: MiRed
  IP: 192.168.1.123
  RSSI: -65 dBm

[SETUP] Paso 2: Configurando OTA Updates...
✓ OTA Update habilitado
  Hostname: ESP32_LAB_001
  Port: 3232
  Password: ******

[SETUP] Paso 3: Inicializando sensores...
✓ DS18B20 Sensor inicializado en pin 4
✓ DHT22 Sensor inicializado en pin 5
✓ MPX5700 Sensor inicializado en pin 34

[SETUP] Setup completo! Sistema funcionando.

[LOOP] Realizando lectura de sensores...
  DS18B20: 25.5°C
  DHT22: 25.3°C, 62.3%
  MPX5700: 101.3 kPa (1.01 bar)
✓ Datos enviados exitosamente al backend
```

### Niveles de Debug

En `config.h`:
```cpp
#define DEBUG_LEVEL 3  // 0=none, 1=error, 2=warn, 3=info, 4=debug
```

---

## 📚 Arquitectura del Código

### Clase Abstracta `Sensor`

Todos los sensores heredan de la clase abstracta:

```cpp
class Sensor {
public:
    virtual String getType() = 0;           // "DS18B20", "DHT22", etc.
    virtual JsonObject read(JsonDocument& doc) = 0;  // Lee datos
    virtual bool isHealthy() = 0;           // Verifica si está funcionando
    virtual void begin() {}                 // Inicialización
};
```

### Agregar un Nuevo Sensor

1. Crear archivo `src/sensors/MiSensor.h`
2. Heredar de `Sensor`
3. Implementar métodos abstractos
4. En `main.cpp`:
```cpp
#include "sensors/MiSensor.h"

sensors.push_back(new MiSensor(PIN_MI_SENSOR));
```

---

## 🔋 Modo Bajo Consumo (Futuro)

Para aplicaciones con batería:
```cpp
// Deep sleep por 5 minutos
esp_sleep_enable_timer_wakeup(300 * 1000000ULL);  // Microsegundos
esp_deep_sleep_start();
```

**Consumo aproximado:**
- Modo activo: ~160 mA
- WiFi transmitiendo: ~240 mA
- Deep sleep: ~10 μA

---

## 📖 Referencias

- [ESP32 Arduino Core](https://docs.espressif.com/projects/arduino-esp32)
- [PlatformIO](https://platformio.org)
- [ArduinoJSON](https://arduinojson.org)
- [WiFiManager](https://github.com/tzapu/WiFiManager)
- [DS18B20 Datasheet](https://datasheets.maximintegrated.com/en/ds/DS18B20.pdf)
- [DHT22 Datasheet](https://www.sparkfun.com/datasheets/Sensors/Temperature/DHT22.pdf)
- [MPX5700 Datasheet](https://www.nxp.com/docs/en/data-sheet/MPX5700.pdf)

---

**Versión:** 1.1.0
**Última actualización:** 2025-10-20
**Autor:** Sistema IoT
