/**
 * Configuración del Firmware ESP32
 * Sistema de Monitoreo IoT
 */

#ifndef CONFIG_H
#define CONFIG_H

// ============================================================================
// CONFIGURACIÓN DE RED
// ============================================================================

// WiFi Manager Portal AP
#define WIFI_AP_NAME_PREFIX "ESP32-IoT-"  // + MAC Address
#define WIFI_AP_PASSWORD "iot_setup_pass"      // Contraseña del portal AP
#define WIFI_CONNECT_TIMEOUT_SEC 30       // Timeout para conexión WiFi

// ============================================================================
// CONFIGURACIÓN DEL BACKEND API
// ============================================================================

// URL del backend (se puede configurar vía WiFi Manager)
#define API_BASE_URL "http://YOUR_SERVER_IP:8000/api/v1"
#define API_ENDPOINT_READINGS "/readings"

// Device EUI (ID único del dispositivo)
// Se auto-genera usando MAC Address si no se define
// #define DEVICE_EUI "ESP32_LAB_001"

// API Key (se debe configurar vía WiFi Manager o hardcodear temporalmente)
// NUNCA commitear la API key real en producción
#define DEFAULT_API_KEY "esp32_device_key_change_me"

// ============================================================================
// CONFIGURACIÓN DE SENSORES
// ============================================================================

// Pines de sensores
// Comentar/descomentar según los sensores conectados
// #define PIN_DS18B20 4           // GPIO4 - Sensor de temperatura DS18B20 (OneWire)
// #define PIN_DHT22 5             // GPIO5 - Sensor DHT22 (Temp + Humedad)
// #define PIN_PRESSURE_ANALOG 34  // GPIO34 (ADC1_6) - Sensor de presión analógico MPX5700
// #define PIN_BATTERY 35          // GPIO35 (ADC1_7) - Voltaje de batería (divisor de voltaje)

// Sensor analógico genérico (potenciómetro, LDR, etc.)
#define PIN_ANALOG_SENSOR 34        // GPIO34 (ADC1_6) - Pin analógico
#define ANALOG_SENSOR_LABEL "pot"   // Etiqueta en JSON: pot_raw, pot_v, pot_pct

// Configuración DHT22
#define DHT_TYPE DHT22

// ============================================================================
// CONFIGURACIÓN DE MUESTREO
// ============================================================================

// Intervalo de muestreo en segundos
#define SAMPLING_INTERVAL_SEC 30  // 30 seg para testing (producción: 300)

// Intervalo mínimo entre muestras (para evitar spam)
#define MIN_SAMPLING_INTERVAL_SEC 10  // 10 segundos

// ============================================================================
// CONFIGURACIÓN DE OTA (Over-The-Air Updates)
// ============================================================================

// Habilitar OTA updates
#define ENABLE_OTA true

// Puerto OTA
#define OTA_PORT 3232

// Password OTA (cambiar en producción)
#define OTA_PASSWORD "CHANGE_ME_OTA_PASSWORD"

// Intervalo de chequeo de OTA (en segundos)
#define OTA_CHECK_INTERVAL_SEC 3600  // 1 hora

// ============================================================================
// CONFIGURACIÓN DE CALIDAD DE DATOS
// ============================================================================

// Valores de error para sensores
#define SENSOR_ERROR_VALUE -999.0

// Thresholds para quality score
#define QUALITY_SCORE_EXCELLENT 1.0
#define QUALITY_SCORE_GOOD 0.8
#define QUALITY_SCORE_ACCEPTABLE 0.5
#define QUALITY_SCORE_POOR 0.3

// ============================================================================
// CONFIGURACIÓN DE DEBUG
// ============================================================================

// Habilitar debug serial
#define ENABLE_SERIAL_DEBUG true

// Nivel de debug (0 = none, 1 = error, 2 = warn, 3 = info, 4 = debug)
#ifndef DEBUG_LEVEL
#define DEBUG_LEVEL 3
#endif

// ============================================================================
// MACROS DE DEBUG
// ============================================================================

#if ENABLE_SERIAL_DEBUG
  #define DEBUG_PRINT(x) Serial.print(x)
  #define DEBUG_PRINTLN(x) Serial.println(x)
  #define DEBUG_PRINTF(fmt, ...) Serial.printf(fmt, ##__VA_ARGS__)
#else
  #define DEBUG_PRINT(x)
  #define DEBUG_PRINTLN(x)
  #define DEBUG_PRINTF(fmt, ...)
#endif

#if DEBUG_LEVEL >= 1
  #define DEBUG_ERROR(x) Serial.print("[ERROR] "); Serial.println(x)
#else
  #define DEBUG_ERROR(x)
#endif

#if DEBUG_LEVEL >= 2
  #define DEBUG_WARN(x) Serial.print("[WARN] "); Serial.println(x)
#else
  #define DEBUG_WARN(x)
#endif

#if DEBUG_LEVEL >= 3
  #define DEBUG_INFO(x) Serial.print("[INFO] "); Serial.println(x)
#else
  #define DEBUG_INFO(x)
#endif

#if DEBUG_LEVEL >= 4
  #define DEBUG_DEBUG(x) Serial.print("[DEBUG] "); Serial.println(x)
#else
  #define DEBUG_DEBUG(x)
#endif

// ============================================================================
// CONFIGURACIÓN DE HARDWARE
// ============================================================================

// LED integrado
#define LED_BUILTIN 2

// ============================================================================
// CONSTANTES DEL SISTEMA
// ============================================================================

// Tamaño del buffer JSON
#define JSON_BUFFER_SIZE 512

// Timeout HTTP en milisegundos
#define HTTP_TIMEOUT_MS 10000

// Reintentos HTTP
#define HTTP_MAX_RETRIES 3

#endif // CONFIG_H
