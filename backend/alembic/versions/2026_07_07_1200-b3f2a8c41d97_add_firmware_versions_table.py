"""add_firmware_versions_table

La tabla firmware_versions existía solo vía Base.metadata.create_all()
(dev y tests) pero nunca tuvo migración: una DB de producción migrada
únicamente con Alembic no la tenía y el módulo OTA fallaba.

Es idempotente: si la tabla ya existe (creada por create_all), no hace nada.

Revision ID: b3f2a8c41d97
Revises: 1afb914f65d5
Create Date: 2026-07-07 12:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'b3f2a8c41d97'
down_revision: Union[str, None] = '1afb914f65d5'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Crear tabla firmware_versions (modelo app/models/firmware.py)."""
    conn = op.get_bind()
    inspector = sa.inspect(conn)

    if 'firmware_versions' in inspector.get_table_names():
        # Ya creada por Base.metadata.create_all() — solo registrar la revisión
        return

    op.create_table(
        'firmware_versions',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('version', sa.String(length=20), nullable=False,
                  comment='Versión semver (ej: 1.2.3, 2.0.0-beta)'),
        sa.Column('file_path', sa.String(length=512), nullable=False,
                  comment='Path relativo del binario (ej: firmware/esp32_v1.2.3.bin)'),
        sa.Column('file_size_bytes', sa.Integer(), nullable=False,
                  comment='Tamaño del archivo en bytes'),
        sa.Column('md5_checksum', sa.String(length=32), nullable=False,
                  comment='MD5 checksum para verificar integridad'),
        sa.Column('release_notes', sa.Text(), nullable=True,
                  comment='Notas de la release (changelog)'),
        sa.Column('is_stable', sa.Boolean(), nullable=False,
                  server_default=sa.text('true'),
                  comment='True si es estable, False si es beta/rc'),
        sa.Column('is_latest', sa.Boolean(), nullable=False,
                  server_default=sa.text('false'),
                  comment='True si es la versión más reciente'),
        sa.Column('min_compatible_version', sa.String(length=20), nullable=True,
                  comment='Versión mínima desde la cual se puede actualizar'),
        sa.Column('created_at', sa.DateTime(), nullable=False,
                  server_default=sa.text('now()'),
                  comment='Fecha de creación del registro'),
        sa.Column('created_by_user_id', sa.Integer(), nullable=True,
                  comment='ID del usuario que subió el firmware'),
        sa.PrimaryKeyConstraint('id'),
    )

    op.create_index('ix_firmware_versions_id', 'firmware_versions', ['id'])
    op.create_index('ix_firmware_versions_version', 'firmware_versions', ['version'], unique=True)
    op.create_index('idx_firmware_version', 'firmware_versions', ['version'])
    op.create_index('idx_firmware_is_latest', 'firmware_versions', ['is_latest'])
    op.create_index('idx_firmware_created', 'firmware_versions', ['created_at'])


def downgrade() -> None:
    """Eliminar tabla firmware_versions."""
    conn = op.get_bind()
    conn.execute(sa.text('DROP TABLE IF EXISTS firmware_versions'))
