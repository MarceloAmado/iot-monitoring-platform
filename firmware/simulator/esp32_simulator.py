#!/usr/bin/env python3
"""
Simulador de ESP32 para testing
Simula el envío de datos de sensores al backend sin hardware físico

Uso:
    python esp32_simulator.py
    python esp32_simulator.py --device ESP32_LAB_002 --interval 10
"""

import argparse
import time
import random
import requests
from datetime import datetime
import json

class ESP32Simulator:
    def __init__(self, device_eui: str, api_url: str, api_key: str, interval: int = 60):
        """
        Inicializa el simulador de ESP32

        Args:
            device_eui: ID único del dispositivo simulado
            api_url: URL base del API (ej: http://localhost:8000/api/v1)
            api_key: API Key para autenticación
            interval: Intervalo de envío en segundos
        """
        self.device_eui = device_eui
        self.api_url = api_url.rstrip('/')
        self.api_key = api_key
        self.interval = interval

        self.total_requests = 0
        self.successful_requests = 0
        self.failed_requests = 0

        print("=" * 60)
        print("ESP32 SIMULATOR")
        print("=" * 60)
        print(f"Device EUI: {self.device_eui}")
        print(f"API URL: {self.api_url}")
        print(f"Interval: {self.interval} seconds")
        print("=" * 60)

    def generate_sensor_data(self) -> dict:
        """
        Genera datos simulados de sensores

        Returns:
            dict: Diccionario con datos de sensores
        """
        # Temperatura DS18B20 (simular variación realista)
        base_temp = 25.0
        temp_variation = random.uniform(-2.0, 2.0)
        temp_c = round(base_temp + temp_variation, 2)

        # Humedad DHT22
        base_humidity = 60.0
        humidity_variation = random.uniform(-5.0, 5.0)
        humidity_pct = round(base_humidity + humidity_variation, 1)

        # RSSI WiFi (simular señal variable)
        rssi_dbm = random.randint(-70, -40)

        # Uptime (incrementar con cada lectura)
        uptime_sec = self.total_requests * self.interval

        # Free heap (simular memoria disponible)
        free_heap_bytes = random.randint(200000, 250000)

        # Voltaje batería (opcional, simular descarga lenta)
        battery_v = round(3.7 - (uptime_sec / 86400) * 0.2, 2)  # Descarga ~0.2V por día

        data = {
            "temp_c": temp_c,
            "humidity_pct": humidity_pct,
            "rssi_dbm": rssi_dbm,
            "uptime_sec": uptime_sec,
            "free_heap_bytes": free_heap_bytes,
            "battery_v": max(3.0, battery_v)  # Mínimo 3.0V
        }

        return data

    def send_reading(self) -> bool:
        """
        Envía una lectura al backend

        Returns:
            bool: True si se envió exitosamente, False en caso contrario
        """
        self.total_requests += 1

        # Generar datos de sensores
        data_payload = self.generate_sensor_data()

        # Construir payload
        payload = {
            "device_eui": self.device_eui,
            "data_payload": data_payload,
            # timestamp se genera en backend si no se proporciona
        }

        # Headers: el backend exige X-API-Key Y X-Device-EUI (sin el EUI → 422)
        headers = {
            "Content-Type": "application/json",
            "X-API-Key": self.api_key,
            "X-Device-EUI": self.device_eui,
        }

        # URL completa
        url = f"{self.api_url}/readings"

        print(f"\n[{datetime.now().strftime('%H:%M:%S')}] Enviando reading #{self.total_requests}")
        print(f"Temperatura: {data_payload['temp_c']}°C")
        print(f"Humedad: {data_payload['humidity_pct']}%")
        print(f"RSSI: {data_payload['rssi_dbm']} dBm")

        try:
            # Enviar POST request
            response = requests.post(url, json=payload, headers=headers, timeout=10)

            if response.status_code in [200, 201]:
                # Éxito
                self.successful_requests += 1

                response_data = response.json()
                print(f"[OK] Enviado exitosamente")
                print(f"  - Reading ID: {response_data.get('id', 'N/A')}")
                print(f"  - Quality Score: {response_data.get('quality_score', 'N/A')}")

                return True

            else:
                # Error HTTP
                self.failed_requests += 1

                print(f"[ERROR] HTTP {response.status_code}")
                print(f"  Response: {response.text[:200]}")

                return False

        except requests.exceptions.ConnectionError:
            self.failed_requests += 1
            print("[ERROR] No se pudo conectar al backend")
            print("  Verificar que el backend este corriendo y la URL sea correcta")
            return False

        except requests.exceptions.Timeout:
            self.failed_requests += 1
            print("[ERROR] Timeout al enviar request")
            return False

        except Exception as e:
            self.failed_requests += 1
            print(f"[ERROR] Error inesperado: {str(e)}")
            return False

    def print_stats(self):
        """Imprime estadísticas del simulador"""
        print("\n" + "=" * 60)
        print("ESTADÍSTICAS")
        print("=" * 60)
        print(f"Total de requests: {self.total_requests}")
        print(f"Exitosos: {self.successful_requests}")
        print(f"Fallidos: {self.failed_requests}")

        if self.total_requests > 0:
            success_rate = (self.successful_requests / self.total_requests) * 100
            print(f"Tasa de éxito: {success_rate:.1f}%")

        print("=" * 60)

    def run(self, max_iterations: int = None):
        """
        Ejecuta el simulador

        Args:
            max_iterations: Número máximo de iteraciones (None = infinito)
        """
        iteration = 0

        try:
            while True:
                # Enviar lectura
                self.send_reading()

                iteration += 1

                # Verificar si se alcanzó el máximo
                if max_iterations and iteration >= max_iterations:
                    print(f"\n[OK] Alcanzado maximo de {max_iterations} iteraciones")
                    break

                # Esperar antes de la próxima lectura
                if max_iterations is None or iteration < max_iterations:
                    print(f"\nPróxima lectura en {self.interval} segundos...")
                    time.sleep(self.interval)

        except KeyboardInterrupt:
            print("\n\n[AVISO] Simulador detenido por el usuario (Ctrl+C)")

        finally:
            # Mostrar estadísticas al finalizar
            self.print_stats()


def main():
    """Función principal"""
    parser = argparse.ArgumentParser(description="Simulador de ESP32 para Sistema de Monitoreo IoT")

    parser.add_argument(
        "--device",
        default="ESP32_SIMULATOR_001",
        help="Device EUI (default: ESP32_SIMULATOR_001)"
    )

    parser.add_argument(
        "--url",
        default="http://localhost:8000/api/v1",
        help="URL del API backend (default: http://localhost:8000/api/v1)"
    )

    parser.add_argument(
        "--key",
        default="esp32_device_key_change_me",
        help="API Key para autenticación"
    )

    parser.add_argument(
        "--interval",
        type=int,
        default=60,
        help="Intervalo de envío en segundos (default: 60)"
    )

    parser.add_argument(
        "--iterations",
        type=int,
        default=None,
        help="Número máximo de iteraciones (default: infinito)"
    )

    args = parser.parse_args()

    # Crear simulador
    simulator = ESP32Simulator(
        device_eui=args.device,
        api_url=args.url,
        api_key=args.key,
        interval=args.interval
    )

    # Ejecutar
    simulator.run(max_iterations=args.iterations)


if __name__ == "__main__":
    main()
