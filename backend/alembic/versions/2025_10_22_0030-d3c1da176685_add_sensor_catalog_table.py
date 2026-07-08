"""add_sensor_catalog_table

Revision ID: d3c1da176685
Revises: 7434c05be701
Create Date: 2025-10-22 00:30:27.006719

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'd3c1da176685'
down_revision: Union[str, None] = '7434c05be701'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Crear tabla sensor_catalog
    op.create_table(
        'sensor_catalog',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(length=128), nullable=False, comment='Nombre único del sensor'),
        sa.Column('sensor_type', sa.String(length=64), nullable=False, comment='Tipo: temperature, humidity, pressure, analog, digital, custom'),
        sa.Column('description', sa.Text(), nullable=True, comment='Descripción del sensor'),
        sa.Column('gpio_pin', sa.Integer(), nullable=True, comment='Pin GPIO para lectura ADC/Digital'),
        sa.Column('protocol', sa.String(length=32), nullable=True, comment='Protocolo de comunicación: OneWire, I2C, SPI, ADC, Digital'),
        sa.Column('i2c_address', sa.String(length=10), nullable=True, comment='Dirección I2C si aplica (ej: 0x76)'),
        sa.Column('calibration_offset', sa.Float(), nullable=True, comment='Offset de calibración'),
        sa.Column('calibration_factor', sa.Float(), nullable=True, comment='Factor multiplicador de calibración'),
        sa.Column('value_min', sa.Float(), nullable=True, comment='Valor mínimo esperado'),
        sa.Column('value_max', sa.Float(), nullable=True, comment='Valor máximo esperado'),
        sa.Column('unit', sa.String(length=32), nullable=True, comment='Unidad de medida: °C, %, kPa, bar, V, mA'),
        sa.Column('decimal_places', sa.Integer(), nullable=True, comment='Decimales para mostrar'),
        sa.Column('config', sa.JSON(), nullable=True, comment="Config JSON: {'adc_bits': 12, 'voltage_divider': 2, 'samples': 10}"),
        sa.Column('manufacturer', sa.String(length=128), nullable=True, comment='Fabricante del sensor'),
        sa.Column('model', sa.String(length=128), nullable=True, comment='Modelo del sensor'),
        sa.Column('datasheet_url', sa.Text(), nullable=True, comment='URL del datasheet'),
        sa.Column('is_active', sa.Boolean(), nullable=True, comment='Sensor activo en el sistema'),
        sa.Column('is_builtin', sa.Boolean(), nullable=True, comment='Sensor built-in (DS18B20, DHT22, MPX5700) no se puede eliminar'),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('name')
    )

    # Crear índices
    op.create_index('idx_sensor_catalog_type', 'sensor_catalog', ['sensor_type'])
    op.create_index('idx_sensor_catalog_protocol', 'sensor_catalog', ['protocol'])
    op.create_index('idx_sensor_catalog_active', 'sensor_catalog', ['is_active'])
    op.create_index(op.f('ix_sensor_catalog_id'), 'sensor_catalog', ['id'], unique=False)


def downgrade() -> None:
    # Eliminar índices
    op.drop_index(op.f('ix_sensor_catalog_id'), table_name='sensor_catalog')
    op.drop_index('idx_sensor_catalog_active', table_name='sensor_catalog')
    op.drop_index('idx_sensor_catalog_protocol', table_name='sensor_catalog')
    op.drop_index('idx_sensor_catalog_type', table_name='sensor_catalog')

    # Eliminar tabla
    op.drop_table('sensor_catalog')
