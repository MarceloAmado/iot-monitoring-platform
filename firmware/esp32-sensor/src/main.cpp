/**
 * Sistema de Monitoreo IoT - Firmware ESP32
 *
 * Funcionalidades:
 * - Zero-Config WiFi (portal cautivo)
 * - Lectura de múltiples sensores (DS18B20, DHT22)
 * - Envío de datos al backend vía HTTP POST
 * - Quality score de lecturas
 * - Detección de fallas de sensores
 * - OTA updates con ArduinoOTA
 *
 * @author Sistema IoT
 * @version 1.1.0
 * @date 2025-10-20
 */

#include <Arduino.h>
#include <vector>
#include <WiFi.h>
#include <ArduinoJson.h>

#include "config.h"
#include "sensors/Sensor.h"
#include "sensors/DS18B20Sensor.h"
#include "sensors/DHT22Sensor.h"
#include "sensors/MPX5700Sensor.h"
#include "sensors/AnalogSensor.h"
#include "network/WiFiManager.h"
#include "network/APIClient.h"
#include "utils/OTAUpdate.h"

// ============================================================================
// INSTANCIAS GLOBALES
// ============================================================================

// WiFi Manager
WiFiConfigManager wifiManager;

// API Client (se configurará después del WiFi)
APIClient* apiClient = nullptr;

// OTA Update Manager (se configurará después del WiFi)
OTAUpdate* otaManager = nullptr;

// Vector de sensores
std::vector<Sensor*> sensors;

// Configuración runtime (se obtiene del WiFi Manager)
String deviceEUI;
String apiUrl;
String apiKey;
int samplingIntervalSec;

// Control de timing
unsigned long lastSampleTime = 0;
unsigned long lastHealthCheckTime = 0;
unsigned long lastHeartbeatTime = 0;
unsigned long bootTime = 0;

// Configuración de heartbeat
#define HEARTBEAT_INTERVAL_SEC 60  // Enviar heartbeat cada 60 segundos (si NO hay sensores)

// Versión del firmware (usada para OTA y heartbeat)
#define FIRMWARE_VERSION "1.2.0"

// ============================================================================
// DECLARACIÓN DE FUNCIONES
// ============================================================================

void setupSensors();
void performSensorReading();
void sendDataToBackend(JsonObject dataPayload);
void sendHeartbeat();
float calculateOverallQuality(JsonObject data);
void printSystemInfo();
void performHealthCheck();
String getTimestamp();

// ============================================================================
// SETUP
// ============================================================================

void setup() {
    // Inicializar Serial
    Serial.begin(115200);
    delay(1000);  // Esperar a que el Serial esté listo

    DEBUG_PRINTLN("\n\n\n");
    DEBUG_PRINTLN("========================================");
    DEBUG_PRINTLN("  SISTEMA DE MONITOREO IoT - ESP32");
    DEBUG_PRINTLN("========================================");
    DEBUG_PRINTF("Firmware Version: %s\n", FIRMWARE_VERSION);
    DEBUG_PRINTF("Build Date: %s %s\n", __DATE__, __TIME__);
    DEBUG_PRINTLN("========================================");

    bootTime = millis();

    // LED de status
    pinMode(LED_BUILTIN, OUTPUT);
    digitalWrite(LED_BUILTIN, LOW);

    // ========================================================================
    // PASO 1: Conectar WiFi (con Zero-Config si es necesario)
    // ========================================================================

    DEBUG_PRINTLN("\n[SETUP] Paso 1: Conectando a WiFi...");

    if (!wifiManager.begin()) {
        DEBUG_ERROR("[SETUP] Fallo al conectar WiFi. El dispositivo se reiniciará.");
        delay(5000);
        ESP.restart();
    }

    // Obtener configuración del WiFi Manager
    deviceEUI = wifiManager.getDeviceEUI();
    apiUrl = wifiManager.getApiUrl();
    apiKey = wifiManager.getApiKey();
    samplingIntervalSec = wifiManager.getSamplingInterval();

    DEBUG_PRINTLN("[SETUP] Configuración obtenida:");
    DEBUG_PRINTF("  Device EUI: %s\n", deviceEUI.c_str());
    DEBUG_PRINTF("  API URL: %s\n", apiUrl.c_str());
    DEBUG_PRINTF("  Intervalo: %d seg\n", samplingIntervalSec);

    // Crear API Client
    apiClient = new APIClient(apiUrl, apiKey);

    // ========================================================================
    // PASO 2: Configurar OTA Updates
    // ========================================================================

    #if ENABLE_OTA
    DEBUG_PRINTLN("\n[SETUP] Paso 2: Configurando OTA Updates...");

    otaManager = new OTAUpdate(deviceEUI, OTA_PASSWORD);
    otaManager->begin();
    otaManager->printPartitionInfo();

    // Configurar HTTP OTA (updates desde backend)
    otaManager->configureHTTPOTA(apiUrl, apiKey, FIRMWARE_VERSION);
    otaManager->setCheckInterval(OTA_CHECK_INTERVAL_SEC);

    // Marcar partición actual como válida (después de boot exitoso)
    // Esto permite rollback automático si el nuevo firmware falla
    otaManager->markCurrentPartitionValid();

    DEBUG_PRINTLN("[SETUP] OTA Updates configurado correctamente");
    #endif

    // ========================================================================
    // PASO 3: Inicializar sensores
    // ========================================================================

    DEBUG_PRINTLN("\n[SETUP] Paso 3: Inicializando sensores...");
    setupSensors();

    // ========================================================================
    // PASO 3: Test de conexión al backend
    // ========================================================================

    DEBUG_PRINTLN("\n[SETUP] Paso 3: Verificando conexión con backend...");

    bool backendOk = apiClient->testConnection();

    if (backendOk) {
        DEBUG_PRINTLN("[SETUP] ✓ Backend accesible");
    } else {
        DEBUG_WARN("[SETUP] Backend no responde. Se intentará enviar datos de todas formas.");
    }

    // ========================================================================
    // PASO 4: Información del sistema
    // ========================================================================

    DEBUG_PRINTLN("\n[SETUP] Paso 4: Información del sistema");
    printSystemInfo();

    // ========================================================================
    // PASO 5: Primera lectura inmediata
    // ========================================================================

    DEBUG_PRINTLN("\n[SETUP] Paso 5: Primera lectura de sensores...");
    delay(2000);  // Dar tiempo a que los sensores se estabilicen
    performSensorReading();

    // ========================================================================
    // SETUP COMPLETADO
    // ========================================================================

    DEBUG_PRINTLN("\n========================================");
    DEBUG_PRINTLN("  ✓ SETUP COMPLETADO EXITOSAMENTE");
    DEBUG_PRINTF("  Tiempo de boot: %lu ms\n", millis() - bootTime);
    DEBUG_PRINTLN("========================================");
    DEBUG_PRINTF("\nPróxima lectura en %d segundos...\n\n", samplingIntervalSec);

    // LED encendido = sistema listo
    digitalWrite(LED_BUILTIN, HIGH);
}

// ============================================================================
// LOOP PRINCIPAL
// ============================================================================

void loop() {
    unsigned long currentTime = millis();

    // Verificar conexión WiFi (reconectar si es necesario)
    wifiManager.maintain();

    // Handle OTA updates (IMPORTANTE: debe ser llamado en cada loop)
    #if ENABLE_OTA
    if (otaManager != nullptr) {
        otaManager->handle();
    }
    #endif

    // Verificar si es tiempo de hacer una lectura
    if (currentTime - lastSampleTime >= (samplingIntervalSec * 1000)) {
        lastSampleTime = currentTime;

        // Parpadeo LED indicando actividad
        digitalWrite(LED_BUILTIN, LOW);
        delay(100);
        digitalWrite(LED_BUILTIN, HIGH);

        // Realizar lectura de sensores
        performSensorReading();
    }

    // Health check cada 5 minutos
    if (currentTime - lastHealthCheckTime >= 300000) {  // 5 min
        lastHealthCheckTime = currentTime;
        performHealthCheck();
    }

    // Verificar HTTP OTA updates desde backend
    #if ENABLE_OTA
    if (otaManager != nullptr) {
        otaManager->checkForUpdates();
        // Si hay update, el ESP32 se reinicia automaticamente
    }
    #endif

    // Heartbeat cada 60 segundos (solo si NO hay sensores o para mantener online)
    // Si hay sensores activos, los readings ya actualizan last_seen_at
    if (currentTime - lastHeartbeatTime >= (HEARTBEAT_INTERVAL_SEC * 1000)) {
        lastHeartbeatTime = currentTime;

        // Enviar heartbeat solo si:
        // 1. No hay sensores conectados, O
        // 2. Los sensores no están enviando datos regularmente
        if (sensors.size() == 0 || samplingIntervalSec > 120) {
            sendHeartbeat();
        }
    }

    // Pequeño delay para no saturar el CPU
    delay(100);
}

// ============================================================================
// IMPLEMENTACIÓN DE FUNCIONES
// ============================================================================

/**
 * Inicializa todos los sensores registrados
 */
void setupSensors() {
    DEBUG_PRINTLN("[SENSORS] Registrando sensores...");

    // Sensor de temperatura DS18B20 (opcional)
    #ifdef PIN_DS18B20
        DEBUG_PRINTLN("[SENSORS] Agregando DS18B20...");
        sensors.push_back(new DS18B20Sensor(PIN_DS18B20));
    #endif

    // Sensor de temperatura y humedad DHT22
    #ifdef PIN_DHT22
        DEBUG_PRINTLN("[SENSORS] Agregando DHT22...");
        sensors.push_back(new DHT22Sensor(PIN_DHT22));
    #endif

    // Sensor de presión MPX5700 (opcional)
    #ifdef PIN_PRESSURE_ANALOG
        DEBUG_PRINTLN("[SENSORS] Agregando MPX5700 (Presión)...");
        sensors.push_back(new MPX5700Sensor(PIN_PRESSURE_ANALOG));
    #endif

    // Sensor analógico genérico (potenciómetro, LDR, etc.)
    #ifdef PIN_ANALOG_SENSOR
        DEBUG_PRINTLN("[SENSORS] Agregando sensor analógico...");
        sensors.push_back(new AnalogSensor(PIN_ANALOG_SENSOR, ANALOG_SENSOR_LABEL));
    #endif

    // Inicializar todos los sensores
    DEBUG_PRINTF("[SENSORS] Inicializando %d sensores...\n", sensors.size());

    for (auto sensor : sensors) {
        DEBUG_PRINTF("[SENSORS] Inicializando %s...\n", sensor->getType().c_str());
        sensor->begin();
        delay(500);  // Dar tiempo entre sensores
    }

    DEBUG_PRINTF("[SENSORS] ✓ %d sensores inicializados\n", sensors.size());
}

/**
 * Realiza lectura de todos los sensores y envía al backend
 */
void performSensorReading() {
    DEBUG_PRINTLN("\n========================================");
    DEBUG_PRINTLN("[READING] Iniciando lectura de sensores");
    DEBUG_PRINTLN("========================================");

    unsigned long readingStartTime = millis();

    // Crear documento JSON para el payload
    StaticJsonDocument<JSON_BUFFER_SIZE> doc;
    JsonObject dataPayload = doc.to<JsonObject>();

    // Leer todos los sensores
    int sensorsRead = 0;
    int sensorsHealthy = 0;

    for (auto sensor : sensors) {
        String sensorType = sensor->getType();

        DEBUG_PRINTF("\n[READING] Leyendo sensor: %s\n", sensorType.c_str());

        // Verificar salud del sensor
        if (!sensor->isHealthy()) {
            DEBUG_WARN("[READING] ⚠ Sensor no saludable");
            continue;
        }

        sensorsHealthy++;

        // Leer datos del sensor
        StaticJsonDocument<128> sensorDoc;
        JsonObject sensorData = sensor->read(sensorDoc);

        // Agregar datos al payload principal
        for (JsonPair kv : sensorData) {
            dataPayload[kv.key()] = kv.value();
            DEBUG_PRINTF("[READING]   %s: ", kv.key().c_str());
            serializeJson(kv.value(), Serial);
            DEBUG_PRINTLN();
        }

        sensorsRead++;
    }

    DEBUG_PRINTF("\n[READING] Sensores leídos: %d/%d saludables\n",
                sensorsHealthy, sensors.size());

    // Agregar metadata del dispositivo
    DEBUG_PRINTLN("\n[READING] Agregando metadata del dispositivo...");

    // RSSI WiFi
    int rssi = wifiManager.getRSSI();
    dataPayload["rssi_dbm"] = rssi;
    DEBUG_PRINTF("[READING]   rssi_dbm: %d\n", rssi);

    // Uptime
    unsigned long uptimeSec = millis() / 1000;
    dataPayload["uptime_sec"] = uptimeSec;
    DEBUG_PRINTF("[READING]   uptime_sec: %lu\n", uptimeSec);

    // Free heap
    uint32_t freeHeap = ESP.getFreeHeap();
    dataPayload["free_heap_bytes"] = freeHeap;
    DEBUG_PRINTF("[READING]   free_heap_bytes: %u\n", freeHeap);

    // Voltaje de batería (si está conectado)
    #ifdef PIN_BATTERY
        float batteryVoltage = analogRead(PIN_BATTERY) * (3.3 / 4096.0) * 2.0;
        dataPayload["battery_v"] = batteryVoltage;
        DEBUG_PRINTF("[READING]   battery_v: %.2f\n", batteryVoltage);
    #endif

    // Calcular quality score general
    float qualityScore = calculateOverallQuality(dataPayload);
    DEBUG_PRINTF("\n[READING] Quality Score: %.2f\n", qualityScore);

    // Tiempo de lectura
    unsigned long readingTime = millis() - readingStartTime;
    DEBUG_PRINTF("[READING] Tiempo de lectura: %lu ms\n", readingTime);

    // Enviar al backend
    DEBUG_PRINTLN("\n[READING] Enviando datos al backend...");
    sendDataToBackend(dataPayload);

    DEBUG_PRINTLN("========================================");
    DEBUG_PRINTLN("[READING] Lectura completada");
    DEBUG_PRINTLN("========================================\n");
}

/**
 * Envía datos al backend
 */
void sendDataToBackend(JsonObject dataPayload) {
    if (!wifiManager.isConnected()) {
        DEBUG_ERROR("[BACKEND] WiFi no conectado. No se puede enviar.");
        return;
    }

    // Enviar con retry automático
    bool success = apiClient->postReadingWithRetry(deviceEUI, dataPayload);

    if (success) {
        DEBUG_PRINTLN("[BACKEND] ✓ Datos enviados exitosamente");
    } else {
        DEBUG_ERROR("[BACKEND] ✗ Error al enviar datos");
    }
}

/**
 * Calcula un quality score general basado en todas las lecturas
 */
float calculateOverallQuality(JsonObject data) {
    int validReadings = 0;
    int totalReadings = 0;

    for (JsonPair kv : data) {
        // Solo considerar valores numéricos de sensores
        if (kv.value().is<float>() || kv.value().is<int>()) {
            totalReadings++;

            float value = kv.value().as<float>();

            // Si no es un error, contar como válido
            if (value != SENSOR_ERROR_VALUE && !isnan(value)) {
                validReadings++;
            }
        }
    }

    if (totalReadings == 0) {
        return 0.0;
    }

    return (float)validReadings / totalReadings;
}

/**
 * Imprime información del sistema
 */
void printSystemInfo() {
    DEBUG_PRINTLN("========================================");
    DEBUG_PRINTLN("INFORMACIÓN DEL SISTEMA");
    DEBUG_PRINTLN("========================================");

    DEBUG_PRINTLN("\n[WIFI]");
    DEBUG_PRINTF("  SSID: %s\n", wifiManager.getSSID().c_str());
    DEBUG_PRINTF("  IP: %s\n", wifiManager.getIP().c_str());
    DEBUG_PRINTF("  MAC: %s\n", wifiManager.getMAC().c_str());
    DEBUG_PRINTF("  RSSI: %d dBm\n", wifiManager.getRSSI());

    DEBUG_PRINTLN("\n[ESP32]");
    DEBUG_PRINTF("  Chip Model: %s\n", ESP.getChipModel());
    DEBUG_PRINTF("  Chip Revision: %d\n", ESP.getChipRevision());
    DEBUG_PRINTF("  CPU Freq: %d MHz\n", ESP.getCpuFreqMHz());
    DEBUG_PRINTF("  Flash Size: %u MB\n", ESP.getFlashChipSize() / (1024 * 1024));
    DEBUG_PRINTF("  Free Heap: %u bytes\n", ESP.getFreeHeap());
    DEBUG_PRINTF("  SDK Version: %s\n", ESP.getSdkVersion());

    DEBUG_PRINTLN("\n[SENSORES]");
    DEBUG_PRINTF("  Sensores registrados: %d\n", sensors.size());
    for (auto sensor : sensors) {
        DEBUG_PRINTF("    - %s: %s\n",
                    sensor->getType().c_str(),
                    sensor->isHealthy() ? "OK" : "FALLA");
    }

    DEBUG_PRINTLN("\n========================================");
}

/**
 * Realiza health check del sistema
 */
void performHealthCheck() {
    DEBUG_PRINTLN("\n========================================");
    DEBUG_PRINTLN("[HEALTH CHECK]");
    DEBUG_PRINTLN("========================================");

    // Verificar WiFi
    DEBUG_PRINTF("WiFi: %s (RSSI: %d dBm)\n",
                wifiManager.isConnected() ? "✓ OK" : "✗ FAIL",
                wifiManager.getRSSI());

    // Verificar sensores
    int healthySensors = 0;
    for (auto sensor : sensors) {
        if (sensor->isHealthy()) {
            healthySensors++;
        }
        DEBUG_PRINTF("Sensor %s: %s\n",
                    sensor->getType().c_str(),
                    sensor->isHealthy() ? "✓ OK" : "✗ FAIL");
    }

    // Verificar memoria
    uint32_t freeHeap = ESP.getFreeHeap();
    DEBUG_PRINTF("Free Heap: %u bytes\n", freeHeap);

    if (freeHeap < 10000) {
        DEBUG_WARN("⚠ Poca memoria libre!");
    }

    // Uptime
    unsigned long uptimeSec = millis() / 1000;
    unsigned long days = uptimeSec / 86400;
    unsigned long hours = (uptimeSec % 86400) / 3600;
    unsigned long minutes = (uptimeSec % 3600) / 60;

    DEBUG_PRINTF("Uptime: %lud %luh %lum\n", days, hours, minutes);

    // Estadísticas del API
    apiClient->printStats();

    DEBUG_PRINTLN("========================================\n");
}

/**
 * Envía heartbeat al backend
 *
 * Reporta que el ESP32 está vivo aunque no tenga sensores conectados.
 * Envía metadata del sistema (RSSI, heap, uptime, etc.)
 */
void sendHeartbeat() {
    DEBUG_PRINTLN("\n========================================");
    DEBUG_PRINTLN("[HEARTBEAT] Enviando heartbeat al backend");
    DEBUG_PRINTLN("========================================");

    if (apiClient == nullptr) {
        DEBUG_ERROR("[HEARTBEAT] API Client no inicializado");
        return;
    }

    // Crear metadata personalizada
    StaticJsonDocument<256> doc;
    JsonObject metadata = doc.to<JsonObject>();

    // Información de WiFi
    metadata["rssi_dbm"] = WiFi.RSSI();
    metadata["wifi_ssid"] = WiFi.SSID();
    metadata["ip_address"] = WiFi.localIP().toString();

    // Información de sistema
    metadata["free_heap_bytes"] = ESP.getFreeHeap();
    metadata["uptime_sec"] = millis() / 1000;

    // Información de sensores
    metadata["sensors_count"] = sensors.size();
    metadata["sampling_interval_sec"] = samplingIntervalSec;

    // Enviar heartbeat con retry
    bool success = apiClient->sendHeartbeatWithRetry(deviceEUI, FIRMWARE_VERSION, metadata);

    if (success) {
        DEBUG_PRINTLN("[HEARTBEAT] ✓ Heartbeat enviado exitosamente");

        // Parpadeo LED indicando actividad
        digitalWrite(LED_BUILTIN, LOW);
        delay(50);
        digitalWrite(LED_BUILTIN, HIGH);
    } else {
        DEBUG_ERROR("[HEARTBEAT] ✗ Error al enviar heartbeat");
    }

    DEBUG_PRINTLN("========================================\n");
}

/**
 * Obtiene timestamp actual (simplificado, usar NTP en producción)
 */
String getTimestamp() {
    // TODO: Implementar NTP para timestamp real
    // Por ahora, el backend usará NOW() si no se proporciona timestamp
    return "";
}
