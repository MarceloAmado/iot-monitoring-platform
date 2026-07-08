"""
Script para generar y asignar API Key a un device.

Uso:
    python scripts/generate_device_api_key.py <device_eui>

Ejemplo:
    python scripts/generate_device_api_key.py ESP32_LAB_001
"""

import sys
sys.path.insert(0, '/app')

from app.core.database import db_session
from app.core.security import generate_device_api_key
from app.models.device import Device


def main():
    if len(sys.argv) < 2:
        print("❌ Error: Debes proporcionar un device_eui")
        print(f"Uso: python {sys.argv[0]} <device_eui>")
        sys.exit(1)

    device_eui = sys.argv[1]

    with db_session() as db:
        # Buscar device
        device = db.query(Device).filter(Device.device_eui == device_eui).first()

        if not device:
            print(f"❌ Error: Device '{device_eui}' no encontrado")
            sys.exit(1)

        # Generar API Key
        api_key = generate_device_api_key(device_eui)

        # Actualizar device
        device.api_key = api_key
        db.commit()

        print(f"✓ API Key generada y asignada exitosamente")
        print(f"  Device: {device.name}")
        print(f"  Device EUI: {device_eui}")
        print(f"  API Key: {api_key}")


if __name__ == "__main__":
    main()
