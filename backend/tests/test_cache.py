"""
Tests para el servicio de caché Redis.

Cubre:
- Operaciones CRUD de caché (set, get, delete)
- Delete por patrón
- Exists, increment, expire
- Graceful degradation cuando Redis no está disponible
- CacheKeys helper
- CacheTTL constants
"""

import json
import pytest
from unittest.mock import patch, MagicMock, PropertyMock

from app.services.cache_service import RedisCache, CacheKeys, CacheTTL


# ============================================
# FIXTURES
# ============================================


@pytest.fixture
def mock_redis_client():
    """Mock del cliente Redis."""
    client = MagicMock()
    client.ping.return_value = True
    return client


@pytest.fixture
def cache_with_redis(mock_redis_client):
    """RedisCache con un cliente Redis mockeado."""
    with patch("app.services.cache_service.redis.Redis", return_value=mock_redis_client):
        cache = RedisCache()
    return cache


@pytest.fixture
def cache_without_redis():
    """RedisCache sin conexión Redis (graceful degradation)."""
    with patch("app.services.cache_service.redis.Redis") as MockRedis:
        MockRedis.return_value.ping.side_effect = Exception("Connection refused")
        cache = RedisCache()
    return cache


# ============================================
# TEST: SET
# ============================================


class TestCacheSet:
    """Tests para RedisCache.set()."""

    def test_set_value_with_ttl(self, cache_with_redis, mock_redis_client):
        """Guardar valor con TTL."""
        result = cache_with_redis.set("test:key", {"data": "value"}, ttl=300)
        assert result is True
        mock_redis_client.setex.assert_called_once_with(
            "test:key", 300, json.dumps({"data": "value"})
        )

    def test_set_value_without_ttl(self, cache_with_redis, mock_redis_client):
        """Guardar valor sin TTL."""
        result = cache_with_redis.set("test:key", {"data": "value"})
        assert result is True
        mock_redis_client.set.assert_called_once_with(
            "test:key", json.dumps({"data": "value"})
        )

    def test_set_serializes_complex_types(self, cache_with_redis, mock_redis_client):
        """Serializa correctamente tipos complejos."""
        complex_data = {"list": [1, 2, 3], "nested": {"a": True}, "null": None}
        cache_with_redis.set("complex:key", complex_data, ttl=60)
        call_args = mock_redis_client.setex.call_args
        stored_value = call_args[0][2]
        assert json.loads(stored_value) == complex_data

    def test_set_returns_false_when_unavailable(self, cache_without_redis):
        """Retorna False cuando Redis no está disponible."""
        result = cache_without_redis.set("key", "value")
        assert result is False

    def test_set_handles_exception(self, cache_with_redis, mock_redis_client):
        """Maneja excepciones de Redis gracefully."""
        mock_redis_client.setex.side_effect = Exception("Redis error")
        result = cache_with_redis.set("key", "value", ttl=60)
        assert result is False


# ============================================
# TEST: GET
# ============================================


class TestCacheGet:
    """Tests para RedisCache.get()."""

    def test_get_existing_value(self, cache_with_redis, mock_redis_client):
        """Obtener valor existente."""
        mock_redis_client.get.return_value = json.dumps({"temp": 25.5})
        result = cache_with_redis.get("test:key")
        assert result == {"temp": 25.5}
        mock_redis_client.get.assert_called_once_with("test:key")

    def test_get_nonexistent_key(self, cache_with_redis, mock_redis_client):
        """Retorna None para clave inexistente."""
        mock_redis_client.get.return_value = None
        result = cache_with_redis.get("missing:key")
        assert result is None

    def test_get_returns_none_when_unavailable(self, cache_without_redis):
        """Retorna None cuando Redis no está disponible."""
        result = cache_without_redis.get("key")
        assert result is None

    def test_get_handles_exception(self, cache_with_redis, mock_redis_client):
        """Maneja excepciones de Redis gracefully."""
        mock_redis_client.get.side_effect = Exception("Redis error")
        result = cache_with_redis.get("key")
        assert result is None


# ============================================
# TEST: DELETE
# ============================================


class TestCacheDelete:
    """Tests para RedisCache.delete()."""

    def test_delete_key(self, cache_with_redis, mock_redis_client):
        """Eliminar una clave."""
        result = cache_with_redis.delete("test:key")
        assert result is True
        mock_redis_client.delete.assert_called_once_with("test:key")

    def test_delete_returns_false_when_unavailable(self, cache_without_redis):
        """Retorna False cuando Redis no está disponible."""
        result = cache_without_redis.delete("key")
        assert result is False


# ============================================
# TEST: DELETE PATTERN
# ============================================


class TestCacheDeletePattern:
    """Tests para RedisCache.delete_pattern()."""

    def test_delete_pattern_with_matches(self, cache_with_redis, mock_redis_client):
        """Eliminar claves por patrón."""
        mock_redis_client.keys.return_value = ["device:1:schema", "device:2:schema"]
        mock_redis_client.delete.return_value = 2
        result = cache_with_redis.delete_pattern("device:*:schema")
        assert result == 2
        mock_redis_client.keys.assert_called_once_with("device:*:schema")
        mock_redis_client.delete.assert_called_once_with("device:1:schema", "device:2:schema")

    def test_delete_pattern_no_matches(self, cache_with_redis, mock_redis_client):
        """Retorna 0 cuando no hay claves que coincidan."""
        mock_redis_client.keys.return_value = []
        result = cache_with_redis.delete_pattern("nonexistent:*")
        assert result == 0

    def test_delete_pattern_returns_zero_when_unavailable(self, cache_without_redis):
        """Retorna 0 cuando Redis no está disponible."""
        result = cache_without_redis.delete_pattern("device:*")
        assert result == 0


# ============================================
# TEST: EXISTS
# ============================================


class TestCacheExists:
    """Tests para RedisCache.exists()."""

    def test_exists_true(self, cache_with_redis, mock_redis_client):
        """Clave existe."""
        mock_redis_client.exists.return_value = 1
        assert cache_with_redis.exists("test:key") is True

    def test_exists_false(self, cache_with_redis, mock_redis_client):
        """Clave no existe."""
        mock_redis_client.exists.return_value = 0
        assert cache_with_redis.exists("missing:key") is False

    def test_exists_returns_false_when_unavailable(self, cache_without_redis):
        """Retorna False cuando Redis no está disponible."""
        assert cache_without_redis.exists("key") is False


# ============================================
# TEST: INCREMENT
# ============================================


class TestCacheIncrement:
    """Tests para RedisCache.increment()."""

    def test_increment_default(self, cache_with_redis, mock_redis_client):
        """Incrementar por 1 (default)."""
        mock_redis_client.incrby.return_value = 5
        result = cache_with_redis.increment("counter:key")
        assert result == 5
        mock_redis_client.incrby.assert_called_once_with("counter:key", 1)

    def test_increment_custom_amount(self, cache_with_redis, mock_redis_client):
        """Incrementar por cantidad custom."""
        mock_redis_client.incrby.return_value = 10
        result = cache_with_redis.increment("counter:key", amount=5)
        assert result == 10
        mock_redis_client.incrby.assert_called_once_with("counter:key", 5)

    def test_increment_returns_none_when_unavailable(self, cache_without_redis):
        """Retorna None cuando Redis no está disponible."""
        result = cache_without_redis.increment("key")
        assert result is None


# ============================================
# TEST: EXPIRE
# ============================================


class TestCacheExpire:
    """Tests para RedisCache.expire()."""

    def test_expire_key(self, cache_with_redis, mock_redis_client):
        """Establecer TTL en clave existente."""
        mock_redis_client.expire.return_value = True
        result = cache_with_redis.expire("test:key", 600)
        assert result is True
        mock_redis_client.expire.assert_called_once_with("test:key", 600)

    def test_expire_returns_false_when_unavailable(self, cache_without_redis):
        """Retorna False cuando Redis no está disponible."""
        result = cache_without_redis.expire("key", 300)
        assert result is False


# ============================================
# TEST: GRACEFUL DEGRADATION
# ============================================


class TestGracefulDegradation:
    """Tests que verifican que el sistema funciona sin Redis."""

    def test_all_operations_return_safe_defaults(self, cache_without_redis):
        """Todas las operaciones retornan valores seguros sin Redis."""
        assert cache_without_redis.set("key", "value") is False
        assert cache_without_redis.get("key") is None
        assert cache_without_redis.delete("key") is False
        assert cache_without_redis.delete_pattern("*") == 0
        assert cache_without_redis.exists("key") is False
        assert cache_without_redis.increment("key") is None
        assert cache_without_redis.expire("key", 60) is False

    def test_is_available_false(self, cache_without_redis):
        """_is_available retorna False sin conexión."""
        assert cache_without_redis._is_available() is False

    def test_is_available_true(self, cache_with_redis):
        """_is_available retorna True con conexión."""
        assert cache_with_redis._is_available() is True


# ============================================
# TEST: CACHE KEYS HELPER
# ============================================


class TestCacheKeys:
    """Tests para CacheKeys helper."""

    def test_device_schema_key(self):
        assert CacheKeys.device_schema(1) == "device:1:schema"
        assert CacheKeys.device_schema(42) == "device:42:schema"

    def test_device_health_key(self):
        assert CacheKeys.device_health(1) == "device:1:health"

    def test_health_dashboard_key(self):
        assert CacheKeys.health_dashboard() == "health:dashboard"

    def test_user_permissions_key(self):
        assert CacheKeys.user_permissions(5) == "user:5:permissions"

    def test_readings_stats_key(self):
        assert CacheKeys.readings_stats(3) == "readings:3:stats"

    def test_alert_rules_active_key(self):
        assert CacheKeys.alert_rules_active() == "alert_rules:active"


# ============================================
# TEST: CACHE TTL CONSTANTS
# ============================================


class TestCacheTTL:
    """Tests para CacheTTL constantes."""

    def test_ttl_values_are_positive(self):
        """Todos los TTL son positivos."""
        assert CacheTTL.DEVICE_SCHEMA > 0
        assert CacheTTL.DEVICE_HEALTH > 0
        assert CacheTTL.DEVICE_LIST > 0
        assert CacheTTL.HEALTH_DASHBOARD > 0
        assert CacheTTL.USER_PERMISSIONS > 0
        assert CacheTTL.READINGS_STATS > 0
        assert CacheTTL.ALERT_RULES > 0

    def test_ttl_hierarchy(self):
        """TTL de datos en tiempo real < TTL de datos periódicos."""
        assert CacheTTL.HEALTH_DASHBOARD < CacheTTL.DEVICE_HEALTH
        assert CacheTTL.DEVICE_HEALTH <= CacheTTL.DEVICE_SCHEMA
