# 🚀 Guía de Configuración ESP32 - Sistema IoT

**Hardware:** NodeMCU ESP32 WiFi + Bluetooth 4.2 IoT WROOM ESP32S USB-C

**Fecha:** 2025-10-22
**Firmware Version:** 1.1.0

---

## 📋 Tabla de Contenidos

1. [Requisitos Previos](#requisitos-previos)
2. [Instalación de Software](#instalación-de-software)
3. [Configuración del Proyecto](#configuración-del-proyecto)
4. [Conexión de Sensores (Opcional)](#conexión-de-sensores-opcional)
5. [Compilación y Flasheo](#compilación-y-flasheo)
6. [Configuración Zero-Config](#configuración-zero-config)
7. [Verificación y Pruebas](#verificación-y-pruebas)
8. [Troubleshooting](#troubleshooting)

---

## 1. Requisitos Previos

### Hardware Necesario
- ✅ NodeMCU ESP32 WiFi + Bluetooth 4.2 (USB-C)
- ✅ Cable USB-C a USB-A/C (para programación)
- 🔧 (Opcional) Sensores:
  - DS18B20 - Temperatura digital (OneWire)
  - DHT22 - Temperatura + Humedad
  - MPX5700 - Presión analógica

### Software Necesario
- **Sistema Operativo:** Windows 10/11 (ya tienes)
- **Python:** 3.8+ (para PlatformIO)
- **VS Code:** Editor recomendado
- **Git:** Para clonar repositorios

### Backend Funcionando
- ✅ Backend corriendo en: `http://YOUR_SERVER_IP:8000`
- ✅ Endpoint readings disponible: `/api/v1/readings`

---

## 2. Instalación de Software

### Opción A: VS Code + PlatformIO (Recomendado)

#### 2.1. Instalar VS Code
1. Descargar desde: https://code.visualstudio.com/
2. Instalar con opciones por defecto

#### 2.2. Instalar PlatformIO Extension
1. Abrir VS Code
2. Ir a Extensions (Ctrl+Shift+X)
3. Buscar "PlatformIO IDE"
4. Click en "Install"
5. Esperar a que termine la instalación (~5 minutos)
6. Reiniciar VS Code

#### 2.3. Verificar Instalación
1. Click en el ícono de PlatformIO (hormiga) en la barra lateral
2. Deberías ver "PIO Home"

---

### Opción B: Arduino IDE (Alternativa Más Simple)

#### 2.1. Instalar Arduino IDE
1. Descargar Arduino IDE 2.x desde: https://www.arduino.cc/en/software
2. Instalar con opciones por defecto

#### 2.2. Agregar Soporte ESP32
1. Abrir Arduino IDE
2. Ir a `File → Preferences`
3. En "Additional Boards Manager URLs" agregar:
   ```
   https://espressif.github.io/arduino-esp32/package_esp32_index.json
   ```
4. Click OK
5. Ir a `Tools → Board → Boards Manager`
6. Buscar "esp32"
7. Instalar "esp32 by Espressif Systems" (versión 2.0.14+)

#### 2.3. Instalar Librerías
Ir a `Sketch → Include Library → Manage Libraries` e instalar:
- **WiFiManager** by tzapu (v2.0.16-rc.2+)
- **ArduinoJson** by Benoit Blanchon (v6.21.4+)
- **OneWire** by Paul Stoffregen (v2.3.7+)
- **DallasTemperature** by Miles Burton (v3.11.0+)
- **DHT sensor library** by Adafruit (v1.4.4+)
- **Adafruit Unified Sensor** by Adafruit (v1.1.14+)

---

## 3. Configuración del Proyecto

### 3.1. Abrir el Proyecto

**Con PlatformIO (VS Code):**
1. Abrir VS Code
2. `File → Open Folder`
3. Navegar a: `e:\Documentos\Marcelo\Trabajos Idea\Python\Idea_IoT\firmware\esp32-sensor`
4. Click "Select Folder"
5. PlatformIO detectará automáticamente el `platformio.ini`

**Con Arduino IDE:**
1. Abrir `firmware/esp32-sensor/src/main.cpp` con un editor de texto
2. Copiar todo el contenido
3. Abrir Arduino IDE
4. Pegar el código
5. Guardar como `ESP32_IoT_Monitor.ino`

---

### 3.2. Configurar Parámetros en `config.h`

Abrir el archivo: `firmware/esp32-sensor/src/config.h`

**Actualizar estas líneas:**

```cpp
// Línea 23: URL de tu backend (CAMBIAR ESTO)
#define API_BASE_URL "http://YOUR_SERVER_IP:8000/api/v1"

// Línea 32: API Key (temporal para pruebas)
#define DEFAULT_API_KEY "esp32_device_key_change_me"

// Línea 52: Intervalo de muestreo (5 minutos = 300 segundos)
#define SAMPLING_INTERVAL_SEC 300

// Para pruebas más rápidas, cambiar a 30 segundos:
// #define SAMPLING_INTERVAL_SEC 30
```

**Nota:** La API Key se puede configurar después via portal Zero-Config.

---

## 4. Conexión de Sensores (Opcional)

Si **NO** tienes sensores conectados, el ESP32 enviará valores simulados. Si quieres conectar sensores:

### 4.1. Sensor DS18B20 (Temperatura Digital)

**Conexiones:**
- VCC (rojo) → 3.3V del ESP32
- GND (negro) → GND del ESP32
- DATA (amarillo) → GPIO4 (D4)
- **Resistencia pull-up:** 4.7kΩ entre DATA y VCC

### 4.2. Sensor DHT22 (Temperatura + Humedad)

**Conexiones:**
- Pin 1 (VCC) → 3.3V del ESP32
- Pin 2 (DATA) → GPIO5 (D5)
- Pin 3 (NC) → No conectar
- Pin 4 (GND) → GND del ESP32
- **Resistencia pull-up:** 10kΩ entre DATA y VCC

### 4.3. Diagrama de Pines ESP32 WROOM

```
                    ESP32 NodeMCU
            ┌─────────────────────────┐
    3.3V ───┤ 3V3              GPIO4  ├─── DS18B20 DATA
     GND ───┤ GND              GPIO5  ├─── DHT22 DATA
            │                  GPIO34 ├─── Presión Analógica
            │                  GPIO35 ├─── Batería (opcional)
            │                         │
            │         LED_BUILTIN     │
            │         GPIO2           │
    USB-C ──┤                         │
            └─────────────────────────┘
```

---

## 5. Compilación y Flasheo

### Con PlatformIO (VS Code)

#### 5.1. Conectar el ESP32
1. Conectar ESP32 via USB-C a tu PC
2. Windows instalará los drivers automáticamente
3. Verificar el puerto COM en Device Manager (ej: COM3)

#### 5.2. Compilar
1. Click en el ícono de PlatformIO (barra inferior)
2. Click en "Build" (ícono de check ✓)
3. Esperar a que compile (~2 minutos la primera vez)

#### 5.3. Flashear
1. Click en "Upload" (ícono de flecha →)
2. PlatformIO detectará automáticamente el puerto
3. Esperar a que termine el upload (~30 segundos)

#### 5.4. Abrir Monitor Serial
1. Click en "Serial Monitor" (ícono de enchufe 🔌)
2. Velocidad: 115200 baud (automático)
3. Deberías ver logs del firmware

---

### Con Arduino IDE

#### 5.1. Configurar la Placa
1. `Tools → Board → ESP32 Arduino → NodeMCU-32S`
2. `Tools → Upload Speed → 921600`
3. `Tools → Flash Frequency → 80MHz`
4. `Tools → Flash Size → 4MB (32Mb)`
5. `Tools → Port → COMx` (tu puerto USB)

#### 5.2. Compilar y Subir
1. Click en "Verify" (ícono de check ✓)
2. Esperar a que compile
3. Click en "Upload" (ícono de flecha →)
4. Esperar a que termine (~30 segundos)

#### 5.3. Abrir Monitor Serial
1. `Tools → Serial Monitor`
2. Velocidad: 115200 baud
3. Deberías ver logs del firmware

---

## 6. Configuración Zero-Config

Si es la **primera vez** que conectas el ESP32, o si borraste la configuración WiFi:

### 6.1. Detectar Modo AP (Access Point)

Después de flashear, el ESP32 NO podrá conectarse a tu WiFi (porque no tiene credenciales guardadas).

**Logs esperados en Serial Monitor:**
```
========================================
  SISTEMA DE MONITOREO IoT - ESP32
========================================
Firmware Version: 1.0.0
========================================

[SETUP] Paso 1: Conectando a WiFi...
[WIFI] No hay credenciales guardadas
[WIFI] Iniciando modo AP (Access Point)
[WIFI] SSID: ESP32-IoT-XXXXXX
[WIFI] Password: iot_setup_pass
[WIFI] IP del portal: 192.168.4.1
[WIFI] Esperando configuración...
```

### 6.2. Conectarse al Portal Web

#### En tu Celular o Laptop:
1. **Buscar WiFi:** "ESP32-IoT-XXXXXX" (XXXXXX = últimos 6 dígitos de la MAC)
2. **Contraseña:** `iot_setup_pass`
3. **Conectarse**
4. **Abrir navegador:** Debería abrir automáticamente el portal cautivo
   - Si no abre, ir manualmente a: `http://192.168.4.1`

### 6.3. Configurar Parámetros

En el portal web verás un formulario con estos campos:

| Campo | Valor para tu Setup | Descripción |
|-------|---------------------|-------------|
| **WiFi SSID** | `TU_RED_WIFI` | Nombre de tu red WiFi |
| **WiFi Password** | `tu_password_wifi` | Contraseña de tu WiFi |
| **API URL** | `http://YOUR_SERVER_IP:8000/api/v1` | URL del backend |
| **API Key** | `esp32_device_key_change_me` | Key temporal |
| **Device EUI** | `ESP32_LAB_TEST_001` | ID único (o dejar vacío = auto) |
| **Sampling Interval (sec)** | `30` | Intervalo de muestreo (30 seg para pruebas) |

**Importante:**
- El **API URL** debe ser accesible desde la red WiFi del ESP32
- Si backend y ESP32 están en la misma red, usar IP local: `YOUR_SERVER_IP`
- Si están en redes diferentes, necesitarás configurar port forwarding o VPN

### 6.4. Guardar y Conectar

1. Click en "Save" en el portal
2. El ESP32 se reiniciará automáticamente
3. Intentará conectarse a tu WiFi
4. Si tiene éxito, el LED integrado (GPIO2) parpadeará

**Logs esperados después de guardar:**
```
[WIFI] Configuración guardada
[WIFI] Reiniciando...

========================================
  SISTEMA DE MONITOREO IoT - ESP32
========================================

[SETUP] Paso 1: Conectando a WiFi...
[WIFI] Conectando a: TU_RED_WIFI
[WIFI] ✓ Conectado exitosamente
[WIFI] IP asignada: 192.168.1.XXX
[WIFI] Signal strength: -45 dBm (Excelente)

[SETUP] Paso 2: Configurando API Client...
[API] URL configurada: http://YOUR_SERVER_IP:8000/api/v1/readings
[API] Device EUI: ESP32_LAB_TEST_001

[SETUP] Paso 3: Inicializando sensores...
[SENSOR] DS18B20 inicializado en GPIO4
[SENSOR] DHT22 inicializado en GPIO5

[SETUP] Setup completo! ✓
```

---

## 7. Verificación y Pruebas

### 7.1. Verificar Primer Envío de Datos

**En Serial Monitor:**
```
[LOOP] Realizando lectura de sensores...
[SENSOR] DS18B20: 22.5°C (calidad: 1.00)
[SENSOR] DHT22: 23.1°C, 58.3% (calidad: 0.95)

[API] Preparando payload...
[API] Device EUI: ESP32_LAB_TEST_001
[API] Variables: temp_c=22.5, humidity_pct=58.3, rssi_dbm=-45
[API] Quality Score: 0.97

[HTTP] POST http://YOUR_SERVER_IP:8000/api/v1/readings
[HTTP] Request enviado (tamaño: 245 bytes)
[HTTP] Response: 200 OK
[HTTP] ✓ Datos enviados exitosamente
[API] Estadísticas: 1 éxitos, 0 fallos (100.0%)
```

### 7.2. Verificar en el Backend

**Opción 1: Logs de Docker**
```bash
docker-compose logs -f backend
```

Deberías ver:
```
INFO:     192.168.1.XXX - "POST /api/v1/readings HTTP/1.1" 200 OK
```

**Opción 2: Consultar la API**

Abrir navegador o Postman:
```
GET http://YOUR_SERVER_IP:8000/api/v1/readings
```

Deberías ver el reading recién enviado.

### 7.3. Verificar en el Frontend

1. Abrir: `http://localhost:3000`
2. Login: `admin@iot-monitoring.com` / `admin123`
3. Ir a Dashboard
4. Deberías ver tu dispositivo "ESP32_LAB_TEST_001"
5. Click en "Ver detalles →"
6. Deberías ver el gráfico con los datos

---

## 8. Troubleshooting

### Problema 1: ESP32 No Aparece en Puerto COM

**Síntomas:**
- Device Manager no muestra el ESP32
- Arduino IDE no detecta puerto

**Soluciones:**
1. **Instalar drivers CP2102 (USB-Serial):**
   - Descargar de: https://www.silabs.com/developers/usb-to-uart-bridge-vcp-drivers
   - Instalar y reiniciar PC

2. **Verificar cable USB-C:**
   - Usar cable de **datos** (no solo carga)
   - Probar otro cable

3. **Presionar botón BOOT:**
   - Mantener presionado "BOOT" mientras conectas el USB
   - Soltar después de 2 segundos

---

### Problema 2: Error al Compilar

**Error: `WiFiManager.h: No such file or directory`**

**Solución PlatformIO:**
1. Abrir terminal en VS Code (Ctrl+`)
2. Ejecutar: `pio lib install`
3. Esperar a que descargue librerías

**Solución Arduino IDE:**
- Instalar librerías manualmente (ver sección 2.3)

---

### Problema 3: ESP32 No Se Conecta a WiFi

**Logs:**
```
[WIFI] Conectando a: TU_RED_WIFI
[WIFI] ............ (timeout)
[WIFI] ✗ Error: No se pudo conectar
```

**Soluciones:**
1. **Verificar SSID y Password:**
   - Borrar configuración: Mantener presionado GPIO0 al arrancar
   - Volver a configurar via portal AP

2. **Verificar frecuencia WiFi:**
   - ESP32 solo soporta **2.4 GHz** (NO 5 GHz)
   - Asegurar que tu router tenga 2.4 GHz habilitado

3. **Acercar ESP32 al router:**
   - La señal WiFi debe ser fuerte (> -70 dBm)

---

### Problema 4: Error 422 al Enviar Datos

**Logs:**
```
[HTTP] Response: 422 Unprocessable Entity
```

**Causas:**
- Payload JSON malformado
- API Key inválida
- Backend rechaza el device_eui

**Soluciones:**
1. **Verificar API Key:**
   - En `config.h` debe coincidir con la configurada en backend

2. **Verificar estructura JSON:**
   - Abrir Serial Monitor
   - Copiar el JSON enviado
   - Probarlo manualmente con Postman

3. **Crear device en backend:**
   - El `device_eui` debe existir en la tabla `devices`
   - Ejecutar seed script: `docker exec -it iot_backend python scripts/seed.py`

---

### Problema 5: Sensores Retornan -999.0

**Logs:**
```
[SENSOR] DS18B20: -999.0°C (calidad: 0.00)
```

**Causas:**
- Sensor no conectado
- Conexiones flojas
- Resistencia pull-up faltante

**Soluciones:**
1. **Verificar conexiones:**
   - VCC → 3.3V
   - GND → GND
   - DATA → GPIO correcto

2. **Agregar resistencia pull-up:**
   - DS18B20: 4.7kΩ entre DATA y VCC
   - DHT22: 10kΩ entre DATA y VCC

3. **Si no tienes sensores:**
   - El firmware enviará valores simulados (temperatura ~25°C)
   - Esto es normal para pruebas

---

### Problema 6: OTA Updates No Funcionan

**Logs:**
```
[OTA] No se pudo iniciar ArduinoOTA
```

**Soluciones:**
1. **Verificar que estés en la misma red:**
   - ESP32 y PC deben estar en la misma subred

2. **Verificar firewall:**
   - Puerto 3232 debe estar abierto

3. **Configurar IP estática (opcional):**
   - En el router, asignar IP fija al ESP32

---

## 📊 Resumen de Configuración Rápida

Para pruebas inmediatas (sin sensores):

1. **Flashear firmware** con PlatformIO
2. **Conectarse al WiFi AP:** `ESP32-IoT-XXXXXX` (password: `iot_setup_pass`)
3. **Abrir portal:** `http://192.168.4.1`
4. **Configurar:**
   - WiFi SSID: `tu_red_wifi`
   - WiFi Password: `tu_password`
   - API URL: `http://YOUR_SERVER_IP:8000/api/v1`
   - API Key: `esp32_device_key_change_me`
   - Device EUI: `ESP32_LAB_TEST_001`
   - Sampling: `30` segundos
5. **Guardar** y esperar conexión
6. **Verificar** en Dashboard (`http://localhost:3000`)

---

## 🎯 Próximos Pasos

Una vez que el ESP32 esté enviando datos correctamente:

1. **Conectar sensores reales** (DS18B20, DHT22)
2. **Configurar alertas** en el frontend
3. **Ajustar intervalo de muestreo** (300 seg = 5 min)
4. **Probar OTA updates** para actualizar firmware remotamente
5. **Agregar más ESP32** al sistema

---

## 📞 Soporte

Si tienes problemas:
1. Revisar logs en Serial Monitor (115200 baud)
2. Verificar logs del backend: `docker-compose logs -f backend`
3. Consultar documentación de PlatformIO: https://docs.platformio.org/
4. Revisar ejemplos de WiFiManager: https://github.com/tzapu/WiFiManager

---

**Versión de Guía:** 1.0
**Última actualización:** 2025-10-22
**Autor:** Sistema IoT - IdeaMakers
