"""initial_migration_create_all_tables

Crea todas las 8 tablas del sistema:
- location_groups
- locations
- assets
- devices
- sensor_readings
- users
- alert_rules
- alert_history

Revision ID: 5494f0ce411a
Revises:
Create Date: 2025-10-16 17:54:43.949598

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '5494f0ce411a'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. Tabla location_groups
    op.create_table(
        'location_groups',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('name', sa.String(length=128), nullable=False, comment='Nombre único del grupo de ubicación'),
        sa.Column('description', sa.Text(), nullable=True, comment='Descripción opcional del grupo'),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('now()'), comment='Fecha de creación del registro'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('name')
    )
    op.create_index(op.f('ix_location_groups_id'), 'location_groups', ['id'], unique=False)
    op.create_index(op.f('ix_location_groups_name'), 'location_groups', ['name'], unique=True)

    # 2. Tabla locations
    op.create_table(
        'locations',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('location_group_id', sa.Integer(), nullable=False, comment='ID del grupo al que pertenece'),
        sa.Column('name', sa.String(length=128), nullable=False, comment='Nombre de la ubicación'),
        sa.Column('code', sa.String(length=32), nullable=True, comment='Código corto único (ej: LAB-QUI, SALA-URG)'),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('now()'), comment='Fecha de creación del registro'),
        sa.ForeignKeyConstraint(['location_group_id'], ['location_groups.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('code')
    )
    op.create_index('idx_locations_group', 'locations', ['location_group_id'], unique=False)
    op.create_index(op.f('ix_locations_id'), 'locations', ['id'], unique=False)
    op.create_index(op.f('ix_locations_code'), 'locations', ['code'], unique=True)

    # 3. Tabla assets
    op.create_table(
        'assets',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('location_id', sa.Integer(), nullable=False, comment='ID de la ubicación donde está el asset'),
        sa.Column('name', sa.String(length=128), nullable=False, comment='Nombre del asset (ej: Heladera_Química_001)'),
        sa.Column('type', sa.String(length=64), nullable=False, comment='Tipo de asset: refrigerator, compressor, room, etc.'),
        sa.Column('description', sa.Text(), nullable=True, comment='Descripción detallada del asset'),
        sa.Column('extra_data', postgresql.JSONB(astext_type=sa.Text()), nullable=True, comment='Metadata adicional en formato JSON (capacidad, marca, modelo, etc.)'),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('now()'), comment='Fecha de creación del registro'),
        sa.ForeignKeyConstraint(['location_id'], ['locations.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('idx_assets_location', 'assets', ['location_id'], unique=False)
    op.create_index('idx_assets_type', 'assets', ['type'], unique=False)
    op.create_index(op.f('ix_assets_id'), 'assets', ['id'], unique=False)

    # 4. Tabla devices
    op.create_table(
        'devices',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('asset_id', sa.Integer(), nullable=True, comment='ID del asset al que está asignado actualmente (NULL si no asignado)'),
        sa.Column('device_eui', sa.String(length=64), nullable=False, comment='ID único del device (MAC address o custom)'),
        sa.Column('name', sa.String(length=128), nullable=False, comment='Nombre amigable del device'),
        sa.Column('status', sa.String(length=32), nullable=False, server_default='active', comment='Estado: active, inactive, maintenance, error'),
        sa.Column('firmware_version', sa.String(length=20), nullable=True, comment='Versión del firmware (para OTA updates)'),
        sa.Column('last_seen_at', sa.DateTime(), nullable=True, comment='Última comunicación exitosa con el backend'),
        sa.Column('config', postgresql.JSONB(astext_type=sa.Text()), nullable=True, comment='Configuración del device (sampling_interval_sec, wifi_ssid, etc.)'),
        sa.Column('extra_data', postgresql.JSONB(astext_type=sa.Text()), nullable=True, comment='Metadata adicional (mac_address, rssi_dbm, battery_mv, etc.)'),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('now()'), comment='Fecha de creación del registro'),
        sa.CheckConstraint("status IN ('active', 'inactive', 'maintenance', 'error')", name='check_device_status'),
        sa.ForeignKeyConstraint(['asset_id'], ['assets.id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('device_eui')
    )
    op.create_index('idx_devices_asset', 'devices', ['asset_id'], unique=False)
    op.create_index('idx_devices_eui', 'devices', ['device_eui'], unique=True)
    op.create_index('idx_devices_last_seen', 'devices', ['last_seen_at'], unique=False)
    op.create_index(op.f('ix_devices_id'), 'devices', ['id'], unique=False)
    op.create_index(op.f('ix_devices_device_eui'), 'devices', ['device_eui'], unique=True)
    op.create_index(op.f('ix_devices_last_seen_at'), 'devices', ['last_seen_at'], unique=False)
    op.create_index(op.f('ix_devices_status'), 'devices', ['status'], unique=False)

    # 5. Tabla sensor_readings (CRÍTICA)
    op.create_table(
        'sensor_readings',
        sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=False, comment='ID autoincremental (BIGINT para millones de registros)'),
        sa.Column('device_id', sa.Integer(), nullable=False, comment='ID del device que generó esta lectura'),
        sa.Column('data_payload', postgresql.JSONB(astext_type=sa.Text()), nullable=False, comment='Datos de la medición en formato JSON flexible'),
        sa.Column('quality_score', sa.Float(), nullable=True, comment='Score de calidad de la lectura (0.0-1.0): 1.0=perfecto, 0.0=inválido'),
        sa.Column('processed', sa.Boolean(), nullable=False, server_default='false', comment='Indica si ya fue procesado por el sistema de alertas'),
        sa.Column('timestamp', sa.DateTime(), nullable=False, server_default=sa.text('now()'), comment='Momento de la medición (UTC)'),
        sa.CheckConstraint('quality_score IS NULL OR (quality_score >= 0 AND quality_score <= 1)', name='check_quality_score_range'),
        sa.ForeignKeyConstraint(['device_id'], ['devices.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('idx_readings_device_time', 'sensor_readings', ['device_id', 'timestamp'], unique=False, postgresql_using='btree')
    op.create_index('idx_readings_processed', 'sensor_readings', ['processed'], unique=False)
    op.create_index('idx_readings_payload', 'sensor_readings', ['data_payload'], unique=False, postgresql_using='gin')
    op.create_index(op.f('ix_sensor_readings_id'), 'sensor_readings', ['id'], unique=False)
    op.create_index(op.f('ix_sensor_readings_device_id'), 'sensor_readings', ['device_id'], unique=False)
    op.create_index(op.f('ix_sensor_readings_processed'), 'sensor_readings', ['processed'], unique=False)
    op.create_index(op.f('ix_sensor_readings_timestamp'), 'sensor_readings', ['timestamp'], unique=False)

    # 6. Tabla users
    op.create_table(
        'users',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('email', sa.String(length=255), nullable=False, comment='Email único del usuario (usado para login)'),
        sa.Column('password_hash', sa.String(length=255), nullable=False, comment='Hash bcrypt de la contraseña (NUNCA plaintext)'),
        sa.Column('role', sa.String(length=32), nullable=False, comment='Rol del usuario: super_admin, service_admin, technician, guest'),
        sa.Column('allowed_location_ids', postgresql.ARRAY(sa.Integer()), nullable=True, comment='Array de IDs de locations que puede ver (NULL=todas si super_admin)'),
        sa.Column('first_name', sa.String(length=64), nullable=False, comment='Nombre del usuario'),
        sa.Column('last_name', sa.String(length=64), nullable=False, comment='Apellido del usuario'),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default='true', comment='Permite desactivar usuarios sin eliminarlos'),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('now()'), comment='Fecha de creación del usuario'),
        sa.Column('last_login_at', sa.DateTime(), nullable=True, comment='Fecha del último login exitoso'),
        sa.CheckConstraint("role IN ('super_admin', 'service_admin', 'technician', 'guest')", name='check_user_role'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('email')
    )
    op.create_index('idx_users_active', 'users', ['is_active'], unique=False)
    op.create_index('idx_users_email', 'users', ['email'], unique=True)
    op.create_index('idx_users_role', 'users', ['role'], unique=False)
    op.create_index(op.f('ix_users_id'), 'users', ['id'], unique=False)
    op.create_index(op.f('ix_users_email'), 'users', ['email'], unique=True)
    op.create_index(op.f('ix_users_is_active'), 'users', ['is_active'], unique=False)
    op.create_index(op.f('ix_users_role'), 'users', ['role'], unique=False)

    # 7. Tabla alert_rules
    op.create_table(
        'alert_rules',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('location_id', sa.Integer(), nullable=True, comment='ID de location específica (NULL = regla global)'),
        sa.Column('device_id', sa.Integer(), nullable=True, comment='ID de device específico (NULL = aplica a todos los devices de la location)'),
        sa.Column('name', sa.String(length=128), nullable=False, comment='Nombre descriptivo de la regla'),
        sa.Column('check_type', sa.String(length=32), nullable=False, comment='Tipo de chequeo: THRESHOLD_ABOVE, THRESHOLD_BELOW, THRESHOLD_RANGE, etc.'),
        sa.Column('variable_key', sa.String(length=64), nullable=False, comment='Key del JSONB a evaluar (ej: temp_c, humidity_pct)'),
        sa.Column('threshold_value', sa.Float(), nullable=True, comment='Valor umbral para THRESHOLD_ABOVE/BELOW'),
        sa.Column('threshold_min', sa.Float(), nullable=True, comment='Valor mínimo para THRESHOLD_RANGE'),
        sa.Column('threshold_max', sa.Float(), nullable=True, comment='Valor máximo para THRESHOLD_RANGE'),
        sa.Column('time_window_minutes', sa.Integer(), nullable=True, comment='Ventana de tiempo para RATE_OF_CHANGE y DEVICE_OFFLINE'),
        sa.Column('enabled', sa.Boolean(), nullable=False, server_default='true', comment='Permite desactivar reglas sin eliminarlas'),
        sa.Column('cooldown_minutes', sa.Integer(), nullable=False, server_default='30', comment='Tiempo mínimo entre alertas consecutivas (evita spam)'),
        sa.Column('notification_channels', postgresql.JSONB(astext_type=sa.Text()), nullable=False, comment='Canales de notificación: ["email", "telegram", "webhook"]'),
        sa.Column('webhook_url', sa.Text(), nullable=True, comment='URL para POST si webhook está en notification_channels'),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('now()'), comment='Fecha de creación de la regla'),
        sa.CheckConstraint("""check_type IN (
                'THRESHOLD_ABOVE',
                'THRESHOLD_BELOW',
                'THRESHOLD_RANGE',
                'RATE_OF_CHANGE',
                'DEVICE_OFFLINE',
                'SENSOR_FAULT',
                'ANOMALY_ML'
            )""", name='check_alert_rule_type'),
        sa.ForeignKeyConstraint(['device_id'], ['devices.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['location_id'], ['locations.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('idx_alert_rules_device', 'alert_rules', ['device_id'], unique=False)
    op.create_index('idx_alert_rules_enabled', 'alert_rules', ['enabled'], unique=False)
    op.create_index('idx_alert_rules_location', 'alert_rules', ['location_id'], unique=False)
    op.create_index(op.f('ix_alert_rules_id'), 'alert_rules', ['id'], unique=False)
    op.create_index(op.f('ix_alert_rules_check_type'), 'alert_rules', ['check_type'], unique=False)
    op.create_index(op.f('ix_alert_rules_device_id'), 'alert_rules', ['device_id'], unique=False)
    op.create_index(op.f('ix_alert_rules_enabled'), 'alert_rules', ['enabled'], unique=False)
    op.create_index(op.f('ix_alert_rules_location_id'), 'alert_rules', ['location_id'], unique=False)

    # 8. Tabla alert_history
    op.create_table(
        'alert_history',
        sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=False, comment='ID autoincremental (BIGINT para muchos registros)'),
        sa.Column('alert_rule_id', sa.Integer(), nullable=False, comment='ID de la regla que disparó la alerta'),
        sa.Column('device_id', sa.Integer(), nullable=False, comment='ID del device que causó la alerta'),
        sa.Column('sensor_reading_id', sa.BigInteger(), nullable=True, comment='ID del reading que disparó (NULL si DEVICE_OFFLINE)'),
        sa.Column('triggered_at', sa.DateTime(), nullable=False, server_default=sa.text('now()'), comment='Momento en que se disparó la alerta'),
        sa.Column('value_observed', sa.Float(), nullable=True, comment='Valor que causó la alerta (si aplica)'),
        sa.Column('message', sa.Text(), nullable=False, comment='Mensaje generado describiendo la alerta'),
        sa.Column('notification_sent', postgresql.JSONB(astext_type=sa.Text()), nullable=True, comment='Resultado de notificaciones: {"email": "success", "telegram": "failed"}'),
        sa.Column('acknowledged_by', sa.Integer(), nullable=True, comment='ID del usuario que reconoció/vio la alerta'),
        sa.Column('acknowledged_at', sa.DateTime(), nullable=True, comment='Momento en que fue reconocida la alerta'),
        sa.ForeignKeyConstraint(['acknowledged_by'], ['users.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['alert_rule_id'], ['alert_rules.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['device_id'], ['devices.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['sensor_reading_id'], ['sensor_readings.id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('idx_alert_history_ack_by', 'alert_history', ['acknowledged_by'], unique=False)
    op.create_index('idx_alert_history_device', 'alert_history', ['device_id'], unique=False)
    op.create_index('idx_alert_history_rule', 'alert_history', ['alert_rule_id'], unique=False)
    op.create_index('idx_alert_history_triggered', 'alert_history', ['triggered_at'], unique=False, postgresql_using='btree')
    op.create_index(op.f('ix_alert_history_id'), 'alert_history', ['id'], unique=False)
    op.create_index(op.f('ix_alert_history_acknowledged_by'), 'alert_history', ['acknowledged_by'], unique=False)
    op.create_index(op.f('ix_alert_history_sensor_reading_id'), 'alert_history', ['sensor_reading_id'], unique=False)


def downgrade() -> None:
    # Eliminar tablas en orden inverso (respetando foreign keys)
    op.drop_table('alert_history')
    op.drop_table('alert_rules')
    op.drop_table('users')
    op.drop_table('sensor_readings')
    op.drop_table('devices')
    op.drop_table('assets')
    op.drop_table('locations')
    op.drop_table('location_groups')
