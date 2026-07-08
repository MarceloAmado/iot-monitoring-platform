"""add_performance_indexes

Revision ID: 1afb914f65d5
Revises: e5bf88e49fde
Create Date: 2025-12-08 20:48:09.795004

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '1afb914f65d5'
down_revision: Union[str, None] = 'e5bf88e49fde'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """
    Agregar índices de performance para queries críticas.
    Usa CREATE INDEX IF NOT EXISTS para idempotencia (safe re-run).
    """
    conn = op.get_bind()

    # SENSOR_READINGS
    conn.execute(sa.text(
        'CREATE INDEX IF NOT EXISTS idx_readings_device_time_desc '
        'ON sensor_readings (device_id, "timestamp" DESC)'
    ))
    conn.execute(sa.text(
        'CREATE INDEX IF NOT EXISTS idx_readings_timestamp_desc '
        'ON sensor_readings ("timestamp" DESC)'
    ))

    # ALERT_HISTORY
    conn.execute(sa.text(
        'CREATE INDEX IF NOT EXISTS idx_alert_history_device_time '
        'ON alert_history (device_id, triggered_at DESC)'
    ))
    conn.execute(sa.text(
        'CREATE INDEX IF NOT EXISTS idx_alert_history_unacknowledged '
        'ON alert_history (device_id) WHERE acknowledged_by IS NULL'
    ))

    # DEVICES
    conn.execute(sa.text(
        'CREATE INDEX IF NOT EXISTS idx_devices_status_last_seen '
        'ON devices (status, last_seen_at DESC)'
    ))

    # USERS
    conn.execute(sa.text(
        'CREATE UNIQUE INDEX IF NOT EXISTS idx_users_email_unique '
        'ON users (email)'
    ))

    # ASSETS
    conn.execute(sa.text(
        'CREATE INDEX IF NOT EXISTS idx_assets_location '
        'ON assets (location_id)'
    ))


def downgrade() -> None:
    """
    Eliminar índices de performance (espejo exacto de upgrade).
    Usa DROP INDEX IF EXISTS para idempotencia (safe re-run).
    """
    conn = op.get_bind()

    # Eliminar en orden inverso al upgrade
    conn.execute(sa.text('DROP INDEX IF EXISTS idx_assets_location'))
    conn.execute(sa.text('DROP INDEX IF EXISTS idx_users_email_unique'))
    conn.execute(sa.text('DROP INDEX IF EXISTS idx_devices_status_last_seen'))
    conn.execute(sa.text('DROP INDEX IF EXISTS idx_alert_history_unacknowledged'))
    conn.execute(sa.text('DROP INDEX IF EXISTS idx_alert_history_device_time'))
    conn.execute(sa.text('DROP INDEX IF EXISTS idx_readings_timestamp_desc'))
    conn.execute(sa.text('DROP INDEX IF EXISTS idx_readings_device_time_desc'))
