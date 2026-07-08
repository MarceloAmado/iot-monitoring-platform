/**
 * OTAUpdate.h - Over-The-Air Update Manager para ESP32
 *
 * Características:
 * - Arduino OTA para updates vía WiFi
 * - Verificación de versión antes de actualizar
 * - Progress callback para feedback
 * - Rollback automático en caso de fallo
 * - Password protection
 *
 * Uso:
 * OTAUpdate ota("ESP32_LAB_001");
 * ota.begin();
 *
 * En loop:
 * ota.handle();
 */

#ifndef OTA_UPDATE_H
#define OTA_UPDATE_H

#include <Arduino.h>
#include <WiFi.h>
#include <ArduinoOTA.h>
#include <HTTPClient.h>
#include <HTTPUpdate.h>
#include <ArduinoJson.h>
#include <esp_ota_ops.h>

class OTAUpdate {
private:
    String deviceName;
    String password;
    bool enabled;
    unsigned long lastCheck;
    unsigned long checkInterval; // Configurable

    // HTTP OTA config
    String apiBaseUrl;
    String apiKey;
    String currentVersion;

    /**
     * Callback cuando comienza el update
     */
    static void onStart() {
        String type;
        if (ArduinoOTA.getCommand() == U_FLASH) {
            type = "sketch";
        } else { // U_SPIFFS
            type = "filesystem";
        }

        // NOTE: Si estás actualizando SPIFFS, debes cerrar todos los archivos primero
        Serial.println("\n🔄 OTA Update iniciado: " + type);
    }

    /**
     * Callback de progreso
     */
    static void onProgress(unsigned int progress, unsigned int total) {
        static unsigned int lastPercent = 0;
        unsigned int percent = (progress / (total / 100));

        // Mostrar solo cada 10%
        if (percent != lastPercent && percent % 10 == 0) {
            Serial.printf("⏳ Progreso: %u%%\n", percent);
            lastPercent = percent;
        }
    }

    /**
     * Callback cuando termina exitosamente
     */
    static void onEnd() {
        Serial.println("\n✅ OTA Update completado exitosamente!");
        Serial.println("🔃 Reiniciando en 3 segundos...");
    }

    /**
     * Callback de error
     */
    static void onError(ota_error_t error) {
        Serial.printf("❌ Error[%u]: ", error);
        if (error == OTA_AUTH_ERROR) {
            Serial.println("Auth Failed");
        } else if (error == OTA_BEGIN_ERROR) {
            Serial.println("Begin Failed");
        } else if (error == OTA_CONNECT_ERROR) {
            Serial.println("Connect Failed");
        } else if (error == OTA_RECEIVE_ERROR) {
            Serial.println("Receive Failed");
        } else if (error == OTA_END_ERROR) {
            Serial.println("End Failed");
        }
    }

public:
    /**
     * Constructor
     */
    OTAUpdate(const String& name, const String& pwd = "admin123")
        : deviceName(name), password(pwd), enabled(false), lastCheck(0),
          checkInterval(3600000) {} // Default 1 hora

    /**
     * Configura HTTP OTA (para updates desde backend)
     */
    void configureHTTPOTA(const String& baseUrl, const String& key,
                          const String& version) {
        apiBaseUrl = baseUrl;
        apiKey = key;
        currentVersion = version;
        Serial.println("[OTA] HTTP OTA configurado");
        Serial.printf("  API: %s\n", baseUrl.c_str());
        Serial.printf("  Version: %s\n", version.c_str());
    }

    /**
     * Configura el intervalo de chequeo en segundos
     */
    void setCheckInterval(unsigned long seconds) {
        checkInterval = seconds * 1000;
    }

    /**
     * Inicializa OTA update
     */
    void begin() {
        // Configurar nombre del dispositivo
        ArduinoOTA.setHostname(deviceName.c_str());

        // Configurar password (IMPORTANTE: cambiar en producción)
        if (password.length() > 0) {
            ArduinoOTA.setPassword(password.c_str());
        }

        // Puerto (default 3232)
        ArduinoOTA.setPort(3232);

        // Callbacks
        ArduinoOTA.onStart(onStart);
        ArduinoOTA.onEnd(onEnd);
        ArduinoOTA.onProgress(onProgress);
        ArduinoOTA.onError(onError);

        // Iniciar OTA
        ArduinoOTA.begin();

        enabled = true;
        Serial.println("✓ OTA Update habilitado");
        Serial.printf("  Hostname: %s\n", deviceName.c_str());
        Serial.printf("  Port: %d\n", 3232);
        Serial.println("  Password: ******");
    }

    /**
     * Debe ser llamado en cada loop
     */
    void handle() {
        if (enabled) {
            ArduinoOTA.handle();
        }
    }

    /**
     * Verifica si hay update disponible en el backend y lo aplica.
     *
     * Flujo:
     * 1. GET /api/v1/firmware/latest?current_version=X.Y.Z
     * 2. Si update_available && is_compatible → descarga el .bin
     * 3. Flashea con httpUpdate y reinicia automaticamente
     *
     * @return true si se inicio un update (el ESP32 se reiniciara)
     */
    bool checkForUpdates() {
        unsigned long now = millis();

        if (now - lastCheck < checkInterval) {
            return false;
        }

        lastCheck = now;

        // Necesita HTTP OTA configurado
        if (apiBaseUrl.length() == 0 || apiKey.length() == 0) {
            return false;
        }

        if (!WiFi.isConnected()) {
            Serial.println("[OTA] WiFi no conectado, skip check");
            return false;
        }

        Serial.println("\n[OTA] Verificando updates en backend...");

        // 1. Consultar /firmware/latest
        HTTPClient http;
        String url = apiBaseUrl + "/firmware/latest?current_version=" + currentVersion;

        http.begin(url);
        http.setTimeout(10000);
        http.addHeader("X-API-Key", apiKey);
        http.addHeader("X-Device-EUI", deviceName);

        int httpCode = http.GET();

        if (httpCode != 200) {
            Serial.printf("[OTA] Check failed, HTTP %d\n", httpCode);
            if (httpCode > 0) {
                Serial.println(http.getString());
            }
            http.end();
            return false;
        }

        // 2. Parsear respuesta JSON
        String response = http.getString();
        http.end();

        StaticJsonDocument<512> doc;
        DeserializationError err = deserializeJson(doc, response);
        if (err) {
            Serial.printf("[OTA] JSON parse error: %s\n", err.c_str());
            return false;
        }

        bool updateAvailable = doc["update_available"] | false;
        bool isCompatible = doc["is_compatible"] | false;
        const char* message = doc["message"] | "";
        const char* downloadUrl = doc["download_url"] | "";
        const char* md5 = doc["md5_checksum"] | "";
        int fileSize = doc["file_size_bytes"] | 0;

        Serial.printf("[OTA] %s\n", message);

        if (!updateAvailable) {
            Serial.println("[OTA] Ya estas en la ultima version");
            return false;
        }

        if (!isCompatible) {
            Serial.println("[OTA] Update no compatible con esta version");
            return false;
        }

        if (strlen(downloadUrl) == 0) {
            Serial.println("[OTA] No hay URL de descarga");
            return false;
        }

        // 3. Descargar e instalar firmware
        Serial.println("[OTA] ========================================");
        Serial.printf("[OTA] Descargando firmware (%d bytes)...\n", fileSize);
        Serial.printf("[OTA] URL: %s%s\n", apiBaseUrl.c_str(), downloadUrl);
        Serial.println("[OTA] ========================================");

        String fullUrl = apiBaseUrl + String(downloadUrl);

        // Configurar httpUpdate
        httpUpdate.setLedPin(LED_BUILTIN, LOW);

        // El MD5 lo verifica HTTPUpdate automaticamente: lee el header
        // x-MD5 que envia el backend en /firmware/download
        if (strlen(md5) > 0) {
            Serial.printf("[OTA] MD5 esperado: %s\n", md5);
        }

        // Cliente HTTP con headers de autenticacion; se pasa el HTTPClient
        // a httpUpdate.update() para que la descarga salga autenticada
        WiFiClient client;
        http.begin(client, fullUrl);
        http.addHeader("X-API-Key", apiKey);
        http.addHeader("X-Device-EUI", deviceName);

        t_httpUpdate_return ret = httpUpdate.update(http);
        http.end();

        switch (ret) {
            case HTTP_UPDATE_FAILED:
                Serial.printf("[OTA] Update FAILED (%d): %s\n",
                    httpUpdate.getLastError(),
                    httpUpdate.getLastErrorString().c_str());
                break;

            case HTTP_UPDATE_NO_UPDATES:
                Serial.println("[OTA] No hay updates");
                break;

            case HTTP_UPDATE_OK:
                Serial.println("[OTA] Update OK! Reiniciando...");
                // El ESP32 se reinicia automaticamente
                break;
        }

        return (ret == HTTP_UPDATE_OK);
    }

    /**
     * Obtiene la partición actual (para rollback)
     */
    String getCurrentPartition() {
        const esp_partition_t* partition = esp_ota_get_running_partition();
        if (partition != NULL) {
            return String(partition->label);
        }
        return "unknown";
    }

    /**
     * Obtiene información de la partición
     */
    void printPartitionInfo() {
        const esp_partition_t* running = esp_ota_get_running_partition();
        const esp_partition_t* configured = esp_ota_get_boot_partition();

        Serial.println("\n--- OTA Partition Info ---");
        if (running != NULL) {
            Serial.printf("Running partition: %s (type %d, subtype %d)\n",
                         running->label, running->type, running->subtype);
        }
        if (configured != NULL && configured != running) {
            Serial.printf("Configured boot partition: %s\n", configured->label);
        }
        Serial.println("--------------------------\n");
    }

    /**
     * Marca la partición actual como válida
     * (Llamar después de verificar que el update funciona correctamente)
     */
    void markCurrentPartitionValid() {
        const esp_partition_t* partition = esp_ota_get_running_partition();
        esp_ota_mark_app_valid_cancel_rollback();
        Serial.println("✓ Partición actual marcada como válida");
    }

    /**
     * Rollback a la partición anterior
     */
    void rollbackToPreviousVersion() {
        Serial.println("⚠️ Iniciando rollback a versión anterior...");
        esp_ota_mark_app_invalid_rollback_and_reboot();
    }

    /**
     * Habilitar/deshabilitar OTA
     */
    void setEnabled(bool state) {
        enabled = state;
        if (enabled) {
            Serial.println("✓ OTA habilitado");
        } else {
            Serial.println("✗ OTA deshabilitado");
        }
    }

    /**
     * Verifica si OTA está habilitado
     */
    bool isEnabled() const {
        return enabled;
    }
};

#endif // OTA_UPDATE_H
