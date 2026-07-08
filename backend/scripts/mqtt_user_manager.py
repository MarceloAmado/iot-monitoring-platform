#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
MQTT User Manager - Gestión de usuarios Mosquitto
==================================================

Script para administrar usuarios MQTT sin necesidad de editar manualmente passwords.txt.

Uso:
    python mqtt_user_manager.py add <username> <password> [--role device|monitor|backend]
    python mqtt_user_manager.py remove <username>
    python mqtt_user_manager.py list
    python mqtt_user_manager.py change-password <username> <new_password>
    python mqtt_user_manager.py reload

Ejemplos:
    # Agregar device
    python mqtt_user_manager.py add ESP32_LAB_001 device_pass_123 --role device

    # Listar usuarios
    python mqtt_user_manager.py list

    # Cambiar password
    python mqtt_user_manager.py change-password ESP32_LAB_001 new_pass_456

    # Eliminar usuario
    python mqtt_user_manager.py remove ESP32_LAB_001

    # Reload Mosquitto
    python mqtt_user_manager.py reload
"""

import argparse
import subprocess
import sys
from datetime import datetime
from pathlib import Path
from typing import Optional

# Configuración
MOSQUITTO_CONTAINER = "iot_mosquitto"
PASSWORDS_FILE = "/mosquitto/config/passwords.txt"
ACL_FILE = "/mosquitto/config/acl.txt"

# Roles y permisos
ROLES = {
    "backend": {
        "description": "Backend principal (lectura/escritura total)",
        "acl_pattern": "topic readwrite iot/#"
    },
    "device": {
        "description": "Dispositivo ESP32 (solo telemetría/status)",
        "acl_pattern": "pattern write iot/+/devices/%u/telemetry\npattern write iot/+/devices/%u/status"
    },
    "monitor": {
        "description": "Monitor read-only (solo lectura)",
        "acl_pattern": "topic read iot/#"
    }
}


class MQTTUserManager:
    """Gestor de usuarios MQTT"""

    def __init__(self):
        self.container_name = MOSQUITTO_CONTAINER

    def check_container_running(self) -> bool:
        """Verifica que el contenedor Mosquitto esté corriendo"""
        try:
            result = subprocess.run(
                ["docker", "ps", "--filter", f"name={self.container_name}", "--format", "{{.Names}}"],
                capture_output=True,
                text=True,
                check=True
            )
            return self.container_name in result.stdout
        except subprocess.CalledProcessError:
            return False

    def docker_exec(self, command: str) -> tuple[bool, str]:
        """
        Ejecuta comando en el contenedor Mosquitto

        Args:
            command: Comando a ejecutar

        Returns:
            Tuple (success, output)
        """
        try:
            result = subprocess.run(
                ["docker", "exec", self.container_name, "sh", "-c", command],
                capture_output=True,
                text=True,
                check=True
            )
            return True, result.stdout
        except subprocess.CalledProcessError as e:
            return False, e.stderr

    def backup_passwords_file(self) -> bool:
        """Crea backup de passwords.txt antes de modificar"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_file = f"{PASSWORDS_FILE}.backup_{timestamp}"

        success, output = self.docker_exec(f"cp {PASSWORDS_FILE} {backup_file}")

        if success:
            print(f"[OK] Backup creado: {backup_file}")
        else:
            print(f"[ERROR] Error al crear backup: {output}")

        return success

    def generate_password_hash(self, username: str, password: str) -> Optional[str]:
        """
        Genera hash de password usando mosquitto_passwd

        Args:
            username: Nombre de usuario
            password: Contraseña en texto plano

        Returns:
            Hash generado o None si falla
        """
        # Usar mosquitto_passwd en el contenedor (flag -c crea archivo si no existe)
        command = f"mosquitto_passwd -b -c /tmp/pw.txt {username} '{password}' && cat /tmp/pw.txt && rm -f /tmp/pw.txt"
        success, output = self.docker_exec(command)

        if success:
            # Parsear output (formato: username:hash)
            lines = output.strip().split("\n")
            for line in lines:
                if line.startswith(f"{username}:"):
                    return line.split(":", 1)[1]
        else:
            print(f"[ERROR] Error al generar hash: {output}")

        return None

    def list_users(self) -> list[tuple[str, str]]:
        """
        Lista usuarios existentes en passwords.txt

        Returns:
            Lista de tuplas (username, hash)
        """
        success, output = self.docker_exec(f"cat {PASSWORDS_FILE}")

        if not success:
            print(f"[ERROR] Error al leer passwords.txt: {output}")
            return []

        users = []
        for line in output.strip().split("\n"):
            if line and ":" in line:
                username, hash_val = line.split(":", 1)
                users.append((username, hash_val))

        return users

    def user_exists(self, username: str) -> bool:
        """Verifica si un usuario existe"""
        users = self.list_users()
        return any(user[0] == username for user in users)

    def add_user(self, username: str, password: str, role: str = "device") -> bool:
        """
        Agrega un nuevo usuario MQTT

        Args:
            username: Nombre de usuario
            password: Contraseña
            role: Rol del usuario (device, monitor, backend)

        Returns:
            True si se agregó exitosamente
        """
        if role not in ROLES:
            print(f"[ERROR] Rol inválido: {role}. Roles disponibles: {', '.join(ROLES.keys())}")
            return False

        # Verificar si ya existe
        if self.user_exists(username):
            print(f"[ERROR] El usuario '{username}' ya existe")
            return False

        # Backup antes de modificar
        if not self.backup_passwords_file():
            return False

        # Generar hash
        print(f"Generando hash para '{username}'...")
        hash_val = self.generate_password_hash(username, password)

        if not hash_val:
            print("[ERROR] Error al generar hash de password")
            return False

        # Agregar al archivo
        command = f"echo '{username}:{hash_val}' >> {PASSWORDS_FILE}"
        success, output = self.docker_exec(command)

        if not success:
            print(f"[ERROR] Error al agregar usuario: {output}")
            return False

        print(f"[OK] Usuario '{username}' agregado exitosamente")
        print(f"  Rol: {role} - {ROLES[role]['description']}")

        # Nota sobre ACL (no auto-modificamos ACL por seguridad)
        if role != "backend":
            print(f"\n[WARN] RECORDATORIO: Actualiza manualmente el ACL si es necesario:")
            print(f"   Archivo: backend/mosquitto/config/acl.txt")
            print(f"   Usuario: user {username}")
            print(f"   Permisos: {ROLES[role]['acl_pattern']}")

        return True

    def remove_user(self, username: str) -> bool:
        """
        Elimina un usuario MQTT

        Args:
            username: Nombre de usuario a eliminar

        Returns:
            True si se eliminó exitosamente
        """
        # Verificar si existe
        if not self.user_exists(username):
            print(f"[ERROR] El usuario '{username}' no existe")
            return False

        # Backup antes de modificar
        if not self.backup_passwords_file():
            return False

        # Eliminar del archivo (usando archivo temporal en /tmp)
        temp_file = "/tmp/passwords_tmp.txt"
        command = f"grep -v '^{username}:' {PASSWORDS_FILE} > {temp_file} && cat {temp_file} > {PASSWORDS_FILE} && rm {temp_file}"
        success, output = self.docker_exec(command)

        if not success:
            print(f"[ERROR] Error al eliminar usuario: {output}")
            return False

        print(f"[OK] Usuario '{username}' eliminado exitosamente")
        print(f"\n[WARN] RECORDATORIO: Actualiza manualmente el ACL si es necesario")

        return True

    def change_password(self, username: str, new_password: str) -> bool:
        """
        Cambia la contraseña de un usuario existente

        Args:
            username: Nombre de usuario
            new_password: Nueva contraseña

        Returns:
            True si se cambió exitosamente
        """
        # Verificar si existe
        if not self.user_exists(username):
            print(f"[ERROR] El usuario '{username}' no existe")
            return False

        # Backup antes de modificar
        if not self.backup_passwords_file():
            return False

        # Generar nuevo hash
        print(f"Generando nuevo hash para '{username}'...")
        new_hash = self.generate_password_hash(username, new_password)

        if not new_hash:
            print("[ERROR] Error al generar hash de password")
            return False

        # Reemplazar línea (filtrar antiguo usuario + agregar nuevo)
        temp_file = "/tmp/passwords_tmp.txt"
        command = f"grep -v '^{username}:' {PASSWORDS_FILE} > {temp_file} && echo '{username}:{new_hash}' >> {temp_file} && cat {temp_file} > {PASSWORDS_FILE} && rm {temp_file}"
        success, output = self.docker_exec(command)

        if not success:
            print(f"[ERROR] Error al cambiar password: {output}")
            return False

        print(f"[OK] Password de '{username}' actualizado exitosamente")

        return True

    def reload_mosquitto(self) -> bool:
        """
        Reload de Mosquitto sin downtime (SIGHUP)

        Returns:
            True si reload exitoso
        """
        print("Reloading Mosquitto broker...")
        success, output = self.docker_exec("killall -HUP mosquitto")

        if success:
            print("[OK] Mosquitto recargado exitosamente (sin downtime)")
            print("  Los cambios en passwords.txt ya están activos")
            return True
        else:
            print(f"[ERROR] Error al reload: {output}")
            return False

    def print_users(self):
        """Imprime lista de usuarios"""
        users = self.list_users()

        if not users:
            print("No hay usuarios configurados")
            return

        print(f"\n{'Username':<30} {'Hash (primeros 20 caracteres)'}")
        print("=" * 70)

        for username, hash_val in users:
            hash_preview = hash_val[:20] + "..."
            print(f"{username:<30} {hash_preview}")

        print(f"\nTotal: {len(users)} usuarios")


def main():
    """Entry point del script"""
    parser = argparse.ArgumentParser(
        description="Gestión de usuarios MQTT para Mosquitto",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Ejemplos:
  %(prog)s add ESP32_LAB_001 device_pass_123 --role device
  %(prog)s list
  %(prog)s change-password ESP32_LAB_001 new_pass_456
  %(prog)s remove ESP32_LAB_001
  %(prog)s reload
        """
    )

    subparsers = parser.add_subparsers(dest="command", help="Comandos disponibles")

    # Comando: add
    add_parser = subparsers.add_parser("add", help="Agregar nuevo usuario")
    add_parser.add_argument("username", help="Nombre de usuario")
    add_parser.add_argument("password", help="Contraseña")
    add_parser.add_argument("--role", choices=["device", "monitor", "backend"], default="device",
                            help="Rol del usuario (default: device)")

    # Comando: remove
    remove_parser = subparsers.add_parser("remove", help="Eliminar usuario")
    remove_parser.add_argument("username", help="Nombre de usuario")

    # Comando: list
    subparsers.add_parser("list", help="Listar usuarios")

    # Comando: change-password
    change_parser = subparsers.add_parser("change-password", help="Cambiar contraseña")
    change_parser.add_argument("username", help="Nombre de usuario")
    change_parser.add_argument("new_password", help="Nueva contraseña")

    # Comando: reload
    subparsers.add_parser("reload", help="Reload Mosquitto sin downtime")

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        sys.exit(1)

    # Crear manager
    manager = MQTTUserManager()

    # Verificar que Docker esté corriendo
    if not manager.check_container_running():
        print(f"[ERROR] El contenedor '{MOSQUITTO_CONTAINER}' no está corriendo")
        print("  Ejecuta: docker-compose up -d")
        sys.exit(1)

    # Ejecutar comando
    try:
        if args.command == "add":
            success = manager.add_user(args.username, args.password, args.role)
            if success:
                print("\n[INFO] No olvides ejecutar: python mqtt_user_manager.py reload")
            sys.exit(0 if success else 1)

        elif args.command == "remove":
            success = manager.remove_user(args.username)
            if success:
                print("\n[INFO] No olvides ejecutar: python mqtt_user_manager.py reload")
            sys.exit(0 if success else 1)

        elif args.command == "list":
            manager.print_users()
            sys.exit(0)

        elif args.command == "change-password":
            success = manager.change_password(args.username, args.new_password)
            if success:
                print("\n[INFO] No olvides ejecutar: python mqtt_user_manager.py reload")
            sys.exit(0 if success else 1)

        elif args.command == "reload":
            success = manager.reload_mosquitto()
            sys.exit(0 if success else 1)

    except KeyboardInterrupt:
        print("\n\n[ERROR] Operación cancelada por el usuario")
        sys.exit(1)
    except Exception as e:
        print(f"\n[ERROR] Error inesperado: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
