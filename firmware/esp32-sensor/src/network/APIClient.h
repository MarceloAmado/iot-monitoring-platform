/**
 * Cliente HTTP para comunicación con el Backend API
 * Envía readings de sensores vía POST
 */

#ifndef API_CLIENT_H
#define API_CLIENT_H

#include <HTTPClient.h>
#include <WiFi.h>
#include <ArduinoJson.h>
#include "../config.h"

/**
 * Cliente HTTP para enviar datos al backend
 */
class APIClient {
private:
    String apiBaseUrl;
    String apiKey;
    HTTPClient http;

    // Estadísticas
    unsigned long totalRequests;
    unsigned long successfulRequests;
    unsigned long failedRequests;
    unsigned long lastRequestTime;
    int lastHttpCode;

public:
    /**
     * Constructor
     *
     * @param baseUrl URL base del API (ej: "http://192.168.1.100:8000/api/v1")
     * @param key API Key para autenticación
     */
    APIClient(String baseUrl, String key)
        : apiBaseUrl(baseUrl),
          apiKey(key),
          totalRequests(0),
          successfulRequests(0),
          failedRequests(0),
          lastRequestTime(0),
          lastHttpCode(0) {
    }

    /**
     * Actualiza la API Key
     *
     * @param key Nueva API Key
     */
    void setApiKey(String key) {
        apiKey = key;
    }

    /**
     * Actualiza la URL base
     *
     * @param url Nueva URL base
     */
    void setBaseUrl(String url) {
        apiBaseUrl = url;
    }

    /**
     * Envía una lectura de sensor al backend
     *
     * @param deviceEUI ID único del dispositivo
     * @param dataPayload Objeto JSON con los datos del sensor
     * @param timestamp Timestamp de la medición (opcional)
     * @return true si se envió exitosamente
     */
    bool postReading(String deviceEUI, JsonObject dataPayload, String timestamp = "") {
        if (!WiFi.isConnected()) {
            DEBUG_ERROR("[API] WiFi no conectado");
            return false;
        }

        totalRequests++;
        lastRequestTime = millis();

        // Construir URL completa
        String url = apiBaseUrl + API_ENDPOINT_READINGS;

        DEBUG_PRINTLN("========================================");
        DEBUG_PRINTLN("[API] Enviando reading al backend");
        DEBUG_PRINTF("[API] URL: %s\n", url.c_str());

        // Crear documento JSON
        StaticJsonDocument<JSON_BUFFER_SIZE> doc;

        // Datos obligatorios
        doc["device_eui"] = deviceEUI;
        doc["data_payload"] = dataPayload;

        // Timestamp (si no se proporciona, el backend usará NOW())
        if (timestamp.length() > 0) {
            doc["timestamp"] = timestamp;
        }

        // Serializar a string
        String jsonBody;
        serializeJson(doc, jsonBody);

        DEBUG_PRINTLN("[API] Payload JSON:");
        DEBUG_PRINTLN(jsonBody);

        // Configurar HTTP client
        http.begin(url);
        http.setTimeout(HTTP_TIMEOUT_MS);

        // Headers de autenticación: el backend exige X-API-Key Y X-Device-EUI
        // (contrato de validate_device_api_key; sin el EUI responde 422)
        http.addHeader("Content-Type", "application/json");
        http.addHeader("X-API-Key", apiKey);
        http.addHeader("X-Device-EUI", deviceEUI);
        http.addHeader("User-Agent", "ESP32-IoT-Sensor/1.0");

        // Enviar POST request
        int httpCode = http.POST(jsonBody);
        lastHttpCode = httpCode;

        DEBUG_PRINTF("[API] HTTP Response Code: %d\n", httpCode);

        // Verificar respuesta
        bool success = false;

        if (httpCode > 0) {
            String response = http.getString();

            if (httpCode == 200 || httpCode == 201) {
                // Success
                DEBUG_PRINTLN("[API] ✓ Reading enviado exitosamente");

                // Parsear respuesta
                StaticJsonDocument<256> responseDoc;
                DeserializationError error = deserializeJson(responseDoc, response);

                if (!error) {
                    DEBUG_PRINTLN("[API] Respuesta del servidor:");
                    if (responseDoc.containsKey("id")) {
                        DEBUG_PRINTF("[API]   - Reading ID: %d\n", responseDoc["id"].as<int>());
                    }
                    if (responseDoc.containsKey("quality_score")) {
                        DEBUG_PRINTF("[API]   - Quality Score: %.2f\n",
                                    responseDoc["quality_score"].as<float>());
                    }
                }

                successfulRequests++;
                success = true;

            } else if (httpCode == 400) {
                DEBUG_ERROR("[API] Error 400: Bad Request");
                DEBUG_PRINTLN(response);
            } else if (httpCode == 401) {
                DEBUG_ERROR("[API] Error 401: No autorizado (verificar API Key)");
            } else if (httpCode == 404) {
                DEBUG_ERROR("[API] Error 404: Endpoint no encontrado");
                DEBUG_ERROR("[API] Verificar URL del API");
            } else if (httpCode == 500) {
                DEBUG_ERROR("[API] Error 500: Error interno del servidor");
                DEBUG_PRINTLN(response);
            } else {
                DEBUG_ERROR("[API] Error HTTP desconocido");
                DEBUG_PRINTLN(response);
            }

            if (!success) {
                failedRequests++;
            }

        } else {
            // Error de conexión HTTP
            DEBUG_ERROR("[API] Error de conexión HTTP");
            DEBUG_PRINTF("[API] Error: %s\n", http.errorToString(httpCode).c_str());
            failedRequests++;
        }

        // Cerrar conexión
        http.end();

        DEBUG_PRINTLN("========================================");

        return success;
    }

    /**
     * Envía una lectura con retry automático
     *
     * @param deviceEUI ID único del dispositivo
     * @param dataPayload Objeto JSON con los datos
     * @param maxRetries Número máximo de reintentos
     * @return true si se envió exitosamente
     */
    bool postReadingWithRetry(String deviceEUI, JsonObject dataPayload, int maxRetries = HTTP_MAX_RETRIES) {
        int attempts = 0;

        while (attempts < maxRetries) {
            if (postReading(deviceEUI, dataPayload)) {
                return true;
            }

            attempts++;
            if (attempts < maxRetries) {
                DEBUG_PRINTF("[API] Reintentando... (%d/%d)\n", attempts, maxRetries);
                delay(2000 * attempts);  // Backoff exponencial
            }
        }

        DEBUG_ERROR("[API] ✗ Falló después de todos los reintentos");
        return false;
    }

    /**
     * Obtiene estadísticas del cliente API
     */
    void printStats() {
        DEBUG_PRINTLN("========================================");
        DEBUG_PRINTLN("[API] Estadísticas");
        DEBUG_PRINTLN("========================================");
        DEBUG_PRINTF("Total de requests: %lu\n", totalRequests);
        DEBUG_PRINTF("Exitosos: %lu\n", successfulRequests);
        DEBUG_PRINTF("Fallidos: %lu\n", failedRequests);

        if (totalRequests > 0) {
            float successRate = (float)successfulRequests / totalRequests * 100.0;
            DEBUG_PRINTF("Tasa de éxito: %.1f%%\n", successRate);
        }

        DEBUG_PRINTF("Último HTTP Code: %d\n", lastHttpCode);

        if (lastRequestTime > 0) {
            unsigned long secondsAgo = (millis() - lastRequestTime) / 1000;
            DEBUG_PRINTF("Último request: hace %lu segundos\n", secondsAgo);
        }

        DEBUG_PRINTLN("========================================");
    }

    /**
     * Resetea las estadísticas
     */
    void resetStats() {
        totalRequests = 0;
        successfulRequests = 0;
        failedRequests = 0;
        lastRequestTime = 0;
        lastHttpCode = 0;
    }

    /**
     * Envía un heartbeat al backend
     *
     * Permite reportar que el ESP32 está vivo aunque no tenga sensores
     * conectados. Actualiza last_seen_at y opcionalmente envía metadata.
     *
     * Usar este método cuando:
     * - El ESP32 está sin sensores conectados
     * - Se quiere reportar metadata del sistema sin enviar readings
     * - El device está en mantenimiento
     *
     * @param deviceEUI ID único del dispositivo
     * @param firmwareVersion Versión del firmware (opcional)
     * @param metadata Objeto JSON con metadata del sistema (opcional)
     * @return true si se envió exitosamente
     */
    bool sendHeartbeat(String deviceEUI, String firmwareVersion = "", JsonObject metadata = JsonObject()) {
        if (!WiFi.isConnected()) {
            DEBUG_ERROR("[API] WiFi no conectado");
            return false;
        }

        totalRequests++;
        lastRequestTime = millis();

        // Construir URL completa
        String url = apiBaseUrl + "/devices/heartbeat";

        DEBUG_PRINTLN("========================================");
        DEBUG_PRINTLN("[API] Enviando heartbeat al backend");
        DEBUG_PRINTF("[API] URL: %s\n", url.c_str());

        // Crear documento JSON
        StaticJsonDocument<512> doc;

        // Datos obligatorios
        doc["device_eui"] = deviceEUI;

        // Firmware version (opcional)
        if (firmwareVersion.length() > 0) {
            doc["firmware_version"] = firmwareVersion;
        }

        // Metadata (opcional)
        if (!metadata.isNull()) {
            doc["metadata"] = metadata;
        } else {
            // Si no se proporciona metadata, enviar metadata básica del sistema
            JsonObject autoMetadata = doc.createNestedObject("metadata");
            autoMetadata["rssi_dbm"] = WiFi.RSSI();
            autoMetadata["free_heap_bytes"] = ESP.getFreeHeap();
            autoMetadata["uptime_sec"] = millis() / 1000;
            autoMetadata["wifi_ssid"] = WiFi.SSID();
            autoMetadata["ip_address"] = WiFi.localIP().toString();
        }

        // Serializar a string
        String jsonBody;
        serializeJson(doc, jsonBody);

        DEBUG_PRINTLN("[API] Heartbeat JSON:");
        DEBUG_PRINTLN(jsonBody);

        // Configurar HTTP client
        http.begin(url);
        http.setTimeout(HTTP_TIMEOUT_MS);

        // Headers de autenticación: el backend valida el heartbeat con el
        // mismo contrato que /readings (X-API-Key + X-Device-EUI)
        http.addHeader("Content-Type", "application/json");
        http.addHeader("X-API-Key", apiKey);
        http.addHeader("X-Device-EUI", deviceEUI);
        http.addHeader("User-Agent", "ESP32-IoT-Sensor/1.0");

        // Enviar POST request
        int httpCode = http.POST(jsonBody);
        lastHttpCode = httpCode;

        DEBUG_PRINTF("[API] HTTP Response Code: %d\n", httpCode);

        // Verificar respuesta
        bool success = false;

        if (httpCode > 0) {
            String response = http.getString();

            if (httpCode == 200) {
                // Success
                DEBUG_PRINTLN("[API] ✓ Heartbeat enviado exitosamente");

                // Parsear respuesta
                StaticJsonDocument<256> responseDoc;
                DeserializationError error = deserializeJson(responseDoc, response);

                if (!error) {
                    DEBUG_PRINTLN("[API] Respuesta del servidor:");
                    if (responseDoc.containsKey("device_id")) {
                        DEBUG_PRINTF("[API]   - Device ID: %d\n", responseDoc["device_id"].as<int>());
                    }
                    if (responseDoc.containsKey("is_online")) {
                        DEBUG_PRINTF("[API]   - Is Online: %s\n",
                                    responseDoc["is_online"].as<bool>() ? "true" : "false");
                    }
                    if (responseDoc.containsKey("message")) {
                        DEBUG_PRINTF("[API]   - Message: %s\n",
                                    responseDoc["message"].as<const char*>());
                    }
                }

                successfulRequests++;
                success = true;

            } else if (httpCode == 401) {
                DEBUG_ERROR("[API] Error 401: No autorizado (verificar API Key y Device EUI)");
                DEBUG_ERROR("[API] El device debe existir en el backend con esa API key");
            } else if (httpCode == 404) {
                DEBUG_ERROR("[API] Error 404: Device no encontrado");
                DEBUG_ERROR("[API] Debe crear el device en el backend primero");
            } else if (httpCode == 400) {
                DEBUG_ERROR("[API] Error 400: Bad Request");
                DEBUG_PRINTLN(response);
            } else if (httpCode == 500) {
                DEBUG_ERROR("[API] Error 500: Error interno del servidor");
                DEBUG_PRINTLN(response);
            } else {
                DEBUG_ERROR("[API] Error HTTP desconocido");
                DEBUG_PRINTLN(response);
            }

            if (!success) {
                failedRequests++;
            }

        } else {
            // Error de conexión HTTP
            DEBUG_ERROR("[API] Error de conexión HTTP");
            DEBUG_PRINTF("[API] Error: %s\n", http.errorToString(httpCode).c_str());
            failedRequests++;
        }

        // Cerrar conexión
        http.end();

        DEBUG_PRINTLN("========================================");

        return success;
    }

    /**
     * Envía un heartbeat con retry automático
     *
     * @param deviceEUI ID único del dispositivo
     * @param firmwareVersion Versión del firmware (opcional)
     * @param metadata Metadata del sistema (opcional)
     * @param maxRetries Número máximo de reintentos
     * @return true si se envió exitosamente
     */
    bool sendHeartbeatWithRetry(String deviceEUI, String firmwareVersion = "",
                               JsonObject metadata = JsonObject(), int maxRetries = HTTP_MAX_RETRIES) {
        int attempts = 0;

        while (attempts < maxRetries) {
            if (sendHeartbeat(deviceEUI, firmwareVersion, metadata)) {
                return true;
            }

            attempts++;
            if (attempts < maxRetries) {
                DEBUG_PRINTF("[API] Reintentando heartbeat... (%d/%d)\n", attempts, maxRetries);
                delay(2000 * attempts);  // Backoff exponencial
            }
        }

        DEBUG_ERROR("[API] ✗ Heartbeat falló después de todos los reintentos");
        return false;
    }

    /**
     * Obtiene el último código HTTP
     */
    int getLastHttpCode() {
        return lastHttpCode;
    }

    /**
     * Obtiene la tasa de éxito
     */
    float getSuccessRate() {
        if (totalRequests == 0) {
            return 0.0;
        }
        return (float)successfulRequests / totalRequests * 100.0;
    }

    /**
     * Test de conexión al API
     *
     * @return true si el API responde
     */
    bool testConnection() {
        if (!WiFi.isConnected()) {
            DEBUG_ERROR("[API] WiFi no conectado");
            return false;
        }

        String url = apiBaseUrl + "/health";  // Endpoint de health check

        DEBUG_PRINTLN("[API] Testeando conexión al backend...");
        DEBUG_PRINTF("[API] URL: %s\n", url.c_str());

        http.begin(url);
        http.setTimeout(5000);

        int httpCode = http.GET();

        DEBUG_PRINTF("[API] Response Code: %d\n", httpCode);

        bool isOk = (httpCode == 200);

        if (isOk) {
            DEBUG_PRINTLN("[API] ✓ Backend accesible");
        } else {
            DEBUG_ERROR("[API] ✗ Backend no accesible");
        }

        http.end();

        return isOk;
    }
};

#endif // API_CLIENT_H
