"""
Servicio de caché con Redis.

Proporciona funciones helper para cachear datos frecuentemente accedidos:
- Dashboard metrics
- Device schemas
- User permissions
- Health status

Estrategia de invalidación:
- TTL (Time To Live) para datos que cambian poco
- Invalidación manual en operaciones CRUD
- Invalidación por patrón (devices:*, readings:*)
"""

import json
import logging
import redis
from typing import Any, Optional, List
from datetime import timedelta
from app.core.config import settings

logger = logging.getLogger(__name__)

# ============================================
# Redis Client Singleton
# ============================================

class RedisCache:
    """
    Cliente Redis singleton con métodos helper.

    Uso:
        from app.services.cache_service import cache

        # Set
        cache.set("key", {"data": "value"}, ttl=300)

        # Get
        data = cache.get("key")

        # Delete
        cache.delete("key")

        # Delete pattern
        cache.delete_pattern("devices:*")
    """

    def __init__(self):
        """Inicializa conexión a Redis."""
        try:
            self.client = redis.Redis(
                host=settings.redis_host,
                port=settings.redis_port,
                db=settings.redis_db,
                decode_responses=True,  # Retorna strings en lugar de bytes
                socket_timeout=5,
                socket_connect_timeout=5
            )
            # Test connection
            self.client.ping()
            logger.info(f"Redis conectado: {settings.redis_host}:{settings.redis_port}")
        except Exception as e:
            logger.warning(f"Redis no disponible: {e}. Sistema funcionará sin caché (performance reducida)")
            self.client = None

    def _is_available(self) -> bool:
        """Verifica si Redis está disponible."""
        return self.client is not None

    def set(self, key: str, value: Any, ttl: Optional[int] = None) -> bool:
        """
        Guarda un valor en caché.

        Args:
            key: Clave del caché
            value: Valor a cachear (será serializado a JSON)
            ttl: Tiempo de vida en segundos (None = sin expiración)

        Returns:
            bool: True si se guardó exitosamente

        Ejemplo:
            cache.set("device:1:schema", schema_data, ttl=3600)
        """
        if not self._is_available():
            return False

        try:
            # Serializar a JSON
            serialized = json.dumps(value)

            if ttl:
                self.client.setex(key, ttl, serialized)
            else:
                self.client.set(key, serialized)

            return True
        except Exception as e:
            logger.warning(f"Error al guardar en caché {key}: {e}")
            return False

    def get(self, key: str) -> Optional[Any]:
        """
        Obtiene un valor del caché.

        Args:
            key: Clave del caché

        Returns:
            Valor deserializado o None si no existe

        Ejemplo:
            schema = cache.get("device:1:schema")
        """
        if not self._is_available():
            return None

        try:
            value = self.client.get(key)
            if value is None:
                return None

            # Deserializar JSON
            return json.loads(value)
        except Exception as e:
            logger.warning(f"Error al leer caché {key}: {e}")
            return None

    def delete(self, key: str) -> bool:
        """
        Elimina una clave del caché.

        Args:
            key: Clave a eliminar

        Returns:
            bool: True si se eliminó
        """
        if not self._is_available():
            return False

        try:
            self.client.delete(key)
            return True
        except Exception as e:
            logger.warning(f"Error al eliminar caché {key}: {e}")
            return False

    def delete_pattern(self, pattern: str) -> int:
        """
        Elimina todas las claves que coincidan con un patrón.

        Args:
            pattern: Patrón con wildcards (devices:*, user:*:permissions)

        Returns:
            int: Número de claves eliminadas

        Ejemplo:
            cache.delete_pattern("device:*")  # Elimina todos los devices
        """
        if not self._is_available():
            return 0

        try:
            keys = self.client.keys(pattern)
            if keys:
                deleted = self.client.delete(*keys)
                return deleted
            return 0
        except Exception as e:
            logger.warning(f"Error al eliminar patrón {pattern}: {e}")
            return 0

    def exists(self, key: str) -> bool:
        """
        Verifica si una clave existe en caché.

        Args:
            key: Clave a verificar

        Returns:
            bool: True si existe
        """
        if not self._is_available():
            return False

        try:
            return self.client.exists(key) > 0
        except Exception as e:
            logger.warning(f"Error al verificar existencia {key}: {e}")
            return False

    def increment(self, key: str, amount: int = 1) -> Optional[int]:
        """
        Incrementa un contador.

        Args:
            key: Clave del contador
            amount: Cantidad a incrementar

        Returns:
            Nuevo valor del contador o None si falla

        Ejemplo:
            cache.increment("readings:device:1:count")
        """
        if not self._is_available():
            return None

        try:
            return self.client.incrby(key, amount)
        except Exception as e:
            logger.warning(f"Error al incrementar {key}: {e}")
            return None

    def expire(self, key: str, ttl: int) -> bool:
        """
        Establece TTL en una clave existente.

        Args:
            key: Clave
            ttl: Tiempo de vida en segundos

        Returns:
            bool: True si se estableció
        """
        if not self._is_available():
            return False

        try:
            return self.client.expire(key, ttl)
        except Exception as e:
            logger.warning(f"Error al establecer TTL {key}: {e}")
            return False


# ============================================
# Cache Keys Helpers
# ============================================

class CacheKeys:
    """
    Generador de claves de caché consistentes.

    Evita typos y centraliza la nomenclatura.
    """

    @staticmethod
    def device_schema(device_id: int) -> str:
        """Key para schema de device."""
        return f"device:{device_id}:schema"

    @staticmethod
    def device_health(device_id: int) -> str:
        """Key para health metrics de device."""
        return f"device:{device_id}:health"

    @staticmethod
    def health_dashboard() -> str:
        """Key para dashboard de salud completo."""
        return "health:dashboard"

    @staticmethod
    def user_permissions(user_id: int) -> str:
        """Key para permisos de usuario."""
        return f"user:{user_id}:permissions"

    @staticmethod
    def readings_stats(device_id: int) -> str:
        """Key para estadísticas de readings."""
        return f"readings:{device_id}:stats"

    @staticmethod
    def alert_rules_active() -> str:
        """Key para reglas de alertas activas."""
        return "alert_rules:active"


# ============================================
# TTL Constants
# ============================================

class CacheTTL:
    """
    Tiempos de vida estándar para diferentes tipos de datos.

    Criterio:
    - Datos que cambian raramente: 1 hora+
    - Datos que cambian frecuentemente: 5-10 minutos
    - Datos en tiempo real: 1 minuto o sin caché
    """

    DEVICE_SCHEMA = 3600  # 1 hora (cambia raramente)
    DEVICE_HEALTH = 300   # 5 minutos (actualiza periódicamente)
    DEVICE_LIST = 300  # 5 minutos (listado de devices)
    HEALTH_DASHBOARD = 60  # 1 minuto (datos frescos)
    USER_PERMISSIONS = 1800  # 30 minutos (cambios poco frecuentes)
    READINGS_STATS = 600  # 10 minutos (estadísticas agregadas)
    ALERT_RULES = 600  # 10 minutos (cambios ocasionales)


# ============================================
# Global Cache Instance
# ============================================

# Instancia global del caché
cache = RedisCache()
