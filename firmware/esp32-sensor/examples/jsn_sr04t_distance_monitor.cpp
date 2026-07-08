/**
 * Ejemplo: Monitor de Distancia con JSN-SR04T
 *
 * Aplicación: Monitoreo de nivel de líquidos en tanques
 *
 * Descripción:
 * Este ejemplo muestra cómo usar el sensor JSN-SR04T para medir
 * el nivel de agua en un tanque instalando el sensor en la parte
 * superior mirando hacia abajo.
 *
 * Hardware requerido:
 * - ESP32 Dev Board
 * - JSN-SR04T Ultrasonic Distance Sensor (waterproof)
 * - Fuente de alimentación 5V
 *
 * Conexiones:
 * - JSN-SR04T VCC  → 5V
 * - JSN-SR04T GND  → GND
 * - JSN-SR04T TRIG → GPIO 12
 * - JSN-SR04T ECHO → GPIO 14 (5V tolerante)
 *
 * Escenario de uso:
 * - Tanque de agua de 2 metros de altura
 * - Sensor instalado en la tapa superior
 * - Distancia mínima: 25 cm (tanque lleno)
 * - Distancia máxima: 200 cm (tanque vacío)
 * - Alertas cuando el nivel baja de 20% (160 cm de distancia)
 *
 * Autor: Sistema de Monitoreo IoT
 * Fecha: 2025-10-23
 */

#include <Arduino.h>
#include "../src/sensors/JSN_SR04TSensor.h"
#include "../src/config.h"

// ========================================
// CONFIGURACIÓN
// ========================================

// Pines del sensor
const uint8_t TRIG_PIN = 12;
const uint8_t ECHO_PIN = 14;

// Dimensiones del tanque
const float TANK_HEIGHT_CM = 200.0;      // Altura total del tanque
const float SENSOR_OFFSET_CM = 5.0;      // Distancia del sensor al nivel máximo (tapa)
const float MIN_DISTANCE_CM = 25.0;      // Tanque lleno (sensor al agua)
const float MAX_DISTANCE_CM = 200.0;     // Tanque vacío

// Umbrales de alerta
const float ALERT_LEVEL_LOW_PERCENT = 20.0;      // Alerta nivel bajo: <20%
const float ALERT_LEVEL_CRITICAL_PERCENT = 10.0; // Alerta crítico: <10%

// Tiempo de muestreo
const unsigned long SAMPLING_INTERVAL_MS = 5000;  // Leer cada 5 segundos

// ========================================
// VARIABLES GLOBALES
// ========================================

JSN_SR04TSensor* sensor;
unsigned long lastReadTime = 0;
float currentLevelPercent = 0.0;
float lastValidLevelPercent = 0.0;
bool alertSentLow = false;
bool alertSentCritical = false;

// ========================================
// FUNCIONES AUXILIARES
// ========================================

/**
 * Convierte distancia medida a porcentaje de nivel del tanque
 *
 * @param distance_cm Distancia medida por el sensor
 * @return float Porcentaje de llenado (0-100%)
 */
float distanceToLevelPercent(float distance_cm) {
    // Si la distancia es MIN_DISTANCE_CM, el tanque está lleno (100%)
    // Si la distancia es MAX_DISTANCE_CM, el tanque está vacío (0%)

    if (distance_cm <= MIN_DISTANCE_CM) {
        return 100.0;  // Tanque lleno
    }

    if (distance_cm >= MAX_DISTANCE_CM) {
        return 0.0;    // Tanque vacío
    }

    // Calcular porcentaje lineal
    float usableRange = MAX_DISTANCE_CM - MIN_DISTANCE_CM;
    float currentLevel = MAX_DISTANCE_CM - distance_cm;
    float percent = (currentLevel / usableRange) * 100.0;

    return constrain(percent, 0.0, 100.0);
}

/**
 * Retorna un símbolo visual del nivel del tanque
 */
String getLevelIndicator(float percent) {
    if (percent >= 80.0) return "████████████";  // Lleno
    if (percent >= 60.0) return "█████████░░░";  // Alto
    if (percent >= 40.0) return "██████░░░░░░";  // Medio
    if (percent >= 20.0) return "███░░░░░░░░░";  // Bajo
    return "█░░░░░░░░░░░";                       // Crítico
}

/**
 * Procesa alertas según el nivel del tanque
 */
void processAlerts(float levelPercent) {
    // Alerta nivel crítico (<10%)
    if (levelPercent < ALERT_LEVEL_CRITICAL_PERCENT) {
        if (!alertSentCritical) {
            Serial.println("\n🚨 ¡ALERTA CRÍTICA! Nivel de agua CRÍTICO");
            Serial.printf("   Nivel actual: %.1f%%\n", levelPercent);
            Serial.println("   Acción requerida: Rellenar tanque INMEDIATAMENTE\n");

            // Aquí enviarías notificación al backend
            // sendAlert("CRITICAL", levelPercent);

            alertSentCritical = true;
            alertSentLow = true;  // También marcar low alert
        }
    }
    // Alerta nivel bajo (<20%)
    else if (levelPercent < ALERT_LEVEL_LOW_PERCENT) {
        if (!alertSentLow) {
            Serial.println("\n⚠️  ALERTA: Nivel de agua BAJO");
            Serial.printf("   Nivel actual: %.1f%%\n", levelPercent);
            Serial.println("   Acción requerida: Planificar recarga del tanque\n");

            // sendAlert("LOW", levelPercent);

            alertSentLow = true;
        }
        alertSentCritical = false;  // Reset critical alert
    }
    // Nivel OK - resetear alertas
    else {
        if (alertSentLow || alertSentCritical) {
            Serial.println("\n✅ Nivel de agua normalizado");
            Serial.printf("   Nivel actual: %.1f%%\n\n", levelPercent);
        }
        alertSentLow = false;
        alertSentCritical = false;
    }
}

/**
 * Imprime status completo del tanque
 */
void printTankStatus(float distance_cm, float levelPercent, bool isHealthy) {
    Serial.println("\n========================================");
    Serial.println("  MONITOR DE NIVEL DE TANQUE");
    Serial.println("========================================");

    Serial.printf("Distancia medida:  %.1f cm\n", distance_cm);
    Serial.printf("Nivel de agua:     %.1f%%\n", levelPercent);
    Serial.printf("Indicador visual:  %s\n", getLevelIndicator(levelPercent).c_str());

    // Calcular volumen aproximado (asumiendo tanque cilíndrico)
    float volumePercent = levelPercent;  // Simplificado
    Serial.printf("Volumen estimado:  %.1f%%\n", volumePercent);

    // Estado del sensor
    Serial.printf("Sensor status:     %s\n", isHealthy ? "OK ✓" : "ERROR ✗");

    if (!isHealthy) {
        Serial.printf("Errores consec.:   %d\n", sensor->getConsecutiveErrors());
    }

    Serial.println("========================================\n");
}

// ========================================
// SETUP
// ========================================

void setup() {
    // Inicializar Serial
    Serial.begin(115200);
    delay(1000);

    Serial.println("\n\n");
    Serial.println("========================================");
    Serial.println("  JSN-SR04T Distance Sensor Example");
    Serial.println("  Monitor de Nivel de Tanque");
    Serial.println("========================================");
    Serial.println();

    // Crear instancia del sensor
    sensor = new JSN_SR04TSensor(TRIG_PIN, ECHO_PIN);

    // Inicializar sensor
    Serial.println("[SETUP] Inicializando sensor JSN-SR04T...");
    sensor->begin();

    if (sensor->isHealthy()) {
        Serial.println("[SETUP] ✓ Sensor inicializado correctamente");
    } else {
        Serial.println("[SETUP] ✗ Error al inicializar sensor");
        Serial.println("[SETUP] Verificar conexiones y alimentación");
    }

    // Configuración del tanque
    Serial.println();
    Serial.println("Configuración del tanque:");
    Serial.printf("  - Altura total:       %.1f cm\n", TANK_HEIGHT_CM);
    Serial.printf("  - Rango de medición:  %.1f - %.1f cm\n", MIN_DISTANCE_CM, MAX_DISTANCE_CM);
    Serial.printf("  - Alerta nivel bajo:  < %.0f%%\n", ALERT_LEVEL_LOW_PERCENT);
    Serial.printf("  - Alerta crítica:     < %.0f%%\n", ALERT_LEVEL_CRITICAL_PERCENT);
    Serial.println();

    Serial.println("[SETUP] Setup completado. Iniciando monitoreo...\n");

    // Primera lectura inmediata
    lastReadTime = millis() - SAMPLING_INTERVAL_MS;
}

// ========================================
// LOOP
// ========================================

void loop() {
    unsigned long now = millis();

    // Tomar lectura según intervalo configurado
    if (now - lastReadTime >= SAMPLING_INTERVAL_MS) {
        lastReadTime = now;

        // Leer sensor
        StaticJsonDocument<128> doc;
        JsonObject data = sensor->read(doc);

        float distance = data["distance_cm"];

        // Verificar si es una lectura válida
        if (distance != SENSOR_ERROR_VALUE &&
            distance >= MIN_DISTANCE_CM &&
            distance <= MAX_DISTANCE_CM) {

            // Calcular nivel del tanque
            currentLevelPercent = distanceToLevelPercent(distance);
            lastValidLevelPercent = currentLevelPercent;

            // Mostrar status
            printTankStatus(distance, currentLevelPercent, sensor->isHealthy());

            // Procesar alertas
            processAlerts(currentLevelPercent);

        } else {
            // Lectura inválida
            Serial.println("\n⚠️  Lectura inválida del sensor");

            if (distance == SENSOR_ERROR_VALUE) {
                Serial.println("   Motivo: Error de lectura");
            } else if (distance < MIN_DISTANCE_CM) {
                Serial.println("   Motivo: Objeto muy cerca (<25 cm)");
                Serial.println("   Posible causa: Espuma, olas o tanque rebosando");
            } else if (distance > MAX_DISTANCE_CM) {
                Serial.println("   Motivo: Fuera de rango máximo");
                Serial.println("   Posible causa: Tanque vacío o sensor desalineado");
            }

            Serial.printf("   Usando última lectura válida: %.1f%%\n\n", lastValidLevelPercent);

            // Verificar salud del sensor
            if (!sensor->isHealthy()) {
                Serial.println("🔴 SENSOR NO SALUDABLE");
                Serial.printf("   Errores consecutivos: %d\n", sensor->getConsecutiveErrors());
                Serial.println("   Acción: Verificar conexiones y alimentación\n");

                // Aquí enviarías alerta de fallo del sensor al backend
                // sendSensorFaultAlert();
            }
        }
    }

    // Pequeño delay para no saturar el CPU
    delay(10);
}

// ========================================
// FUNCIONES ADICIONALES (Placeholder)
// ========================================

/**
 * Envía alerta al backend (a implementar)
 */
void sendAlert(String type, float levelPercent) {
    // TODO: Implementar envío de alerta al backend
    // POST /api/v1/alerts
    // {
    //   "device_eui": "ESP32_TANK_001",
    //   "alert_type": "TANK_LEVEL_LOW",
    //   "severity": "WARNING",
    //   "message": "Nivel de tanque bajo: 15.5%",
    //   "data": {
    //     "level_percent": 15.5,
    //     "distance_cm": 160.0
    //   }
    // }
}

/**
 * Envía alerta de fallo de sensor (a implementar)
 */
void sendSensorFaultAlert() {
    // TODO: Implementar envío de alerta de fallo
}
