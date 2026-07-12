#!/usr/bin/env python3
"""
Script para simular un ESP32 enviando datos al backend.

El backend autentica devices con DOS headers obligatorios:
X-API-Key + X-Device-EUI. El device debe existir en la DB con esa
api_key (columna api_key o api_key_encrypted).

Uso:
    python simulate_esp32.py                    # Envía 1 lectura
    python simulate_esp32.py --count 10         # Envía 10 lecturas
    python simulate_esp32.py --interval 5       # Envía lecturas cada 5 segundos (infinito)

    # API key/EUI configurables por variable de entorno:
    DEVICE_API_KEY=mi_key DEVICE_EUI=ESP32_LAB_001 python simulate_esp32.py
"""

import os
import requests
import random
import time
import argparse
from datetime import datetime

# Configuración
API_URL = os.getenv("API_URL", "http://localhost:8000/api/v1/readings")
DEVICE_EUI = os.getenv("DEVICE_EUI", "ESP32_LAB_001")
DEVICE_API_KEY = os.getenv("DEVICE_API_KEY", "esp32_lab_001_key")

def generate_reading():
    """Genera una lectura simulada con variación realista"""
    return {
        "device_eui": DEVICE_EUI,
        "data_payload": {
            "temp_c": round(random.uniform(20.0, 28.0), 2),
            "humidity_pct": round(random.uniform(55.0, 70.0), 2),
            "battery_mv": random.randint(3600, 3900),
            "rssi_dbm": random.randint(-75, -55)
        },
        "timestamp": datetime.utcnow().isoformat() + "Z"
    }

def send_reading(reading):
    """Envía una lectura al backend"""
    headers = {
        "X-API-Key": DEVICE_API_KEY,
        "X-Device-EUI": DEVICE_EUI,
    }
    try:
        response = requests.post(API_URL, json=reading, headers=headers, timeout=10)
        if response.status_code == 201:
            data = response.json()
            print(f"✓ Lectura enviada - ID: {data['id']} | Temp: {reading['data_payload']['temp_c']}°C | Humedad: {reading['data_payload']['humidity_pct']}%")
            return True
        else:
            print(f"✗ Error {response.status_code}: {response.text}")
            return False
    except requests.exceptions.ConnectionError:
        print("✗ Error: No se pudo conectar al backend. ¿Está corriendo en http://localhost:8000?")
        return False
    except Exception as e:
        print(f"✗ Error inesperado: {e}")
        return False

def main():
    parser = argparse.ArgumentParser(description="Simulador de ESP32 para testing")
    parser.add_argument("--count", type=int, help="Número de lecturas a enviar (default: 1)")
    parser.add_argument("--interval", type=int, help="Intervalo en segundos entre lecturas (modo continuo)")
    args = parser.parse_args()

    print("=" * 60)
    print("🌡️  Simulador de ESP32")
    print("=" * 60)
    print(f"Device EUI: {DEVICE_EUI}")
    print(f"API URL: {API_URL}")
    print("=" * 60)

    if args.interval:
        # Modo continuo
        print(f"Modo continuo: enviando lecturas cada {args.interval} segundos")
        print("Presiona Ctrl+C para detener\n")
        count = 0
        try:
            while True:
                count += 1
                print(f"[{count}] ", end="")
                reading = generate_reading()
                send_reading(reading)
                time.sleep(args.interval)
        except KeyboardInterrupt:
            print(f"\n\n✓ Detenido. Total de lecturas enviadas: {count}")
    else:
        # Modo batch
        count = args.count or 1
        print(f"Enviando {count} lectura(s)...\n")
        success = 0
        for i in range(count):
            reading = generate_reading()
            if send_reading(reading):
                success += 1
            if i < count - 1:
                time.sleep(1)  # 1 segundo entre lecturas

        print(f"\n✓ Completado: {success}/{count} lecturas enviadas exitosamente")

if __name__ == "__main__":
    main()
