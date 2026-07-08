/**
 * Sensor de temperatura DS18B20 (OneWire)
 * Rango: -55°C a +125°C
 * Precisión: ±0.5°C
 */

#ifndef DS18B20_SENSOR_H
#define DS18B20_SENSOR_H

#include "Sensor.h"
#include <OneWire.h>
#include <DallasTemperature.h>
#include "../config.h"

/**
 * Clase para sensor de temperatura DS18B20
 * Usa protocolo OneWire para comunicación
 */
class DS18B20Sensor : public Sensor {
private:
    OneWire oneWire;
    DallasTemperature sensor;
    bool initialized;

    // Configuración
    const float ERROR_TEMP = SENSOR_ERROR_VALUE;

public:
    /**
     * Constructor
     *
     * @param pin Pin GPIO donde está conectado el sensor
     */
    DS18B20Sensor(uint8_t pin)
        : oneWire(pin),
          sensor(&oneWire),
          initialized(false) {
        this->pin = pin;
        this->name = "DS18B20";
    }

    /**
     * Inicializa el sensor
     */
    void begin() override {
        DEBUG_PRINTF("[DS18B20] Inicializando sensor en pin %d\n", pin);

        sensor.begin();

        // Configurar resolución (9-12 bits)
        // 12 bits = máxima precisión (0.0625°C) pero más lento (750ms)
        // 9 bits = menor precisión (0.5°C) pero más rápido (93.75ms)
        sensor.setResolution(12);

        // Verificar que hay al menos un dispositivo conectado
        int deviceCount = sensor.getDeviceCount();

        if (deviceCount > 0) {
            initialized = true;
            DEBUG_PRINTF("[DS18B20] Sensor inicializado correctamente. Dispositivos encontrados: %d\n", deviceCount);
        } else {
            initialized = false;
            DEBUG_ERROR("[DS18B20] No se encontraron dispositivos OneWire");
        }
    }

    /**
     * Retorna el tipo de sensor
     */
    String getType() override {
        return "DS18B20";
    }

    /**
     * Lee la temperatura del sensor
     *
     * @param doc JsonDocument donde se agregarán los datos
     * @return JsonObject con los datos: {"temp_c": 25.5}
     */
    JsonObject read(JsonDocument& doc) override {
        JsonObject data = doc.createNestedObject();

        if (!initialized) {
            DEBUG_ERROR("[DS18B20] Sensor no inicializado");
            data["temp_c"] = ERROR_TEMP;
            return data;
        }

        // Solicitar lectura de temperatura
        sensor.requestTemperatures();

        // Esperar a que la conversión termine (máx 750ms en 12-bit)
        // El método requestTemperatures() ya espera internamente

        // Leer temperatura del primer dispositivo (índice 0)
        float temp = sensor.getTempCByIndex(0);

        // Verificar si la lectura es válida
        if (temp == DEVICE_DISCONNECTED_C) {
            DEBUG_ERROR("[DS18B20] Sensor desconectado o sin respuesta");
            data["temp_c"] = ERROR_TEMP;
        } else if (temp < -55.0 || temp > 125.0) {
            // Fuera del rango válido del DS18B20
            DEBUG_WARN("[DS18B20] Temperatura fuera de rango válido");
            data["temp_c"] = ERROR_TEMP;
        } else {
            // Lectura válida
            data["temp_c"] = temp;
            DEBUG_PRINTF("[DS18B20] Temperatura: %.2f°C\n", temp);
        }

        return data;
    }

    /**
     * Verifica si el sensor está funcionando correctamente
     *
     * @return true si hay dispositivos conectados
     */
    bool isHealthy() override {
        if (!initialized) {
            return false;
        }

        // Verificar que sigue habiendo dispositivos
        int deviceCount = sensor.getDeviceCount();
        return deviceCount > 0;
    }

    /**
     * Obtiene el número de dispositivos OneWire en el bus
     *
     * @return int cantidad de dispositivos
     */
    int getDeviceCount() {
        return sensor.getDeviceCount();
    }

    /**
     * Lee la dirección del dispositivo (útil para debugging)
     *
     * @param deviceIndex Índice del dispositivo (default: 0)
     * @return String con la dirección en formato hexadecimal
     */
    String getDeviceAddress(int deviceIndex = 0) {
        DeviceAddress address;
        if (sensor.getAddress(address, deviceIndex)) {
            String addressStr = "";
            for (uint8_t i = 0; i < 8; i++) {
                if (address[i] < 16) addressStr += "0";
                addressStr += String(address[i], HEX);
                if (i < 7) addressStr += ":";
            }
            return addressStr;
        }
        return "N/A";
    }

    /**
     * Establece la resolución del sensor (9-12 bits)
     *
     * @param resolution Resolución en bits (9, 10, 11 o 12)
     */
    void setResolution(uint8_t resolution) {
        if (resolution >= 9 && resolution <= 12) {
            sensor.setResolution(resolution);
            DEBUG_PRINTF("[DS18B20] Resolución establecida: %d bits\n", resolution);
        }
    }
};

#endif // DS18B20_SENSOR_H
