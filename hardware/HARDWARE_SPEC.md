# Especificacion de Hardware - Sistema IoT Monitoring
> Documento para ingenieria - Preparacion de hardware
> Fecha: 2026-02-21 | Firmware: v1.2.0

## Estructura de esta carpeta

```
hardware/
├── HARDWARE_SPEC.md          ← Este archivo (spec, BOM, pinout, conexiones)
└── kicad/                    ← Esquematicos y PCB (KiCad 8+)
    ├── iot-node.kicad_pro    ← Proyecto KiCad
    ├── iot-node.kicad_sch    ← Esquematico
    ├── iot-node.kicad_pcb    ← PCB layout
    └── fabrication/          ← Gerbers y BOM para fabricacion
```

> Los archivos KiCad son mantenidos por ingenieria. Esta spec sirve como referencia de diseño.

---

## 1. Resumen del Sistema

Sistema SCADA-lite de monitoreo IoT. Dispositivos ESP32 leen sensores, envian datos via HTTP al backend (FastAPI + PostgreSQL), y se visualizan en dashboard web (React). Soporte para multiples sensores por nodo, OTA updates remoto, y WiFi zero-config.

```
[Sensor] → [ESP32] → WiFi → [Backend API] → [PostgreSQL]
                                   ↓
                              [Dashboard Web]
```

---

## 2. Microcontrolador

### Placa soportada
| Parametro | Valor |
|-----------|-------|
| Placa | ESP32-DevKit v1 (o compatible ESP32-WROOM-32) |
| Framework | Arduino (via PlatformIO) |
| Platform | espressif32 |
| Board ID (PlatformIO) | `esp32dev` |
| CPU | Dual-core Xtensa LX6, 240 MHz |
| Flash | 4 MB minimo |
| RAM | 520 KB SRAM |
| WiFi | 802.11 b/g/n 2.4 GHz |
| ADC | 12 bits (0-4095), pines GPIO 32-39 |
| Alimentacion | 5V via USB o 3.3V regulado |

### NodeMCU ESP32
Tambien compatible. Mismo chip ESP32-WROOM-32. Conexion USB micro/tipo-C segun version.

---

## 3. Sensores Soportados

El firmware usa arquitectura modular con clase base `Sensor`. Cada sensor se activa/desactiva comentando defines en `config.h`.

### 3.1 Sensor Analogico Generico (AnalogSensor)
**Estado: ACTIVO para pruebas**

Para potenciometros, LDR, sensores de humedad de suelo, o cualquier señal 0-3.3V.

| Parametro | Valor |
|-----------|-------|
| Archivo | `sensors/AnalogSensor.h` |
| Pin default | GPIO34 (ADC1_CH6) |
| Resolucion | 12 bits (0-4095) |
| Rango entrada | 0 - 3.3V |
| Define en config.h | `PIN_ANALOG_SENSOR`, `ANALOG_SENSOR_LABEL` |

**Datos reportados:**
| Key JSON | Descripcion | Ejemplo |
|----------|-------------|---------|
| `{label}_raw` | Valor ADC crudo (0-4095) | `pot_raw: 2048` |
| `{label}_v` | Voltaje calculado (0-3.3V) | `pot_v: 1.65` |
| `{label}_pct` | Porcentaje (0-100%) | `pot_pct: 50.0` |

**Conexion potenciometro (10K):**
```
        ESP32
       ┌──────┐
3.3V ──┤ 3V3  │
       │      │
  ┌────┤GPIO34│ (ADC input)
  │    │      │
  │  ──┤ GND  │
  │ │  └──────┘
  │ │
  └─┤── Potenciometro 10K
    │   (wiper al medio → GPIO34)
    │   (extremo 1 → 3.3V)
    └── (extremo 2 → GND)
```

> **IMPORTANTE:** Solo usar pines ADC1 (GPIO 32-39). ADC2 (GPIO 0,2,4,12-15,25-27) NO funciona cuando WiFi esta activo.

### 3.2 DS18B20 - Temperatura (OneWire)
| Parametro | Valor |
|-----------|-------|
| Archivo | `sensors/DS18B20Sensor.h` |
| Pin default | GPIO4 |
| Protocolo | OneWire |
| Rango | -55°C a +125°C |
| Precision | ±0.5°C |
| Define en config.h | `PIN_DS18B20` |
| Libreria | DallasTemperature + OneWire |

**Conexion:**
```
DS18B20         ESP32
───────         ─────
VDD (rojo)  →  3.3V
GND (negro) →  GND
DATA (amarillo) → GPIO4
                   │
              R 4.7K pull-up
                   │
                  3.3V
```

**Datos reportados:** `temp_c` (float, grados Celsius)

### 3.3 DHT22 - Temperatura + Humedad
| Parametro | Valor |
|-----------|-------|
| Archivo | `sensors/DHT22Sensor.h` |
| Pin default | GPIO5 |
| Protocolo | Digital propietario |
| Rango temp | -40°C a +80°C (±0.5°C) |
| Rango humedad | 0-100% RH (±2%) |
| Define en config.h | `PIN_DHT22` |
| Libreria | Adafruit DHT + Unified Sensor |

**Conexion:**
```
DHT22          ESP32
─────          ─────
VCC (pin 1) →  3.3V
DATA (pin 2) → GPIO5
               │
          R 10K pull-up
               │
              3.3V
NC (pin 3)     (no conectar)
GND (pin 4) →  GND
```

**Datos reportados:** `temp_c`, `humidity_pct`

### 3.4 MPX5700 - Presion Analogica
| Parametro | Valor |
|-----------|-------|
| Archivo | `sensors/MPX5700Sensor.h` |
| Pin default | GPIO34 (ADC) |
| Rango | 15 - 700 kPa |
| Salida | 0.2V - 4.7V (requiere divisor de voltaje para ESP32) |
| Define en config.h | `PIN_PRESSURE_ANALOG` |

**Datos reportados:** `pressure_kpa`

> **ATENCION:** La salida del MPX5700 puede superar 3.3V. Usar divisor de voltaje resistivo para no dañar el ADC del ESP32.

### 3.5 JSN-SR04T - Distancia Ultrasonica
| Parametro | Valor |
|-----------|-------|
| Archivo | `sensors/JSN_SR04TSensor.h` |
| Protocolo | Trigger/Echo (como HC-SR04) |
| Rango | 20 cm - 600 cm |
| Resistente al agua | Si (IP67 en el transductor) |

**Datos reportados:** `distance_cm`

---

## 4. Configuracion Inicial para Pruebas con Potenciometro

### 4.1 Hardware necesario
- 1x ESP32-DevKit v1 o NodeMCU ESP32
- 1x Potenciometro 10K ohm (lineal)
- 3x Cables dupont (macho-macho o macho-hembra segun placa)
- 1x Cable USB micro/tipo-C (para alimentacion y programacion)

### 4.2 Conexiones
| Potenciometro | ESP32 |
|---------------|-------|
| Pin izquierdo | GND |
| Pin central (wiper) | GPIO34 |
| Pin derecho | 3.3V |

> No usar el pin de 5V para el potenciometro. El ADC del ESP32 tiene rango maximo de 3.3V.

### 4.3 Configuracion del firmware (`config.h`)

Antes de flashear, editar estos valores:

```cpp
// WiFi (tu red local)
// Se configura via WiFi Manager portal cautivo al primer boot.
// Si la red no se encuentra, el ESP32 abre un AP:
//   SSID: ESP32-IoT-XXXX  |  Password: iot_setup_pass

// Backend API
#define API_BASE_URL "http://<IP_PC_BACKEND>:8000/api/v1"
#define DEFAULT_API_KEY "test_key_nodemcu_001"

// Sensor analogico
#define PIN_ANALOG_SENSOR 34
#define ANALOG_SENSOR_LABEL "pot"

// Sampling (30s para testing, 300s en produccion)
#define SAMPLING_INTERVAL_SEC 30
```

### 4.4 Datos pre-cargados en la base de datos

| Campo | Valor |
|-------|-------|
| Device EUI | `NODEMCU_POT_001` |
| API Key | `test_key_nodemcu_001` |
| Asset | Potenciometro_Test_001 |
| Location | Mesa de Pruebas (LAB-MESA-01) |
| LocationGroup | Laboratorio IdeaMakers |

### 4.5 Flashear el firmware

```bash
# Desde la carpeta firmware/esp32-sensor/
# Compilar y subir por USB
pio run -t upload

# Monitor serial (ver logs)
pio device monitor --baud 115200
```

### 4.6 Primer boot - WiFi Manager

1. El ESP32 intenta conectar a la ultima red guardada
2. Si falla, abre un Access Point:
   - SSID: `ESP32-IoT-XXXX` (XXXX = ultimos digitos MAC)
   - Password: `iot_setup_pass`
3. Conectarse al AP desde celular/PC
4. Se abre portal cautivo automaticamente (o ir a 192.168.4.1)
5. Configurar:
   - SSID y password de tu red WiFi
   - Device EUI: `NODEMCU_POT_001`
   - API URL: `http://<IP_PC>:8000/api/v1`
   - API Key: `test_key_nodemcu_001`
   - Sampling interval: `30`
6. Guardar. El ESP32 se reinicia y conecta a tu red.

---

## 5. Flujo de Datos

```
1. ESP32 boot → WiFi connect → OTA check
2. Cada 30s (configurable):
   a. Lee potenciometro (raw, voltaje, porcentaje)
   b. Agrega metadata (RSSI, uptime, free_heap)
   c. POST /api/v1/readings con headers:
      X-API-Key: test_key_nodemcu_001
      X-Device-EUI: NODEMCU_POT_001
   d. Backend almacena en PostgreSQL
   e. WebSocket notifica al dashboard en tiempo real
3. Cada 5 min: health check interno
4. Cada 1h: chequeo OTA (firmware updates via HTTP)
```

### Ejemplo de payload enviado al backend
```json
{
  "device_eui": "NODEMCU_POT_001",
  "data_payload": {
    "pot_raw": 2048,
    "pot_v": 1.65,
    "pot_pct": 50.0,
    "rssi_dbm": -55,
    "uptime_sec": 120,
    "free_heap_bytes": 180000
  }
}
```

---

## 6. Pines Reservados / No Usar

| Pin | Motivo |
|-----|--------|
| GPIO0 | Boot mode (no usar como input) |
| GPIO1 | TX Serial (usado por USB-UART) |
| GPIO2 | LED integrado (usado para status) |
| GPIO3 | RX Serial (usado por USB-UART) |
| GPIO6-11 | Flash SPI interno (NO TOCAR) |
| GPIO12 | Boot strapping (evitar pull-up externo) |
| ADC2 (GPIO 0,2,4,12-15,25-27) | No funciona con WiFi activo |

### Pines ADC1 disponibles (funcionan con WiFi)
| Pin | Canal ADC | Disponible |
|-----|-----------|------------|
| GPIO32 | ADC1_CH4 | Libre |
| GPIO33 | ADC1_CH5 | Libre |
| GPIO34 | ADC1_CH6 | **Usado: Potenciometro** |
| GPIO35 | ADC1_CH7 | Reservado para bateria |
| GPIO36 (VP) | ADC1_CH0 | Libre |
| GPIO39 (VN) | ADC1_CH3 | Libre |

> GPIO34-39 son solo input (no tienen pull-up/pull-down interno).

---

## 7. OTA Updates

### 7.1 OTA Local (ArduinoOTA - misma red WiFi)
```bash
# Descomentar en platformio.ini:
upload_protocol = espota
upload_port = <IP_DEL_ESP32>
upload_flags =
    --port=3232
    --auth=CHANGE_ME_OTA_PASSWORD

# Luego:
pio run -t upload
```

### 7.2 OTA Remoto (HTTP desde backend)
El ESP32 consulta al backend cada 1 hora (configurable) si hay firmware nuevo:
1. `GET /api/v1/firmware/latest?current_version=1.2.0`
2. Si hay version nueva → descarga el `.bin`
3. Verifica MD5 checksum
4. Flash y reinicio automatico

Para subir un nuevo firmware al backend:
```bash
# Desde el panel web (pagina Firmware) o via API:
POST /api/v1/firmware/upload
Content-Type: multipart/form-data
# Adjuntar el archivo .bin generado por PlatformIO
# (ubicado en .pio/build/esp32dev/firmware.bin)
```

---

## 8. Indicadores LED

| Estado LED (GPIO2) | Significado |
|---------------------|-------------|
| Apagado | Boot / Configurando |
| Encendido fijo | Sistema operativo normal |
| Parpadeo rapido | Enviando datos / heartbeat |
| Apagado despues de estar encendido | Error WiFi o reinicio |

---

## 9. Requisitos de Red

- WiFi 2.4 GHz (ESP32 NO soporta 5 GHz)
- El ESP32 debe poder alcanzar el backend por HTTP (puerto 8000)
- Ancho de banda minimo: despreciable (~1 KB cada 30 seg por dispositivo)
- IP del backend debe ser alcanzable desde la red WiFi del ESP32

### Para pruebas locales
El backend corre en Docker en la PC de desarrollo:
```
PC (Docker):  http://<IP_LOCAL>:8000
ESP32:        conectado a la misma red WiFi
```

Verificar la IP local de la PC con `ipconfig` (Windows) o `ifconfig` (Linux).

---

## 10. Lista de Materiales (BOM) - Prueba Basica

| Cant | Componente | Referencia | Notas |
|------|-----------|-----------|-------|
| 1 | ESP32 DevKit v1 | ESP32-WROOM-32 | O NodeMCU-32S |
| 1 | Potenciometro 10K | B10K lineal | 3 pines |
| 3 | Cable dupont | Macho-macho | O macho-hembra |
| 1 | Cable USB | Micro-B o Type-C | Segun placa |
| 1 | Protoboard | 400 puntos | Opcional, para montaje |

### BOM ampliado (sensores adicionales)
| Cant | Componente | Pin ESP32 | Define |
|------|-----------|-----------|--------|
| 1 | DS18B20 + R 4.7K | GPIO4 | `PIN_DS18B20` |
| 1 | DHT22 + R 10K | GPIO5 | `PIN_DHT22` |
| 1 | MPX5700 + divisor voltaje | GPIO34 | `PIN_PRESSURE_ANALOG` |
| 1 | JSN-SR04T | 2 GPIOs | Ver sensor header |

---

## 11. Troubleshooting Rapido

| Problema | Solucion |
|----------|----------|
| No conecta WiFi | Verificar 2.4 GHz. Borrar flash: `pio run -t erase` y re-flashear |
| Portal cautivo no aparece | Ir manualmente a `192.168.4.1` |
| "Backend no responde" en serial | Verificar IP en config, firewall, que Docker este corriendo |
| ADC lee siempre 0 | Verificar conexion a GPIO34. Solo pines 32-39 funcionan con WiFi |
| ADC lee siempre 4095 | Verificar que no este conectado directo a 3.3V sin potenciometro |
| OTA falla | Verificar espacio en flash (4MB). Password debe coincidir en ambos lados |
| No aparece en dashboard | Verificar que Device EUI y API Key coincidan con la DB |
