/**
 * AnalogSensor.h - Sensor analógico genérico para ESP32
 *
 * Lee un pin ADC y reporta el valor raw (0-4095) y el voltaje (0-3.3V).
 * Ideal para potenciómetros, LDR, sensores de humedad de suelo, etc.
 *
 * Uso:
 *   sensors.push_back(new AnalogSensor(34, "potenciometro"));
 */

#ifndef ANALOG_SENSOR_H
#define ANALOG_SENSOR_H

#include "Sensor.h"
#include "../config.h"

class AnalogSensor : public Sensor {
private:
    String label;
    int lastRawValue;
    bool initialized;

public:
    /**
     * Constructor
     * @param analogPin Pin ADC (GPIO 32-39 en ESP32)
     * @param sensorLabel Etiqueta para el JSON (ej: "potenciometro", "ldr")
     */
    AnalogSensor(uint8_t analogPin, const String& sensorLabel = "analog")
        : label(sensorLabel), lastRawValue(0), initialized(false) {
        pin = analogPin;
        name = "Analog_" + sensorLabel;
    }

    String getType() override {
        return "AnalogSensor_" + label;
    }

    void begin() override {
        // Configurar resolución ADC (12 bits = 0-4095)
        analogReadResolution(12);

        // Hacer una lectura de prueba
        lastRawValue = analogRead(pin);
        initialized = true;

        DEBUG_PRINTF("[ANALOG] Sensor '%s' inicializado en GPIO%d\n",
                    label.c_str(), pin);
        DEBUG_PRINTF("[ANALOG] Lectura inicial: %d (%.2fV)\n",
                    lastRawValue, rawToVoltage(lastRawValue));
    }

    JsonObject read(JsonDocument& doc) override {
        JsonObject data = doc.to<JsonObject>();

        lastRawValue = analogRead(pin);
        float voltage = rawToVoltage(lastRawValue);
        float percent = rawToPercent(lastRawValue);

        // Reportar valor raw, voltaje y porcentaje
        String rawKey = label + "_raw";
        String voltKey = label + "_v";
        String pctKey = label + "_pct";

        data[rawKey] = lastRawValue;
        data[voltKey] = round(voltage * 100.0) / 100.0;  // 2 decimales
        data[pctKey] = round(percent * 10.0) / 10.0;     // 1 decimal

        return data;
    }

    bool isHealthy() override {
        return initialized;
    }

    /**
     * Obtiene el último valor raw leído
     */
    int getLastRawValue() const {
        return lastRawValue;
    }

private:
    /**
     * Convierte valor ADC raw a voltaje
     */
    float rawToVoltage(int raw) {
        return (raw / 4095.0) * 3.3;
    }

    /**
     * Convierte valor ADC raw a porcentaje (0-100%)
     */
    float rawToPercent(int raw) {
        return (raw / 4095.0) * 100.0;
    }
};

#endif // ANALOG_SENSOR_H
