/**
 * Sensor de temperatura y humedad DHT22 (AM2302)
 * Temperatura: -40°C a +80°C (±0.5°C)
 * Humedad: 0-100% RH (±2%)
 */

#ifndef DHT22_SENSOR_H
#define DHT22_SENSOR_H

#include "Sensor.h"
#include <DHT.h>
#include "../config.h"

/**
 * Clase para sensor DHT22
 * Lee temperatura y humedad relativa
 */
class DHT22Sensor : public Sensor {
private:
    DHT dht;
    bool initialized;
    const float ERROR_VALUE = SENSOR_ERROR_VALUE;

    // Límites de lectura válidos
    const float MIN_TEMP = -40.0;
    const float MAX_TEMP = 80.0;
    const float MIN_HUMIDITY = 0.0;
    const float MAX_HUMIDITY = 100.0;

public:
    /**
     * Constructor
     *
     * @param pin Pin GPIO donde está conectado el sensor
     */
    DHT22Sensor(uint8_t pin)
        : dht(pin, DHT_TYPE),
          initialized(false) {
        this->pin = pin;
        this->name = "DHT22";
    }

    /**
     * Inicializa el sensor
     */
    void begin() override {
        DEBUG_PRINTF("[DHT22] Inicializando sensor en pin %d\n", pin);

        dht.begin();

        // Esperar un momento para que el sensor se estabilice
        delay(2000);

        // Hacer una lectura de prueba
        float testTemp = dht.readTemperature();
        float testHum = dht.readHumidity();

        if (isnan(testTemp) || isnan(testHum)) {
            initialized = false;
            DEBUG_ERROR("[DHT22] Sensor no responde correctamente");
        } else {
            initialized = true;
            DEBUG_PRINTF("[DHT22] Sensor inicializado. Temp: %.1f°C, Humedad: %.1f%%\n",
                        testTemp, testHum);
        }
    }

    /**
     * Retorna el tipo de sensor
     */
    String getType() override {
        return "DHT22";
    }

    /**
     * Lee temperatura y humedad del sensor
     *
     * @param doc JsonDocument donde se agregarán los datos
     * @return JsonObject con los datos: {"temp_c": 25.5, "humidity_pct": 60.2}
     */
    JsonObject read(JsonDocument& doc) override {
        JsonObject data = doc.createNestedObject();

        if (!initialized) {
            DEBUG_ERROR("[DHT22] Sensor no inicializado");
            data["temp_c"] = ERROR_VALUE;
            data["humidity_pct"] = ERROR_VALUE;
            return data;
        }

        // Leer temperatura
        float temp = dht.readTemperature();

        // Leer humedad
        float humidity = dht.readHumidity();

        // Validar temperatura
        if (isnan(temp)) {
            DEBUG_ERROR("[DHT22] Error al leer temperatura (NaN)");
            data["temp_c"] = ERROR_VALUE;
        } else if (temp < MIN_TEMP || temp > MAX_TEMP) {
            DEBUG_WARN("[DHT22] Temperatura fuera de rango válido");
            data["temp_c"] = ERROR_VALUE;
        } else {
            data["temp_c"] = temp;
            DEBUG_PRINTF("[DHT22] Temperatura: %.2f°C\n", temp);
        }

        // Validar humedad
        if (isnan(humidity)) {
            DEBUG_ERROR("[DHT22] Error al leer humedad (NaN)");
            data["humidity_pct"] = ERROR_VALUE;
        } else if (humidity < MIN_HUMIDITY || humidity > MAX_HUMIDITY) {
            DEBUG_WARN("[DHT22] Humedad fuera de rango válido");
            data["humidity_pct"] = ERROR_VALUE;
        } else {
            data["humidity_pct"] = humidity;
            DEBUG_PRINTF("[DHT22] Humedad: %.2f%%\n", humidity);
        }

        return data;
    }

    /**
     * Verifica si el sensor está funcionando correctamente
     *
     * @return true si el sensor responde
     */
    bool isHealthy() override {
        if (!initialized) {
            return false;
        }

        // Hacer una lectura de prueba
        float temp = dht.readTemperature();
        float humidity = dht.readHumidity();

        // Si ambas lecturas son NaN, el sensor tiene problemas
        return !(isnan(temp) && isnan(humidity));
    }

    /**
     * Lee el índice de calor (sensación térmica)
     * Útil en ambientes cálidos y húmedos
     *
     * @param fahrenheit true para resultado en °F, false para °C (default)
     * @return float índice de calor
     */
    float readHeatIndex(bool fahrenheit = false) {
        float temp = dht.readTemperature(fahrenheit);
        float humidity = dht.readHumidity();

        if (isnan(temp) || isnan(humidity)) {
            return ERROR_VALUE;
        }

        return dht.computeHeatIndex(temp, humidity, fahrenheit);
    }

    /**
     * Lee el punto de rocío (dew point)
     * Temperatura a la que el aire se satura y condensa
     *
     * @return float punto de rocío en °C
     */
    float readDewPoint() {
        float temp = dht.readTemperature();
        float humidity = dht.readHumidity();

        if (isnan(temp) || isnan(humidity)) {
            return ERROR_VALUE;
        }

        // Fórmula de Magnus-Tetens
        float a = 17.271;
        float b = 237.7;
        float alpha = ((a * temp) / (b + temp)) + log(humidity / 100.0);
        float dewPoint = (b * alpha) / (a - alpha);

        return dewPoint;
    }

    /**
     * Calcula un quality score basado en las lecturas
     *
     * @return float score de calidad (0.0 - 1.0)
     */
    float calculateQualityScore() {
        float temp = dht.readTemperature();
        float humidity = dht.readHumidity();

        // Ambas lecturas fallidas = 0.0
        if (isnan(temp) && isnan(humidity)) {
            return 0.0;
        }

        // Una lectura fallida = 0.5
        if (isnan(temp) || isnan(humidity)) {
            return 0.5;
        }

        // Ambas lecturas OK = 1.0
        return 1.0;
    }
};

#endif // DHT22_SENSOR_H
