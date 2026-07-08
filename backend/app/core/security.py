"""
Sistema de Monitoreo IoT
Módulo de Seguridad y Autenticación

Maneja:
- Hashing de contraseñas con bcrypt
- Generación y verificación de tokens JWT
- Validación de API Keys para devices ESP32
- Encriptación simétrica de datos sensibles con Fernet
"""

import logging
from datetime import datetime, timedelta
from typing import Optional
import hashlib

from jose import JWTError, jwt
from passlib.context import CryptContext
from cryptography.fernet import Fernet, InvalidToken

from app.core.config import settings

logger = logging.getLogger(__name__)


# ============================================================
# Configuración de Bcrypt para Hashing de Contraseñas
# ============================================================

# Context de Passlib configurado para bcrypt
# deprecated="auto" permite migrar de algoritmos viejos si es necesario
pwd_context = CryptContext(
    schemes=["bcrypt"],
    deprecated="auto",
    bcrypt__rounds=12,  # Cost factor (12 es un buen balance seguridad/performance)
)


# ============================================================
# Funciones de Hashing de Contraseñas
# ============================================================

def hash_password(password: str) -> str:
    """
    Genera un hash bcrypt de una contraseña en texto plano.

    Args:
        password (str): Contraseña en texto plano

    Returns:
        str: Hash bcrypt de la contraseña

    Example:
        ```python
        hashed = hash_password("mi_password_segura")
        # "$2b$12$..."
        ```

    Notas:
        - NUNCA almacenar contraseñas en texto plano
        - El hash bcrypt incluye el salt automáticamente
        - Cada hash es único incluso para la misma contraseña
    """
    return pwd_context.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    Verifica si una contraseña en texto plano coincide con un hash.

    Args:
        plain_password (str): Contraseña ingresada por el usuario
        hashed_password (str): Hash almacenado en la base de datos

    Returns:
        bool: True si la contraseña es correcta, False en caso contrario

    Example:
        ```python
        if verify_password(input_password, user.password_hash):
            print("Contraseña correcta")
        ```
    """
    return pwd_context.verify(plain_password, hashed_password)


# ============================================================
# Funciones JWT (JSON Web Tokens)
# ============================================================

def create_access_token(
    data: dict,
    expires_delta: Optional[timedelta] = None
) -> str:
    """
    Crea un token JWT para autenticación de usuarios.

    Args:
        data (dict): Payload del token (ej: {"sub": user.email, "role": "admin"})
        expires_delta (Optional[timedelta]): Tiempo de expiración custom

    Returns:
        str: Token JWT firmado

    Example:
        ```python
        token = create_access_token(
            data={"sub": "admin@example.com", "role": "super_admin"}
        )
        # "<header>.<payload>.<signature>" (JWT firmado en base64url)
        ```

    Notas:
        - El token incluye automáticamente el campo "exp" (expiration)
        - Si no se especifica expires_delta, usa el valor por defecto de config
    """
    to_encode = data.copy()

    # Calcular tiempo de expiración
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(
            minutes=settings.access_token_expire_minutes
        )

    # Agregar campos estándar JWT
    to_encode.update({
        "exp": expire,  # Expiration time
        "iat": datetime.utcnow(),  # Issued at
    })

    # Firmar el token
    encoded_jwt = jwt.encode(
        to_encode,
        settings.jwt_secret_key,
        algorithm=settings.jwt_algorithm
    )

    return encoded_jwt


def decode_access_token(token: str) -> Optional[dict]:
    """
    Decodifica y valida un token JWT.

    Args:
        token (str): Token JWT a decodificar

    Returns:
        Optional[dict]: Payload del token si es válido, None si es inválido/expirado

    Example:
        ```python
        payload = decode_access_token(token)
        if payload:
            user_email = payload.get("sub")
        else:
            print("Token inválido o expirado")
        ```

    Notas:
        - Valida automáticamente la firma y la expiración
        - Retorna None si el token está expirado o tiene firma inválida
    """
    try:
        payload = jwt.decode(
            token,
            settings.jwt_secret_key,
            algorithms=[settings.jwt_algorithm]
        )
        return payload
    except JWTError as e:
        # Token inválido, expirado o firma incorrecta
        logger.debug(f"Error decodificando JWT: {e}")
        return None


# ============================================================
# API Keys para Devices ESP32
# ============================================================

def generate_device_api_key(device_eui: str) -> str:
    """
    Genera una API Key única para un device ESP32.

    La API Key se deriva del device_eui + un salt secreto del servidor.
    Esto permite validar keys sin almacenarlas en la DB.

    Args:
        device_eui (str): Identificador único del device (ej: "ESP32_LAB_001")

    Returns:
        str: API Key en formato hexadecimal

    Example:
        ```python
        api_key = generate_device_api_key("ESP32_LAB_001")
        # "a3f5b8c2d9e1f4a7..."
        ```

    Notas:
        - La API Key es determinística (mismo device_eui = misma key)
        - El salt secreto debe estar en las variables de entorno
        - Si se cambia el salt, todas las keys quedan inválidas
    """
    # Concatenar device_eui con el salt secreto
    data = f"{device_eui}{settings.device_api_key_salt}".encode("utf-8")

    # Generar hash SHA256
    hash_object = hashlib.sha256(data)
    api_key = hash_object.hexdigest()

    return api_key


# NOTA: la validación de API keys de devices vive en app/api/deps.py
# (dependencia validate_device_api_key, vía Fernet). La variante HMAC que
# existía acá era código muerto y fue eliminada en la Fase 4 (2026-07-07).


# ============================================================
# Utilidades de Validación
# ============================================================

def is_strong_password(password: str) -> tuple[bool, str]:
    """
    Valida que una contraseña cumpla con los requisitos de seguridad.

    Requisitos:
    - Mínimo 8 caracteres
    - Al menos una letra mayúscula
    - Al menos una letra minúscula
    - Al menos un número
    - Al menos un carácter especial

    Args:
        password (str): Contraseña a validar

    Returns:
        tuple[bool, str]: (es_válida, mensaje_error)

    Example:
        ```python
        is_valid, error_msg = is_strong_password("Password123!")
        if not is_valid:
            return {"error": error_msg}
        ```
    """
    if len(password) < 8:
        return False, "La contraseña debe tener al menos 8 caracteres"

    if not any(c.isupper() for c in password):
        return False, "La contraseña debe tener al menos una mayúscula"

    if not any(c.islower() for c in password):
        return False, "La contraseña debe tener al menos una minúscula"

    if not any(c.isdigit() for c in password):
        return False, "La contraseña debe tener al menos un número"

    special_chars = "!@#$%^&*()_+-=[]{}|;:,.<>?"
    if not any(c in special_chars for c in password):
        return False, "La contraseña debe tener al menos un carácter especial"

    return True, ""


# ============================================================
# Funciones de Encriptación Simétrica con Fernet
# ============================================================

def get_fernet_cipher() -> Fernet:
    """
    Obtiene una instancia de Fernet configurada con la ENCRYPTION_KEY.

    Returns:
        Fernet: Instancia de cipher Fernet

    Raises:
        ValueError: Si ENCRYPTION_KEY no está configurada o es inválida

    Example:
        ```python
        cipher = get_fernet_cipher()
        encrypted = cipher.encrypt(b"datos sensibles")
        ```

    Notas:
        - ENCRYPTION_KEY debe ser una clave Fernet válida de 32 bytes base64-encoded
        - Generar con: Fernet.generate_key().decode()
    """
    if not settings.encryption_key:
        raise ValueError("ENCRYPTION_KEY no configurada en settings")

    try:
        return Fernet(settings.encryption_key.encode())
    except Exception as e:
        raise ValueError(f"ENCRYPTION_KEY inválida: {e}")


def encrypt_api_key(api_key: str) -> str:
    """
    Encripta una API Key usando Fernet (encriptación simétrica).

    Args:
        api_key (str): API Key en texto plano

    Returns:
        str: API Key encriptada (base64)

    Example:
        ```python
        encrypted = encrypt_api_key("abc123...")
        # Resultado: "gAAAAABh..."
        ```

    Notas:
        - Usa Fernet (AES-128 en modo CBC con HMAC SHA256)
        - El resultado incluye timestamp y puede ser desencriptado
        - Safe para almacenar en base de datos
    """
    cipher = get_fernet_cipher()
    encrypted_bytes = cipher.encrypt(api_key.encode())
    return encrypted_bytes.decode()


def decrypt_api_key(encrypted_api_key: str) -> Optional[str]:
    """
    Desencripta una API Key previamente encriptada con Fernet.

    Args:
        encrypted_api_key (str): API Key encriptada (base64)

    Returns:
        Optional[str]: API Key en texto plano, o None si falló la desencriptación

    Example:
        ```python
        decrypted = decrypt_api_key("gAAAAABh...")
        if decrypted:
            # Usar API Key
            validate_key(decrypted)
        else:
            # Error de desencriptación
            raise HTTPException(401, "API Key corrupta")
        ```

    Notas:
        - Retorna None si la key está corrupta o fue encriptada con otra ENCRYPTION_KEY
        - Retorna None si el token Fernet expiró (si se configuró TTL)
    """
    cipher = get_fernet_cipher()

    try:
        decrypted_bytes = cipher.decrypt(encrypted_api_key.encode())
        return decrypted_bytes.decode()
    except InvalidToken:
        # Token inválido, corrupto o expirado
        return None
    except Exception:
        # Cualquier otro error de desencriptación
        return None


def encrypt_sensitive_data(data: str) -> str:
    """
    Encripta datos sensibles genéricos usando Fernet.

    Args:
        data (str): Datos a encriptar

    Returns:
        str: Datos encriptados (base64)

    Example:
        ```python
        encrypted_token = encrypt_sensitive_data("refresh_token_abc123")
        # Guardar en DB
        user.encrypted_refresh_token = encrypted_token
        ```

    Notas:
        - Alias genérico de encrypt_api_key()
        - Útil para encriptar cualquier dato sensible (tokens, passwords temporales, etc.)
    """
    return encrypt_api_key(data)


def decrypt_sensitive_data(encrypted_data: str) -> Optional[str]:
    """
    Desencripta datos sensibles previamente encriptados.

    Args:
        encrypted_data (str): Datos encriptados (base64)

    Returns:
        Optional[str]: Datos en texto plano, o None si falló

    Example:
        ```python
        refresh_token = decrypt_sensitive_data(user.encrypted_refresh_token)
        if refresh_token:
            # Usar token
            validate_refresh_token(refresh_token)
        ```

    Notas:
        - Alias genérico de decrypt_api_key()
    """
    return decrypt_api_key(encrypted_data)
