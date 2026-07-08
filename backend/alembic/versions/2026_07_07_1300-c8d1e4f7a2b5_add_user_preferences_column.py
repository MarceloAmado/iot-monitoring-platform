"""add_user_preferences_column

Columna JSONB para persistir las preferencias de UI del usuario
(notificaciones, tema, formato de fecha) desde la página Settings.

Revision ID: c8d1e4f7a2b5
Revises: b3f2a8c41d97
Create Date: 2026-07-07 13:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'c8d1e4f7a2b5'
down_revision: Union[str, None] = 'b3f2a8c41d97'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Agregar columna preferences a users (idempotente)."""
    conn = op.get_bind()
    inspector = sa.inspect(conn)

    # Si la tabla no existe (DB provisionada por Base.metadata.create_all,
    # que ya incluye la columna desde el modelo), no hay nada que alterar.
    if 'users' not in inspector.get_table_names():
        return

    conn.execute(sa.text(
        'ALTER TABLE users ADD COLUMN IF NOT EXISTS preferences JSONB'
    ))


def downgrade() -> None:
    """Eliminar columna preferences de users."""
    conn = op.get_bind()
    inspector = sa.inspect(conn)

    if 'users' not in inspector.get_table_names():
        return

    conn.execute(sa.text(
        'ALTER TABLE users DROP COLUMN IF EXISTS preferences'
    ))
