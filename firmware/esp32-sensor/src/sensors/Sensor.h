/**
 * Clase abstracta base para sensores
 * Permite implementar diferentes tipos de sensores con interfaz común
 */

#ifndef SENSOR_H
#define SENSOR_H

#include <Arduino.h>
#include <ArduinoJson.h>

/**
 * Clase base abstracta para todos los sensores
 *
 * Implementar las siguientes funciones en las subclases:
 * - getType(): Retorna el tipo de sensor como String
 * - read(doc): Lee el sensor y agrega datos al JsonDocument
 * - isHealthy(): Verifica si el sensor está funcionando correctamente
 * - begin(): Inicializa el sensor (opcional, override si es necesario)
 */
class Sensor {
public:
    /**
     * Destructor virtual para permitir polimorfismo
     */
    virtual ~Sensor() {}

    /**
     * Retorna el tipo de sensor
     * Ejemplo: "DS18B20", "DHT22", "MPX5700"
     *
     * @return String con el tipo de sensor
     */
    virtual String getType() = 0;

    /**
     * Lee el sensor y agrega los datos al JsonDocument
     * Los datos se agregan como pares key-value
     * Ejemplo: data["temp_c"] = 25.5;
     *
     * @param doc JsonDocument donde se agregarán los datos
     * @return JsonObject con los datos del sensor
     */
    virtual JsonObject read(JsonDocument& doc) = 0;

    /**
     * Verifica si el sensor está saludable (respondiendo correctamente)
     *
     * @return true si el sensor está funcionando, false si hay problemas
     */
    virtual bool isHealthy() = 0;

    /**
     * Inicializa el sensor
     * Override en subclases si se requiere inicialización específica
     */
    virtual void begin() {}

    /**
     * Calcula un quality score básico (0.0 - 1.0)
     * Puede ser override en subclases para lógica más compleja
     *
     * @param value Valor leído del sensor
     * @param errorValue Valor que indica error
     * @return float score de calidad (0.0 = error, 1.0 = perfecto)
     */
    virtual float calculateQuality(float value, float errorValue = -999.0) {
        if (value == errorValue || isnan(value) || isinf(value)) {
            return 0.0;  // Error total
        }

        if (!isHealthy()) {
            return 0.3;  // Sensor reporta problemas
        }

        return 1.0;  // Todo OK
    }

protected:
    /**
     * Nombre del sensor (opcional, para debugging)
     */
    String name;

    /**
     * Pin del sensor
     */
    uint8_t pin;
};

#endif // SENSOR_H
