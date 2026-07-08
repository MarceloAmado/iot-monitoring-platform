/**
 * Sensor de distancia ultrasónico JSN-SR04T (resistente al agua)
 * Rango: 25cm a 600cm
 * Resolución: 0.5cm
 * Resistente al agua con cable de 2.5m
 */

#ifndef JSN_SR04T_SENSOR_H
#define JSN_SR04T_SENSOR_H

#include "Sensor.h"
#include "../config.h"

/**
 * Clase para sensor de distancia ultrasónico JSN-SR04T
 *
 * Características:
 * - Rango de medición: 25cm - 600cm
 * - Precisión: 0.5cm
 * - Voltaje de operación: 5V
 * - Corriente: 30mA
 * - Ángulo de detección: 70°
 * - Resistente al agua (IP67)
 * - Cable de 2.5m
 *
 * Protocolo:
 * 1. Enviar pulso TRIGGER de 10µs
 * 2. Esperar respuesta ECHO
 * 3. Medir duración del pulso ECHO
 * 4. Calcular distancia: distance_cm = (duration_us * 0.0343) / 2
 *    (velocidad del sonido: 343 m/s = 0.0343 cm/µs)
 */
class JSN_SR04TSensor : public Sensor {
private:
    uint8_t triggerPin;
    uint8_t echoPin;
    bool initialized;

    // Configuración según datasheet
    const float ERROR_DISTANCE = SENSOR_ERROR_VALUE;
    const float MIN_DISTANCE_CM = 25.0;      // Distancia mínima detectable
    const float MAX_DISTANCE_CM = 600.0;     // Distancia máxima detectable
    const unsigned long TIMEOUT_US = 38000;  // Timeout para ECHO (equivale a ~650cm)
    const unsigned long TRIGGER_PULSE_US = 10;
    const unsigned long MIN_CYCLE_PERIOD_MS = 50;  // Mínimo tiempo entre lecturas
    const int MAX_RETRIES = 3;               // Reintentos en caso de falla

    // Velocidad del sonido (cm/µs)
    const float SOUND_SPEED = 0.0343;

    // Variables de estado
    unsigned long lastReadTime;
    float lastValidDistance;
    int consecutiveErrors;

public:
    /**
     * Constructor
     *
     * @param triggerPin Pin GPIO para TRIGGER
     * @param echoPin Pin GPIO para ECHO
     */
    JSN_SR04TSensor(uint8_t triggerPin, uint8_t echoPin)
        : triggerPin(triggerPin),
          echoPin(echoPin),
          initialized(false),
          lastReadTime(0),
          lastValidDistance(0.0),
          consecutiveErrors(0) {
        this->pin = triggerPin;  // Para compatibilidad con clase base
        this->name = "JSN-SR04T";
    }

    /**
     * Inicializa el sensor
     */
    void begin() override {
        DEBUG_PRINTF("[JSN-SR04T] Inicializando sensor en pines TRIGGER=%d, ECHO=%d\n",
                     triggerPin, echoPin);

        // Configurar pines
        pinMode(triggerPin, OUTPUT);
        pinMode(echoPin, INPUT);

        // Estado inicial
        digitalWrite(triggerPin, LOW);
        delayMicroseconds(2);

        // Hacer una lectura de prueba
        float testDistance = measureDistance();

        if (testDistance != ERROR_DISTANCE ||
            (testDistance >= MIN_DISTANCE_CM && testDistance <= MAX_DISTANCE_CM)) {
            initialized = true;
            DEBUG_PRINTF("[JSN-SR04T] Sensor inicializado correctamente. Distancia de prueba: %.1f cm\n",
                        testDistance);
        } else {
            initialized = false;
            DEBUG_WARN("[JSN-SR04T] Sensor inicializado pero sin lectura válida (puede estar fuera de rango)");
            // Aún así marcar como inicializado - podría estar apuntando fuera de rango
            initialized = true;
        }
    }

    /**
     * Retorna el tipo de sensor
     */
    String getType() override {
        return "JSN-SR04T";
    }

    /**
     * Lee la distancia del sensor
     *
     * @param doc JsonDocument donde se agregarán los datos
     * @return JsonObject con los datos: {"distance_cm": 123.5}
     */
    JsonObject read(JsonDocument& doc) override {
        JsonObject data = doc.createNestedObject();

        if (!initialized) {
            DEBUG_ERROR("[JSN-SR04T] Sensor no inicializado");
            data["distance_cm"] = ERROR_DISTANCE;
            return data;
        }

        // Verificar tiempo mínimo entre lecturas
        unsigned long now = millis();
        if (now - lastReadTime < MIN_CYCLE_PERIOD_MS) {
            // Demasiado pronto, retornar última lectura válida
            data["distance_cm"] = lastValidDistance;
            DEBUG_PRINTF("[JSN-SR04T] Retornando última lectura (cooldown): %.1f cm\n",
                        lastValidDistance);
            return data;
        }

        // Intentar lectura con reintentos
        float distance = ERROR_DISTANCE;
        for (int retry = 0; retry < MAX_RETRIES; retry++) {
            distance = measureDistance();

            if (distance != ERROR_DISTANCE &&
                distance >= MIN_DISTANCE_CM &&
                distance <= MAX_DISTANCE_CM) {
                // Lectura válida
                consecutiveErrors = 0;
                lastValidDistance = distance;
                break;
            }

            if (retry < MAX_RETRIES - 1) {
                delay(MIN_CYCLE_PERIOD_MS);  // Esperar antes de reintentar
            }
        }

        lastReadTime = now;

        if (distance == ERROR_DISTANCE ||
            distance < MIN_DISTANCE_CM ||
            distance > MAX_DISTANCE_CM) {
            consecutiveErrors++;
            DEBUG_WARN("[JSN-SR04T] Lectura inválida o fuera de rango: %.1f cm (errores consecutivos: %d)\n",
                      distance, consecutiveErrors);
            data["distance_cm"] = ERROR_DISTANCE;
        } else {
            data["distance_cm"] = distance;
            DEBUG_PRINTF("[JSN-SR04T] Distancia: %.1f cm\n", distance);
        }

        return data;
    }

    /**
     * Verifica si el sensor está funcionando correctamente
     *
     * @return true si no hay demasiados errores consecutivos
     */
    bool isHealthy() override {
        if (!initialized) {
            return false;
        }

        // Considerar no saludable si hay 5+ errores consecutivos
        return consecutiveErrors < 5;
    }

    /**
     * Obtiene la última distancia válida medida
     *
     * @return float distancia en centímetros
     */
    float getLastValidDistance() {
        return lastValidDistance;
    }

    /**
     * Resetea el contador de errores consecutivos
     */
    void resetErrorCount() {
        consecutiveErrors = 0;
    }

    /**
     * Obtiene el número de errores consecutivos
     *
     * @return int cantidad de errores
     */
    int getConsecutiveErrors() {
        return consecutiveErrors;
    }

private:
    /**
     * Realiza una medición de distancia
     *
     * @return float distancia en centímetros, o ERROR_DISTANCE si falla
     */
    float measureDistance() {
        // 1. Enviar pulso TRIGGER de 10µs
        digitalWrite(triggerPin, LOW);
        delayMicroseconds(2);
        digitalWrite(triggerPin, HIGH);
        delayMicroseconds(TRIGGER_PULSE_US);
        digitalWrite(triggerPin, LOW);

        // 2. Medir duración del pulso ECHO
        unsigned long duration = pulseIn(echoPin, HIGH, TIMEOUT_US);

        // 3. Verificar timeout
        if (duration == 0) {
            DEBUG_WARN("[JSN-SR04T] Timeout esperando ECHO (objeto muy lejos o sensor desconectado)");
            return ERROR_DISTANCE;
        }

        // 4. Calcular distancia
        // distancia = (tiempo * velocidad del sonido) / 2
        // El /2 es porque el sonido viaja ida y vuelta
        float distance = (duration * SOUND_SPEED) / 2.0;

        return distance;
    }
};

#endif // JSN_SR04T_SENSOR_H
