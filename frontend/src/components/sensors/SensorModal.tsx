/**
 * SensorModal Component - Modal para crear/editar sensores del catálogo
 *
 * Funcionalidades:
 * - Crear nuevo sensor personalizado
 * - Editar sensor existente (excepto built-in)
 * - Validación de formulario
 * - Campos dinámicos según tipo de sensor
 * - Configuración de calibración
 */

import { useState, useEffect } from 'react';
import { useMutation } from '@tanstack/react-query';
import sensorService from '../../services/sensorService';
import { SensorCatalog, SensorCatalogCreate, SensorCatalogUpdate } from '../../types';

interface SensorModalProps {
  sensor: SensorCatalog | null; // null = crear nuevo, sensor = editar
  onClose: () => void;
  onSuccess: () => void;
}

export default function SensorModal({ sensor, onClose, onSuccess }: SensorModalProps) {
  const isEditing = sensor !== null;
  const isBuiltin = sensor?.is_builtin || false;

  // Estado del formulario
  const [formData, setFormData] = useState<SensorCatalogCreate>({
    name: '',
    sensor_type: 'temperature',
    description: '',
    gpio_pin: null,
    protocol: 'ADC',
    i2c_address: '',
    calibration_offset: 0,
    calibration_factor: 1,
    value_min: null,
    value_max: null,
    unit: '°C',
    decimal_places: 2,
    config: null,
    manufacturer: '',
    model: '',
    datasheet_url: '',
    is_active: true,
  });

  const [errors, setErrors] = useState<Record<string, string>>({});

  // Cargar datos del sensor si estamos editando
  useEffect(() => {
    if (sensor) {
      setFormData({
        name: sensor.name,
        sensor_type: sensor.sensor_type,
        description: sensor.description || '',
        gpio_pin: sensor.gpio_pin,
        protocol: sensor.protocol || 'ADC',
        i2c_address: sensor.i2c_address || '',
        calibration_offset: sensor.calibration_offset,
        calibration_factor: sensor.calibration_factor,
        value_min: sensor.value_min,
        value_max: sensor.value_max,
        unit: sensor.unit || '',
        decimal_places: sensor.decimal_places,
        config: sensor.config,
        manufacturer: sensor.manufacturer || '',
        model: sensor.model || '',
        datasheet_url: sensor.datasheet_url || '',
        is_active: sensor.is_active,
      });
    }
  }, [sensor]);

  // Actualizar unidad cuando cambia el tipo de sensor
  useEffect(() => {
    const units = sensorService.getCommonUnits(formData.sensor_type);
    if (units.length > 0 && !isEditing) {
      setFormData((prev) => ({ ...prev, unit: units[0] }));
    }
  }, [formData.sensor_type, isEditing]);

  // Mutations
  const createMutation = useMutation({
    mutationFn: (data: SensorCatalogCreate) => sensorService.createSensor(data),
    onSuccess: () => {
      onSuccess();
    },
    onError: (error: any) => {
      const detail = error.response?.data?.detail || error.message;
      setErrors({ submit: detail });
    },
  });

  const updateMutation = useMutation({
    mutationFn: (data: SensorCatalogUpdate) => sensorService.updateSensor(sensor!.id, data),
    onSuccess: () => {
      onSuccess();
    },
    onError: (error: any) => {
      const detail = error.response?.data?.detail || error.message;
      setErrors({ submit: detail });
    },
  });

  // Validación
  const validate = (): boolean => {
    const newErrors: Record<string, string> = {};

    if (!formData.name.trim()) {
      newErrors.name = 'El nombre es requerido';
    }

    if (!formData.sensor_type) {
      newErrors.sensor_type = 'El tipo es requerido';
    }

    if (formData.calibration_factor !== undefined && formData.calibration_factor <= 0) {
      newErrors.calibration_factor = 'El factor de calibración debe ser mayor a 0';
    }

    if (
      formData.value_min != null &&
      formData.value_max != null &&
      formData.value_min >= formData.value_max
    ) {
      newErrors.value_max = 'El valor máximo debe ser mayor que el mínimo';
    }

    if (formData.gpio_pin != null && (formData.gpio_pin < 0 || formData.gpio_pin > 39)) {
      newErrors.gpio_pin = 'El GPIO debe estar entre 0 y 39';
    }

    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  };

  // Submit
  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();

    if (!validate()) {
      return;
    }

    // Limpiar campos vacíos
    const cleanData: any = { ...formData };
    if (!cleanData.description) cleanData.description = null;
    if (!cleanData.gpio_pin && cleanData.gpio_pin !== 0) cleanData.gpio_pin = null;
    if (!cleanData.protocol) cleanData.protocol = null;
    if (!cleanData.i2c_address) cleanData.i2c_address = null;
    if (!cleanData.value_min && cleanData.value_min !== 0) cleanData.value_min = null;
    if (!cleanData.value_max && cleanData.value_max !== 0) cleanData.value_max = null;
    if (!cleanData.unit) cleanData.unit = null;
    if (!cleanData.manufacturer) cleanData.manufacturer = null;
    if (!cleanData.model) cleanData.model = null;
    if (!cleanData.datasheet_url) cleanData.datasheet_url = null;

    if (isEditing) {
      await updateMutation.mutateAsync(cleanData);
    } else {
      await createMutation.mutateAsync(cleanData);
    }
  };

  const isLoading = createMutation.isPending || updateMutation.isPending;

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
      <div className="bg-white rounded-lg shadow-xl max-w-3xl w-full max-h-[90vh] overflow-y-auto">
        {/* Header */}
        <div className="sticky top-0 bg-white border-b px-6 py-4 flex justify-between items-center">
          <h2 className="text-2xl font-bold text-gray-900">
            {isEditing ? `Editar: ${sensor.name}` : 'Nuevo Sensor Personalizado'}
          </h2>
          <button
            onClick={onClose}
            className="text-gray-400 hover:text-gray-600 text-2xl"
            disabled={isLoading}
          >
            ×
          </button>
        </div>

        {/* Form */}
        <form onSubmit={handleSubmit} className="p-6 space-y-6">
          {/* Mensaje de error general */}
          {errors.submit && (
            <div className="bg-red-50 text-red-600 p-3 rounded-lg text-sm">{errors.submit}</div>
          )}

          {/* Warning para built-in */}
          {isBuiltin && (
            <div className="bg-yellow-50 text-yellow-800 p-3 rounded-lg text-sm">
              ⚠ Este es un sensor built-in. Solo puedes modificar ciertos campos.
            </div>
          )}

          {/* Información Básica */}
          <div className="space-y-4">
            <h3 className="text-lg font-semibold text-gray-900">Información Básica</h3>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              {/* Nombre */}
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Nombre *
                </label>
                <input
                  type="text"
                  value={formData.name}
                  onChange={(e) => setFormData({ ...formData, name: e.target.value })}
                  disabled={isBuiltin}
                  className={`w-full px-3 py-2 border rounded-lg focus:ring-2 focus:ring-purple-500 ${
                    errors.name ? 'border-red-500' : 'border-gray-300'
                  } ${isBuiltin ? 'bg-gray-100' : ''}`}
                  placeholder="ej: BME280_Presion"
                />
                {errors.name && <p className="text-red-500 text-xs mt-1">{errors.name}</p>}
              </div>

              {/* Tipo */}
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Tipo de Sensor *
                </label>
                <select
                  value={formData.sensor_type}
                  onChange={(e) => setFormData({ ...formData, sensor_type: e.target.value })}
                  disabled={isBuiltin}
                  className={`w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-purple-500 ${
                    isBuiltin ? 'bg-gray-100' : ''
                  }`}
                >
                  {sensorService.getSensorTypes().map((type) => (
                    <option key={type} value={type}>
                      {type}
                    </option>
                  ))}
                </select>
              </div>
            </div>

            {/* Descripción */}
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Descripción
              </label>
              <textarea
                value={formData.description || ''}
                onChange={(e) => setFormData({ ...formData, description: e.target.value })}
                rows={2}
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-purple-500"
                placeholder="Descripción opcional del sensor"
              />
            </div>
          </div>

          {/* Configuración de Hardware */}
          <div className="space-y-4">
            <h3 className="text-lg font-semibold text-gray-900">Configuración de Hardware</h3>

            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
              {/* Protocolo */}
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Protocolo
                </label>
                <select
                  value={formData.protocol || ''}
                  onChange={(e) => setFormData({ ...formData, protocol: e.target.value })}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-purple-500"
                >
                  <option value="">Ninguno</option>
                  {sensorService.getProtocols().map((protocol) => (
                    <option key={protocol} value={protocol}>
                      {protocol}
                    </option>
                  ))}
                </select>
              </div>

              {/* GPIO Pin */}
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  GPIO Pin (0-39)
                </label>
                <input
                  type="number"
                  min="0"
                  max="39"
                  value={formData.gpio_pin ?? ''}
                  onChange={(e) =>
                    setFormData({
                      ...formData,
                      gpio_pin: e.target.value ? parseInt(e.target.value) : null,
                    })
                  }
                  className={`w-full px-3 py-2 border rounded-lg focus:ring-2 focus:ring-purple-500 ${
                    errors.gpio_pin ? 'border-red-500' : 'border-gray-300'
                  }`}
                  placeholder="ej: 34"
                />
                {errors.gpio_pin && <p className="text-red-500 text-xs mt-1">{errors.gpio_pin}</p>}
              </div>

              {/* I2C Address */}
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Dirección I2C
                </label>
                <input
                  type="text"
                  value={formData.i2c_address || ''}
                  onChange={(e) => setFormData({ ...formData, i2c_address: e.target.value })}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-purple-500"
                  placeholder="ej: 0x76"
                />
              </div>
            </div>
          </div>

          {/* Calibración */}
          <div className="space-y-4">
            <h3 className="text-lg font-semibold text-gray-900">Calibración</h3>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              {/* Offset */}
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Offset
                </label>
                <input
                  type="number"
                  step="0.001"
                  value={formData.calibration_offset}
                  onChange={(e) =>
                    setFormData({
                      ...formData,
                      calibration_offset: parseFloat(e.target.value) || 0,
                    })
                  }
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-purple-500"
                />
              </div>

              {/* Factor */}
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Factor *
                </label>
                <input
                  type="number"
                  step="0.001"
                  value={formData.calibration_factor}
                  onChange={(e) =>
                    setFormData({
                      ...formData,
                      calibration_factor: parseFloat(e.target.value) || 1,
                    })
                  }
                  className={`w-full px-3 py-2 border rounded-lg focus:ring-2 focus:ring-purple-500 ${
                    errors.calibration_factor ? 'border-red-500' : 'border-gray-300'
                  }`}
                />
                {errors.calibration_factor && (
                  <p className="text-red-500 text-xs mt-1">{errors.calibration_factor}</p>
                )}
              </div>
            </div>
          </div>

          {/* Rango y Unidades */}
          <div className="space-y-4">
            <h3 className="text-lg font-semibold text-gray-900">Rango y Formato</h3>

            <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
              {/* Valor Mínimo */}
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Valor Mínimo
                </label>
                <input
                  type="number"
                  step="0.01"
                  value={formData.value_min ?? ''}
                  onChange={(e) =>
                    setFormData({
                      ...formData,
                      value_min: e.target.value ? parseFloat(e.target.value) : null,
                    })
                  }
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-purple-500"
                />
              </div>

              {/* Valor Máximo */}
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Valor Máximo
                </label>
                <input
                  type="number"
                  step="0.01"
                  value={formData.value_max ?? ''}
                  onChange={(e) =>
                    setFormData({
                      ...formData,
                      value_max: e.target.value ? parseFloat(e.target.value) : null,
                    })
                  }
                  className={`w-full px-3 py-2 border rounded-lg focus:ring-2 focus:ring-purple-500 ${
                    errors.value_max ? 'border-red-500' : 'border-gray-300'
                  }`}
                />
                {errors.value_max && <p className="text-red-500 text-xs mt-1">{errors.value_max}</p>}
              </div>

              {/* Unidad */}
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Unidad
                </label>
                <input
                  type="text"
                  value={formData.unit || ''}
                  onChange={(e) => setFormData({ ...formData, unit: e.target.value })}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-purple-500"
                  placeholder="ej: °C, %, kPa"
                  list="common-units"
                />
                <datalist id="common-units">
                  {sensorService.getCommonUnits(formData.sensor_type).map((unit) => (
                    <option key={unit} value={unit} />
                  ))}
                </datalist>
              </div>

              {/* Decimales */}
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Decimales
                </label>
                <input
                  type="number"
                  min="0"
                  max="6"
                  value={formData.decimal_places}
                  onChange={(e) =>
                    setFormData({
                      ...formData,
                      decimal_places: parseInt(e.target.value) || 2,
                    })
                  }
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-purple-500"
                />
              </div>
            </div>
          </div>

          {/* Metadatos */}
          <div className="space-y-4">
            <h3 className="text-lg font-semibold text-gray-900">Metadatos (Opcional)</h3>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              {/* Fabricante */}
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Fabricante
                </label>
                <input
                  type="text"
                  value={formData.manufacturer || ''}
                  onChange={(e) => setFormData({ ...formData, manufacturer: e.target.value })}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-purple-500"
                  placeholder="ej: Bosch"
                />
              </div>

              {/* Modelo */}
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Modelo
                </label>
                <input
                  type="text"
                  value={formData.model || ''}
                  onChange={(e) => setFormData({ ...formData, model: e.target.value })}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-purple-500"
                  placeholder="ej: BME280"
                />
              </div>
            </div>

            {/* Datasheet URL */}
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                URL del Datasheet
              </label>
              <input
                type="url"
                value={formData.datasheet_url || ''}
                onChange={(e) => setFormData({ ...formData, datasheet_url: e.target.value })}
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-purple-500"
                placeholder="https://..."
              />
            </div>
          </div>

          {/* Estado Activo */}
          <div>
            <label className="flex items-center">
              <input
                type="checkbox"
                checked={formData.is_active}
                onChange={(e) => setFormData({ ...formData, is_active: e.target.checked })}
                className="mr-2 h-4 w-4 text-purple-600 focus:ring-purple-500 border-gray-300 rounded"
              />
              <span className="text-sm font-medium text-gray-700">Sensor activo</span>
            </label>
          </div>

          {/* Botones */}
          <div className="flex justify-end gap-3 pt-4 border-t">
            <button
              type="button"
              onClick={onClose}
              disabled={isLoading}
              className="px-6 py-2 border border-gray-300 rounded-lg text-gray-700 hover:bg-gray-50 font-medium disabled:opacity-50"
            >
              Cancelar
            </button>
            <button
              type="submit"
              disabled={isLoading}
              className="px-6 py-2 bg-purple-600 text-white rounded-lg hover:bg-purple-700 font-medium disabled:opacity-50"
            >
              {isLoading ? 'Guardando...' : isEditing ? 'Actualizar' : 'Crear Sensor'}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}
