"""
Script para migrar API Keys de plaintext a encriptado.

Este script:
1. Busca devices con api_key en plaintext pero sin api_key_encrypted
2. Encripta cada API key usando Fernet
3. Guarda el resultado en api_key_encrypted
4. Mantiene api_key temporalmente para backward compatibility

Uso:
    docker exec iot_backend python scripts/migrate_api_keys.py

Autor: Sistema SCADA - Fase 1.2
Fecha: 2025-11-08
"""

import sys
import os

# Agregar el directorio raíz al path para imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app.core.database import SessionLocal
from app.models.device import Device
from app.core.security import encrypt_api_key


def migrate_api_keys():
    """
    Migra API Keys de plaintext a encriptado.

    Busca devices que tienen api_key pero no api_key_encrypted,
    y encripta las keys usando Fernet.
    """
    db = SessionLocal()

    try:
        # Buscar devices con api_key pero sin api_key_encrypted
        devices = db.query(Device).filter(
            Device.api_key.isnot(None),
            Device.api_key != "",  # Excluir strings vacíos
            Device.api_key_encrypted.is_(None)
        ).all()

        total_devices = len(devices)

        if total_devices == 0:
            print("✅ No hay API keys para migrar")
            print("   Todos los devices ya tienen api_key_encrypted o no tienen api_key")
            return

        print(f"📊 Encontrados {total_devices} devices con API keys sin encriptar")
        print("-" * 60)

        migrated_count = 0
        failed_count = 0

        for device in devices:
            try:
                print(f"🔒 Encriptando API key de device '{device.device_eui}'...", end=" ")

                # Encriptar la API key
                encrypted_key = encrypt_api_key(device.api_key)

                # Guardar en la columna encrypted
                device.api_key_encrypted = encrypted_key

                print("✅ OK")
                migrated_count += 1

            except Exception as e:
                print(f"❌ ERROR")
                print(f"   Detalle: {e}")
                failed_count += 1

        # Commit de todos los cambios
        if migrated_count > 0:
            db.commit()
            print("-" * 60)
            print(f"✅ Migración completada exitosamente")
            print(f"   - API keys migradas: {migrated_count}")
            print(f"   - Errores: {failed_count}")
            print(f"   - Total procesados: {total_devices}")

            if failed_count == 0:
                print("\n💡 Próximos pasos:")
                print("   1. Verificar que todas las API keys fueron encriptadas")
                print("   2. Actualizar endpoints para usar api_key_encrypted")
                print("   3. En 1-2 semanas, deprecar columna api_key (opcional)")
        else:
            print("⚠️  No se realizaron cambios")

    except Exception as e:
        db.rollback()
        print(f"\n❌ Error crítico durante la migración:")
        print(f"   {e}")
        print("\n🔄 Rollback realizado - No se aplicaron cambios")
        sys.exit(1)

    finally:
        db.close()


def verify_migration():
    """
    Verifica el estado de la migración.

    Muestra estadísticas de devices con/sin API keys encriptadas.
    """
    db = SessionLocal()

    try:
        # Contar devices por estado de encriptación
        total_devices = db.query(Device).count()

        encrypted_only = db.query(Device).filter(
            Device.api_key_encrypted.isnot(None),
            Device.api_key.is_(None)
        ).count()

        plaintext_only = db.query(Device).filter(
            Device.api_key.isnot(None),
            Device.api_key != "",
            Device.api_key_encrypted.is_(None)
        ).count()

        both = db.query(Device).filter(
            Device.api_key.isnot(None),
            Device.api_key != "",
            Device.api_key_encrypted.isnot(None)
        ).count()

        no_key = db.query(Device).filter(
            (Device.api_key.is_(None)) | (Device.api_key == ""),
            Device.api_key_encrypted.is_(None)
        ).count()

        print("\n📊 Estado de API Keys en Devices")
        print("=" * 60)
        print(f"Total de devices:              {total_devices}")
        print(f"  - Solo encrypted:            {encrypted_only}")
        print(f"  - Solo plaintext:            {plaintext_only}")
        print(f"  - Ambas (en migración):      {both}")
        print(f"  - Sin API key:               {no_key}")
        print("=" * 60)

        if plaintext_only > 0:
            print(f"\n⚠️  Hay {plaintext_only} devices con API keys sin encriptar")
            print("   Ejecuta: python scripts/migrate_api_keys.py")
        elif both > 0:
            print(f"\n✅ Migración completada, pero hay {both} devices con ambas columnas")
            print("   Esto es normal durante el período de transición")
        else:
            print("\n✅ Migración completada - Todas las API keys están encriptadas")

    finally:
        db.close()


if __name__ == "__main__":
    print("🔐 Script de Migración de API Keys - SCADA Fase 1.2")
    print("=" * 60)

    # Verificar estado actual
    verify_migration()

    # Ejecutar migración
    print("\n")
    migrate_api_keys()

    # Verificar resultado
    verify_migration()
