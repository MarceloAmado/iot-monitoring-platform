/**
 * MPX5700Sensor.h - Sensor de presión MPX5700AP (0-700 kPa)
 *
 * Sensor analógico de presión absoluta de la serie MPX de Freescale/NXP.
 *
 * Características:
 * - Rango: 15 kPa a 700 kPa (0.15 bar a 7 bar)
 * - Salida: 0.2V a 4.7V (lineal)
 * - Precisión: ±2.5% del rango completo
 * - Temperatura operativa: -40°C a 125°C
 *
 * Fórmula de conversión:
 * P(kPa) = (Vout - 0.2) * 700 / (4.7 - 0.2)
 * P(kPa) = (Vout - 0.2) * 155.56
 *
 * Conexión:
 * - Pin 1: Vout → ADC del ESP32 (GPIO34/ADC1_6)
 * - Pin 2: GND  → GND
 * - Pin 3: Vcc  → 5V (o 3.3V con factor de corrección)
 *
 * @author Sistema IoT
 * @version 1.0.0
 * @date 2025-10-20
 */

#ifndef MPX5700_SENSOR_H
#define MPX5700_SENSOR_H

#include "Sensor.h"
#include <Arduino.h>

class MPX5700Sensor : public Sensor {
private:
    uint8_t pin;
    float calibrationOffset;   // Offset de calibración en kPa
    float calibrationFactor;   // Factor de corrección multiplicativo

    // Constantes del sensor
    const float V_MIN = 0.2;   // Voltaje mínimo (V)
    const float V_MAX = 4.7;   // Voltaje máximo (V)
    const float P_MIN = 15.0;  // Presión mínima (kPa)
    const float P_MAX = 700.0; // Presión máxima (kPa)

    // Constantes de ADC del ESP32
    const int ADC_RESOLUTION = 4095;  // 12 bits
    const float ADC_VREF = 3.3;       // Voltaje de referencia del ADC

    // Muestras para promedio
    const int NUM_SAMPLES = 10;

    /**
     * Lee voltaje del ADC con promedio de múltiples muestras
     */
    float readVoltage() {
        float sum = 0;

        for (int i = 0; i < NUM_SAMPLES; i++) {
            int raw = analogRead(pin);
            sum += raw;
            delay(5);  // Pequeño delay entre muestras
        }

        float avgRaw = sum / NUM_SAMPLES;

        // Convertir a voltaje
        // Si el sensor está alimentado a 5V, necesitamos un divisor de voltaje
        // para proteger el ADC del ESP32 (máx 3.3V)
        float voltage = (avgRaw / ADC_RESOLUTION) * ADC_VREF;

        return voltage;
    }

    /**
     * Convierte voltaje a presión en kPa
     */
    float voltageToPressureKPa(float voltage) {
        // Fórmula: P = (V - V_MIN) * (P_MAX - P_MIN) / (V_MAX - V_MIN) + P_MIN
        float pressure = ((voltage - V_MIN) * (P_MAX - P_MIN) / (V_MAX - V_MIN)) + P_MIN;

        // Aplicar calibración
        pressure = (pressure + calibrationOffset) * calibrationFactor;

        // Limitar al rango válido
        if (pressure < P_MIN) pressure = P_MIN;
        if (pressure > P_MAX) pressure = P_MAX;

        return pressure;
    }

    /**
     * Convierte kPa a bar
     */
    float kPaToBar(float kPa) {
        return kPa / 100.0;
    }

    /**
     * Convierte kPa a PSI
     */
    float kPaToPsi(float kPa) {
        return kPa * 0.145038;
    }

public:
    /**
     * Constructor
     *
     * @param pin Pin ADC del ESP32 (ej: GPIO34)
     * @param offset Offset de calibración en kPa (default 0)
     * @param factor Factor de corrección multiplicativo (default 1.0)
     */
    MPX5700Sensor(uint8_t pin, float offset = 0.0, float factor = 1.0)
        : pin(pin), calibrationOffset(offset), calibrationFactor(factor) {}

    /**
     * Inicializa el sensor
     */
    void begin() override {
        // Configurar pin como entrada analógica
        pinMode(pin, INPUT);

        // Configurar resolución del ADC (12 bits)
        analogReadResolution(12);

        // Configurar atenuación del ADC para rango completo (0-3.3V)
        // Si se usa divisor de voltaje 5V→3.3V
        analogSetAttenuation(ADC_11db);  // Atenuación 11dB → rango 0-3.3V

        Serial.printf("✓ MPX5700 Sensor inicializado en pin %d\n", pin);
    }

    /**
     * Retorna el tipo de sensor
     */
    String getType() override {
        return "MPX5700";
    }

    /**
     * Lee datos del sensor
     *
     * Retorna JSON con:
     * - voltage_v: Voltaje leído (V)
     * - pressure_kpa: Presión en kiloPascales
     * - pressure_bar: Presión en bar
     * - pressure_psi: Presión en PSI
     */
    JsonObject read(JsonDocument& doc) override {
        JsonObject data = doc.createNestedObject();

        // Leer voltaje
        float voltage = readVoltage();

        // Verificar rango válido
        if (voltage < 0.1 || voltage > ADC_VREF) {
            // Error: voltaje fuera de rango
            data["voltage_v"] = voltage;
            data["pressure_kpa"] = -999.0;
            data["pressure_bar"] = -999.0;
            data["pressure_psi"] = -999.0;
            return data;
        }

        // Convertir a presión
        float pressureKPa = voltageToPressureKPa(voltage);
        float pressureBar = kPaToBar(pressureKPa);
        float pressurePsi = kPaToPsi(pressureKPa);

        // Retornar datos
        data["voltage_v"] = voltage;
        data["pressure_kpa"] = pressureKPa;
        data["pressure_bar"] = pressureBar;
        data["pressure_psi"] = pressurePsi;

        return data;
    }

    /**
     * Verifica si el sensor está funcionando correctamente
     */
    bool isHealthy() override {
        float voltage = readVoltage();

        // Verificar que el voltaje esté en un rango razonable
        // (al menos 0.1V para asegurar que hay señal)
        return (voltage >= 0.1 && voltage <= ADC_VREF);
    }

    /**
     * Calibra el sensor con una presión conocida
     *
     * @param knownPressureKPa Presión de referencia conocida en kPa
     */
    void calibrate(float knownPressureKPa) {
        Serial.println("\n--- Calibración MPX5700 ---");
        Serial.printf("Presión de referencia: %.2f kPa\n", knownPressureKPa);

        // Leer presión actual (sin calibración)
        calibrationOffset = 0;
        calibrationFactor = 1.0;

        float voltage = readVoltage();
        float measuredPressure = voltageToPressureKPa(voltage);

        Serial.printf("Presión medida (sin calibrar): %.2f kPa\n", measuredPressure);

        // Calcular offset
        calibrationOffset = knownPressureKPa - measuredPressure;

        Serial.printf("Offset de calibración: %.2f kPa\n", calibrationOffset);
        Serial.println("Calibración completada ✓");
    }

    /**
     * Establece el offset de calibración manualmente
     */
    void setCalibrationOffset(float offset) {
        calibrationOffset = offset;
    }

    /**
     * Establece el factor de calibración manualmente
     */
    void setCalibrationFactor(float factor) {
        calibrationFactor = factor;
    }

    /**
     * Obtiene el offset de calibración actual
     */
    float getCalibrationOffset() const {
        return calibrationOffset;
    }

    /**
     * Obtiene el factor de calibración actual
     */
    float getCalibrationFactor() const {
        return calibrationFactor;
    }
};

#endif // MPX5700_SENSOR_H
