/**
 * Ejemplo: Monitor de Presión con MPX5700
 *
 * Este ejemplo muestra cómo usar el sensor MPX5700 para monitorear
 * presión en sistemas de aire comprimido, tanques de agua, etc.
 *
 * Hardware necesario:
 * - ESP32 DevKit
 * - Sensor MPX5700AP (0-700 kPa / 0-7 bar)
 * - Resistor 10kΩ y 4.7kΩ para divisor de voltaje (si se alimenta a 5V)
 *
 * Conexiones:
 * - MPX5700 Pin 1 (Vout) → Divisor de voltaje → GPIO34 (ADC1_6)
 * - MPX5700 Pin 2 (GND)  → GND
 * - MPX5700 Pin 3 (Vcc)  → 5V
 *
 * Divisor de voltaje (5V → 3.3V):
 *   5V ─┬─ R1 (10kΩ) ─┬─ A GPIO34
 *       │             └─ R2 (4.7kΩ) ─ GND
 *
 * @author Sistema IoT
 * @date 2025-10-21
 */

#include <Arduino.h>
#include <ArduinoJson.h>
#include "sensors/MPX5700Sensor.h"

// Pin del sensor
#define PRESSURE_SENSOR_PIN 34  // GPIO34 (ADC1_6)

// Crear instancia del sensor
MPX5700Sensor pressureSensor(PRESSURE_SENSOR_PIN);

void setup() {
    Serial.begin(115200);
    delay(1000);

    Serial.println("\n========================================");
    Serial.println("Monitor de Presión MPX5700");
    Serial.println("========================================\n");

    // Inicializar sensor
    pressureSensor.begin();

    // Opcional: Calibrar con una presión conocida
    // Por ejemplo, si sabemos que hay 100 kPa (1 bar) en el sistema:
    // pressureSensor.calibrate(100.0);

    Serial.println("\nSensor listo. Comenzando lecturas cada 5 segundos...\n");
}

void loop() {
    // Crear documento JSON
    StaticJsonDocument<256> doc;

    // Leer datos del sensor
    JsonObject data = pressureSensor.read(doc);

    // Verificar si el sensor está saludable
    if (!pressureSensor.isHealthy()) {
        Serial.println("⚠️ ADVERTENCIA: Sensor no saludable!");
        delay(5000);
        return;
    }

    // Obtener valores
    float voltage = data["voltage_v"];
    float pressureKPa = data["pressure_kpa"];
    float pressureBar = data["pressure_bar"];
    float pressurePsi = data["pressure_psi"];

    // Verificar si hay error
    if (pressureKPa == -999.0) {
        Serial.println("❌ ERROR: Lectura inválida (voltaje fuera de rango)");
        delay(5000);
        return;
    }

    // Mostrar datos
    Serial.println("┌─────────────────────────────────────┐");
    Serial.printf("│ Voltaje:    %8.3f V           │\n", voltage);
    Serial.printf("│ Presión:    %8.2f kPa         │\n", pressureKPa);
    Serial.printf("│             %8.3f bar         │\n", pressureBar);
    Serial.printf("│             %8.2f PSI         │\n", pressurePsi);
    Serial.println("└─────────────────────────────────────┘");

    // Alerta si la presión es baja o alta
    if (pressureBar < 1.0) {
        Serial.println("⚠️  ALERTA: Presión baja!");
    } else if (pressureBar > 6.0) {
        Serial.println("⚠️  ALERTA: Presión alta!");
    } else {
        Serial.println("✅ Presión normal");
    }

    Serial.println();

    // Esperar 5 segundos
    delay(5000);
}

/**
 * NOTAS DE CALIBRACIÓN:
 *
 * Si las lecturas no son precisas, puedes calibrar el sensor de dos formas:
 *
 * 1. Calibración con presión conocida:
 *    - Conecta el sensor a un sistema con presión conocida (ej: 2 bar)
 *    - Usa: pressureSensor.calibrate(200.0);  // 2 bar = 200 kPa
 *
 * 2. Calibración manual:
 *    - Si sabes el offset: pressureSensor.setCalibrationOffset(5.0);
 *    - Si sabes el factor: pressureSensor.setCalibrationFactor(0.98);
 *
 * CONVERSIONES ÚTILES:
 * - 1 bar = 100 kPa = 14.5038 PSI
 * - 1 PSI = 6.89476 kPa
 * - Presión atmosférica al nivel del mar ≈ 101.325 kPa (1.01325 bar)
 */
