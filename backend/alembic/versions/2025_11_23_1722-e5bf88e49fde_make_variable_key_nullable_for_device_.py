"""make variable_key nullable for device_offline alerts

Revision ID: e5bf88e49fde
Revises: 035e1efdb618
Create Date: 2025-11-23 17:22:49.705199

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = 'e5bf88e49fde'
down_revision: Union[str, None] = '035e1efdb618'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Modificar columna variable_key para permitir NULL (necesario para DEVICE_OFFLINE)
    op.alter_column('alert_rules', 'variable_key',
                    existing_type=sa.String(length=64),
                    nullable=True,
                    comment='Key del JSONB a evaluar (ej: temp_c, humidity_pct). NULL para DEVICE_OFFLINE')


def downgrade() -> None:
    # Revertir columna variable_key a NOT NULL
    op.alter_column('alert_rules', 'variable_key',
                    existing_type=sa.String(length=64),
                    nullable=False,
                    comment='Key del JSONB a evaluar (ej: temp_c, humidity_pct)')
