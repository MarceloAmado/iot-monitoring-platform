/**
 * WiFi Manager con Zero-Config
 * Portal cautivo para configuración de WiFi sin código
 */

#ifndef WIFI_MANAGER_H
#define WIFI_MANAGER_H

#include <WiFi.h>
#include <WiFiManager.h>  // Librería de tzapu
#include "../config.h"

/**
 * Gestor de conexión WiFi con portal de configuración
 * Si no hay credenciales guardadas, crea un portal AP para configuración
 */
class WiFiConfigManager {
private:
    WiFiManager wifiManager;
    String deviceName;
    bool connected;

    // Parámetros personalizados del portal
    WiFiManagerParameter* param_api_url;
    WiFiManagerParameter* param_api_key;
    WiFiManagerParameter* param_device_eui;
    WiFiManagerParameter* param_sampling_interval;

public:
    /**
     * Constructor
     */
    WiFiConfigManager() : connected(false) {
        // Generar nombre del dispositivo usando MAC Address
        uint8_t mac[6];
        WiFi.macAddress(mac);
        deviceName = String(WIFI_AP_NAME_PREFIX) +
                    String(mac[3], HEX) +
                    String(mac[4], HEX) +
                    String(mac[5], HEX);

        deviceName.toUpperCase();
    }

    /**
     * Inicializa el WiFi Manager
     * Si no hay credenciales guardadas, abre portal de configuración
     *
     * @param forceConfig true para forzar portal de configuración
     * @return true si se conectó exitosamente
     */
    bool begin(bool forceConfig = false) {
        DEBUG_PRINTLN("========================================");
        DEBUG_PRINTLN("[WiFi] Iniciando WiFi Manager");
        DEBUG_PRINTLN("========================================");

        // Configurar callbacks
        wifiManager.setAPCallback(configModeCallback);
        wifiManager.setSaveConfigCallback(saveConfigCallback);

        // Configurar timeout de conexión
        wifiManager.setConfigPortalTimeout(180);  // 3 minutos

        // Agregar parámetros personalizados al portal
        setupCustomParameters();

        // Si se solicita forzar configuración, borrar credenciales
        if (forceConfig) {
            DEBUG_PRINTLN("[WiFi] Forzando modo configuración...");
            wifiManager.resetSettings();
        }

        // LED parpadeo rápido mientras intenta conectar
        pinMode(LED_BUILTIN, OUTPUT);

        // Intentar conectar con credenciales guardadas o abrir portal
        DEBUG_PRINTF("[WiFi] Nombre del AP: %s\n", deviceName.c_str());
        DEBUG_PRINTF("[WiFi] Contraseña del AP: %s\n", WIFI_AP_PASSWORD);

        connected = wifiManager.autoConnect(deviceName.c_str(), WIFI_AP_PASSWORD);

        if (connected) {
            // Conexión exitosa
            DEBUG_PRINTLN("========================================");
            DEBUG_PRINTLN("[WiFi] ✓ Conectado exitosamente");
            DEBUG_PRINTF("[WiFi] IP Address: %s\n", WiFi.localIP().toString().c_str());
            DEBUG_PRINTF("[WiFi] SSID: %s\n", WiFi.SSID().c_str());
            DEBUG_PRINTF("[WiFi] RSSI: %d dBm\n", WiFi.RSSI());
            DEBUG_PRINTF("[WiFi] MAC: %s\n", WiFi.macAddress().c_str());
            DEBUG_PRINTLN("========================================");

            // LED encendido fijo
            digitalWrite(LED_BUILTIN, HIGH);

            // Leer parámetros personalizados guardados
            readCustomParameters();

            return true;
        } else {
            // Timeout o fallo
            DEBUG_ERROR("[WiFi] Timeout del portal de configuración");
            DEBUG_ERROR("[WiFi] Reiniciando...");

            // LED apagado
            digitalWrite(LED_BUILTIN, LOW);

            delay(3000);
            ESP.restart();
            return false;
        }
    }

    /**
     * Verifica el estado de la conexión WiFi
     *
     * @return true si está conectado
     */
    bool isConnected() {
        return WiFi.status() == WL_CONNECTED;
    }

    /**
     * Reconecta si se perdió la conexión
     */
    void maintain() {
        if (!isConnected() && connected) {
            DEBUG_WARN("[WiFi] Conexión perdida. Intentando reconectar...");

            // LED parpadeando
            for (int i = 0; i < 10; i++) {
                digitalWrite(LED_BUILTIN, !digitalRead(LED_BUILTIN));
                delay(200);
            }

            // Intentar reconectar
            WiFi.disconnect();
            WiFi.reconnect();

            int attempts = 0;
            while (!isConnected() && attempts < 20) {
                delay(500);
                DEBUG_PRINT(".");
                attempts++;
            }

            if (isConnected()) {
                DEBUG_PRINTLN("\n[WiFi] ✓ Reconectado exitosamente");
                digitalWrite(LED_BUILTIN, HIGH);
            } else {
                DEBUG_ERROR("\n[WiFi] No se pudo reconectar. Reiniciando...");
                delay(3000);
                ESP.restart();
            }
        }
    }

    /**
     * Resetea la configuración WiFi (borra credenciales)
     */
    void reset() {
        DEBUG_WARN("[WiFi] Reseteando configuración WiFi...");
        wifiManager.resetSettings();
        delay(1000);
        ESP.restart();
    }

    /**
     * Obtiene la intensidad de señal WiFi (RSSI)
     *
     * @return int RSSI en dBm
     */
    int getRSSI() {
        return WiFi.RSSI();
    }

    /**
     * Obtiene la IP local
     *
     * @return String con la IP
     */
    String getIP() {
        return WiFi.localIP().toString();
    }

    /**
     * Obtiene la MAC Address
     *
     * @return String con la MAC
     */
    String getMAC() {
        return WiFi.macAddress();
    }

    /**
     * Obtiene el SSID conectado
     *
     * @return String con el SSID
     */
    String getSSID() {
        return WiFi.SSID();
    }

    /**
     * Obtiene el nombre del dispositivo (AP)
     *
     * @return String con el nombre
     */
    String getDeviceName() {
        return deviceName;
    }

    /**
     * Obtiene parámetro personalizado: API URL
     */
    String getApiUrl() {
        if (param_api_url) {
            return String(param_api_url->getValue());
        }
        return String(API_BASE_URL);
    }

    /**
     * Obtiene parámetro personalizado: API Key
     */
    String getApiKey() {
        if (param_api_key) {
            return String(param_api_key->getValue());
        }
        return String(DEFAULT_API_KEY);
    }

    /**
     * Obtiene parámetro personalizado: Device EUI
     */
    String getDeviceEUI() {
        if (param_device_eui) {
            String eui = String(param_device_eui->getValue());
            if (eui.length() > 0) {
                return eui;
            }
        }
        // Si no hay EUI configurado, generar uno usando MAC
        return "ESP32_" + String(WiFi.macAddress()).substring(12);
    }

    /**
     * Obtiene parámetro personalizado: Intervalo de muestreo
     */
    int getSamplingInterval() {
        if (param_sampling_interval) {
            String interval = String(param_sampling_interval->getValue());
            if (interval.length() > 0) {
                return interval.toInt();
            }
        }
        return SAMPLING_INTERVAL_SEC;
    }

private:
    /**
     * Configura parámetros personalizados del portal
     */
    void setupCustomParameters() {
        // HTML personalizado para el encabezado
        const char* custom_html = "<h3>Configuración del Sistema IoT</h3>";

        // Parámetro: API URL
        param_api_url = new WiFiManagerParameter(
            "api_url",
            "URL del Backend API",
            API_BASE_URL,
            64,
            "placeholder=\"http://192.168.1.100:8000/api/v1\""
        );

        // Parámetro: API Key
        param_api_key = new WiFiManagerParameter(
            "api_key",
            "API Key del Dispositivo",
            DEFAULT_API_KEY,
            64,
            "placeholder=\"esp32_device_key_xxxxx\""
        );

        // Parámetro: Device EUI
        String defaultEUI = "ESP32_" + deviceName.substring(deviceName.length() - 6);
        param_device_eui = new WiFiManagerParameter(
            "device_eui",
            "ID del Dispositivo",
            defaultEUI.c_str(),
            32,
            "placeholder=\"ESP32_LAB_001\""
        );

        // Parámetro: Intervalo de muestreo
        char samplingIntervalStr[8];
        sprintf(samplingIntervalStr, "%d", SAMPLING_INTERVAL_SEC);
        param_sampling_interval = new WiFiManagerParameter(
            "sampling_interval",
            "Intervalo de Muestreo (segundos)",
            samplingIntervalStr,
            6,
            "type=\"number\" min=\"10\" max=\"3600\""
        );

        // Agregar parámetros al WiFi Manager
        wifiManager.addParameter(param_api_url);
        wifiManager.addParameter(param_api_key);
        wifiManager.addParameter(param_device_eui);
        wifiManager.addParameter(param_sampling_interval);
    }

    /**
     * Lee y guarda los parámetros personalizados
     * (En una implementación completa, guardarlos en EEPROM/Preferences)
     */
    void readCustomParameters() {
        DEBUG_PRINTLN("[WiFi] Parámetros configurados:");
        DEBUG_PRINTF("  - API URL: %s\n", getApiUrl().c_str());
        DEBUG_PRINTF("  - Device EUI: %s\n", getDeviceEUI().c_str());
        DEBUG_PRINTF("  - Intervalo: %d seg\n", getSamplingInterval());
        // No mostrar API Key completa por seguridad
        DEBUG_PRINTLN("  - API Key: ***********");
    }

    /**
     * Callback cuando entra en modo de configuración
     */
    static void configModeCallback(WiFiManager *myWiFiManager) {
        DEBUG_PRINTLN("========================================");
        DEBUG_PRINTLN("[WiFi] Modo Portal de Configuración");
        DEBUG_PRINTLN("========================================");
        DEBUG_PRINTF("[WiFi] Conéctate al WiFi: %s\n", myWiFiManager->getConfigPortalSSID().c_str());
        DEBUG_PRINTF("[WiFi] Contraseña: %s\n", WIFI_AP_PASSWORD);
        DEBUG_PRINTLN("[WiFi] Abre tu navegador en: http://192.168.4.1");
        DEBUG_PRINTLN("========================================");

        // LED parpadeando lento en modo configuración
        pinMode(LED_BUILTIN, OUTPUT);
        for (int i = 0; i < 5; i++) {
            digitalWrite(LED_BUILTIN, HIGH);
            delay(300);
            digitalWrite(LED_BUILTIN, LOW);
            delay(300);
        }
    }

    /**
     * Callback cuando se guarda la configuración
     */
    static void saveConfigCallback() {
        DEBUG_PRINTLN("[WiFi] ✓ Configuración guardada");
        DEBUG_PRINTLN("[WiFi] Reiniciando...");
    }
};

#endif // WIFI_MANAGER_H
