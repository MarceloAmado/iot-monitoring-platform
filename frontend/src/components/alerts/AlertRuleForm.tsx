import { useState } from 'react';
import { useMutation, useQuery } from '@tanstack/react-query';
import {
  createAlertRule,
  updateAlertRule,
  type AlertRule,
  type AlertRuleCreate,
  type AlertRuleUpdate,
} from '../../services/alertService';
import deviceService from '../../services/deviceService';

interface AlertRuleFormProps {
  rule?: AlertRule | null;
  onClose: () => void;
  onSuccess: () => void;
}

export default function AlertRuleForm({ rule, onClose, onSuccess }: AlertRuleFormProps) {
  const isEditing = !!rule;

  // Form state
  const [formData, setFormData] = useState({
    name: rule?.name || '',
    check_type: rule?.check_type || 'THRESHOLD_ABOVE',
    variable_key: rule?.variable_key || 'temp_c',
    threshold_value: rule?.threshold_value?.toString() || '',
    threshold_min: rule?.threshold_min?.toString() || '',
    threshold_max: rule?.threshold_max?.toString() || '',
    time_window_minutes: rule?.time_window_minutes?.toString() || '5',
    enabled: rule?.enabled ?? true,
    cooldown_minutes: rule?.cooldown_minutes?.toString() || '30',
    notification_channels: rule?.notification_channels || ['email'],
    webhook_url: rule?.webhook_url || '',
    device_id: rule?.device_id?.toString() || '',
  });

  const [errors, setErrors] = useState<Record<string, string>>({});

  // Query devices for selector
  const { data: devices } = useQuery({
    queryKey: ['devices'],
    queryFn: () => deviceService.getDevices(),
  });

  // Mutation
  const mutation = useMutation({
    mutationFn: async (data: AlertRuleCreate | AlertRuleUpdate) => {
      if (isEditing && rule) {
        return updateAlertRule(rule.id, data as AlertRuleUpdate);
      }
      return createAlertRule(data as AlertRuleCreate);
    },
    onSuccess: () => {
      onSuccess();
    },
    onError: (error: any) => {
      const detail = error.response?.data?.detail;
      if (typeof detail === 'string') {
        setErrors({ general: detail });
      } else if (Array.isArray(detail)) {
        const newErrors: Record<string, string> = {};
        detail.forEach((err: any) => {
          newErrors[err.loc[err.loc.length - 1]] = err.msg;
        });
        setErrors(newErrors);
      }
    },
  });

  const handleChange = (
    e: React.ChangeEvent<HTMLInputElement | HTMLSelectElement | HTMLTextAreaElement>
  ) => {
    const { name, value, type } = e.target;

    if (type === 'checkbox') {
      const checked = (e.target as HTMLInputElement).checked;
      setFormData((prev) => ({ ...prev, [name]: checked }));
    } else {
      setFormData((prev) => ({ ...prev, [name]: value }));
    }

    // Clear error for this field
    setErrors((prev) => {
      const newErrors = { ...prev };
      delete newErrors[name];
      return newErrors;
    });
  };

  const handleChannelToggle = (channel: string) => {
    setFormData((prev) => {
      const channels = prev.notification_channels.includes(channel)
        ? prev.notification_channels.filter((c) => c !== channel)
        : [...prev.notification_channels, channel];
      return { ...prev, notification_channels: channels };
    });
  };

  const validate = (): boolean => {
    const newErrors: Record<string, string> = {};

    if (!formData.name.trim()) {
      newErrors.name = 'El nombre es requerido';
    }

    if (!formData.variable_key.trim()) {
      newErrors.variable_key = 'La variable es requerida';
    }

    if (
      ['THRESHOLD_ABOVE', 'THRESHOLD_BELOW'].includes(formData.check_type) &&
      !formData.threshold_value
    ) {
      newErrors.threshold_value = 'El valor umbral es requerido';
    }

    if (formData.check_type === 'THRESHOLD_RANGE') {
      if (!formData.threshold_min) {
        newErrors.threshold_min = 'El valor mínimo es requerido';
      }
      if (!formData.threshold_max) {
        newErrors.threshold_max = 'El valor máximo es requerido';
      }
      if (
        formData.threshold_min &&
        formData.threshold_max &&
        parseFloat(formData.threshold_min) >= parseFloat(formData.threshold_max)
      ) {
        newErrors.threshold_min = 'El mínimo debe ser menor que el máximo';
      }
    }

    if (
      ['RATE_OF_CHANGE', 'DEVICE_OFFLINE'].includes(formData.check_type) &&
      !formData.time_window_minutes
    ) {
      newErrors.time_window_minutes = 'La ventana de tiempo es requerida';
    }

    if (formData.notification_channels.length === 0) {
      newErrors.notification_channels = 'Debe seleccionar al menos un canal';
    }

    if (formData.notification_channels.includes('webhook') && !formData.webhook_url.trim()) {
      newErrors.webhook_url = 'La URL del webhook es requerida';
    }

    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  };

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();

    if (!validate()) {
      return;
    }

    const payload: any = {
      name: formData.name,
      check_type: formData.check_type,
      variable_key: formData.variable_key,
      enabled: formData.enabled,
      cooldown_minutes: parseInt(formData.cooldown_minutes),
      notification_channels: formData.notification_channels,
      device_id: formData.device_id ? parseInt(formData.device_id) : null,
    };

    if (['THRESHOLD_ABOVE', 'THRESHOLD_BELOW'].includes(formData.check_type)) {
      payload.threshold_value = parseFloat(formData.threshold_value);
    }

    if (formData.check_type === 'THRESHOLD_RANGE') {
      payload.threshold_min = parseFloat(formData.threshold_min);
      payload.threshold_max = parseFloat(formData.threshold_max);
    }

    if (['RATE_OF_CHANGE', 'DEVICE_OFFLINE'].includes(formData.check_type)) {
      payload.time_window_minutes = parseInt(formData.time_window_minutes);
    }

    if (formData.notification_channels.includes('webhook')) {
      payload.webhook_url = formData.webhook_url;
    }

    mutation.mutate(payload);
  };

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center p-4 z-50">
      <div className="bg-white rounded-lg shadow-xl max-w-2xl w-full max-h-[90vh] overflow-y-auto">
        <div className="p-6">
          <div className="flex justify-between items-center mb-6">
            <h2 className="text-2xl font-bold text-gray-900">
              {isEditing ? 'Editar Regla de Alerta' : 'Nueva Regla de Alerta'}
            </h2>
            <button
              onClick={onClose}
              className="text-gray-400 hover:text-gray-600 text-2xl leading-none"
            >
              ×
            </button>
          </div>

          {errors.general && (
            <div className="mb-4 p-3 bg-red-100 border border-red-400 text-red-700 rounded">
              {errors.general}
            </div>
          )}

          <form onSubmit={handleSubmit} className="space-y-4">
            {/* Nombre */}
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Nombre de la regla *
              </label>
              <input
                type="text"
                name="name"
                value={formData.name}
                onChange={handleChange}
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                placeholder="Ej: Temperatura alta en heladera"
              />
              {errors.name && <p className="mt-1 text-sm text-red-600">{errors.name}</p>}
            </div>

            {/* Device selector */}
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Device (opcional)
              </label>
              <select
                name="device_id"
                value={formData.device_id}
                onChange={handleChange}
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
              >
                <option value="">Todos los devices</option>
                {devices?.map((device) => (
                  <option key={device.id} value={device.id}>
                    {device.name} ({device.device_eui})
                  </option>
                ))}
              </select>
            </div>

            {/* Tipo de chequeo */}
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Tipo de chequeo *
              </label>
              <select
                name="check_type"
                value={formData.check_type}
                onChange={handleChange}
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
              >
                <option value="THRESHOLD_ABOVE">Supera umbral (mayor que)</option>
                <option value="THRESHOLD_BELOW">Bajo umbral (menor que)</option>
                <option value="THRESHOLD_RANGE">Fuera de rango</option>
                <option value="RATE_OF_CHANGE">Cambio rápido</option>
                <option value="DEVICE_OFFLINE">Device offline</option>
                <option value="SENSOR_FAULT">Sensor roto</option>
              </select>
            </div>

            {/* Variable */}
            {formData.check_type !== 'DEVICE_OFFLINE' && (
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Variable a monitorear *
                </label>
                <input
                  type="text"
                  name="variable_key"
                  value={formData.variable_key}
                  onChange={handleChange}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                  placeholder="Ej: temp_c, humidity_pct"
                />
                {errors.variable_key && (
                  <p className="mt-1 text-sm text-red-600">{errors.variable_key}</p>
                )}
              </div>
            )}

            {/* Threshold value */}
            {['THRESHOLD_ABOVE', 'THRESHOLD_BELOW'].includes(formData.check_type) && (
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Valor umbral *
                </label>
                <input
                  type="number"
                  step="any"
                  name="threshold_value"
                  value={formData.threshold_value}
                  onChange={handleChange}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                  placeholder="Ej: 25.5"
                />
                {errors.threshold_value && (
                  <p className="mt-1 text-sm text-red-600">{errors.threshold_value}</p>
                )}
              </div>
            )}

            {/* Threshold range */}
            {formData.check_type === 'THRESHOLD_RANGE' && (
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Valor mínimo *
                  </label>
                  <input
                    type="number"
                    step="any"
                    name="threshold_min"
                    value={formData.threshold_min}
                    onChange={handleChange}
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                    placeholder="Ej: 18"
                  />
                  {errors.threshold_min && (
                    <p className="mt-1 text-sm text-red-600">{errors.threshold_min}</p>
                  )}
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Valor máximo *
                  </label>
                  <input
                    type="number"
                    step="any"
                    name="threshold_max"
                    value={formData.threshold_max}
                    onChange={handleChange}
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                    placeholder="Ej: 24"
                  />
                  {errors.threshold_max && (
                    <p className="mt-1 text-sm text-red-600">{errors.threshold_max}</p>
                  )}
                </div>
              </div>
            )}

            {/* Time window */}
            {['RATE_OF_CHANGE', 'DEVICE_OFFLINE'].includes(formData.check_type) && (
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Ventana de tiempo (minutos) *
                </label>
                <input
                  type="number"
                  name="time_window_minutes"
                  value={formData.time_window_minutes}
                  onChange={handleChange}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                  placeholder="Ej: 5"
                />
                {errors.time_window_minutes && (
                  <p className="mt-1 text-sm text-red-600">{errors.time_window_minutes}</p>
                )}
              </div>
            )}

            {/* Cooldown */}
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Cooldown (minutos) *
              </label>
              <input
                type="number"
                name="cooldown_minutes"
                value={formData.cooldown_minutes}
                onChange={handleChange}
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                placeholder="Ej: 30"
              />
              <p className="mt-1 text-xs text-gray-500">
                Tiempo mínimo entre alertas consecutivas
              </p>
            </div>

            {/* Notification channels */}
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Canales de notificación *
              </label>
              <div className="space-y-2">
                <label className="flex items-center">
                  <input
                    type="checkbox"
                    checked={formData.notification_channels.includes('email')}
                    onChange={() => handleChannelToggle('email')}
                    className="mr-2"
                  />
                  <span className="text-sm">Email</span>
                </label>
                <label className="flex items-center">
                  <input
                    type="checkbox"
                    checked={formData.notification_channels.includes('telegram')}
                    onChange={() => handleChannelToggle('telegram')}
                    className="mr-2"
                  />
                  <span className="text-sm">Telegram</span>
                </label>
                <label className="flex items-center">
                  <input
                    type="checkbox"
                    checked={formData.notification_channels.includes('webhook')}
                    onChange={() => handleChannelToggle('webhook')}
                    className="mr-2"
                  />
                  <span className="text-sm">Webhook</span>
                </label>
              </div>
              {errors.notification_channels && (
                <p className="mt-1 text-sm text-red-600">{errors.notification_channels}</p>
              )}
            </div>

            {/* Webhook URL */}
            {formData.notification_channels.includes('webhook') && (
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  URL del Webhook *
                </label>
                <input
                  type="url"
                  name="webhook_url"
                  value={formData.webhook_url}
                  onChange={handleChange}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                  placeholder="https://example.com/webhook"
                />
                {errors.webhook_url && (
                  <p className="mt-1 text-sm text-red-600">{errors.webhook_url}</p>
                )}
              </div>
            )}

            {/* Enabled toggle */}
            <div>
              <label className="flex items-center">
                <input
                  type="checkbox"
                  name="enabled"
                  checked={formData.enabled}
                  onChange={handleChange}
                  className="mr-2"
                />
                <span className="text-sm font-medium text-gray-700">Regla activa</span>
              </label>
            </div>

            {/* Buttons */}
            <div className="flex justify-end space-x-3 pt-4 border-t">
              <button
                type="button"
                onClick={onClose}
                className="px-4 py-2 border border-gray-300 rounded-lg text-gray-700 hover:bg-gray-50 transition"
              >
                Cancelar
              </button>
              <button
                type="submit"
                disabled={mutation.isPending}
                className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition disabled:bg-gray-400"
              >
                {mutation.isPending
                  ? 'Guardando...'
                  : isEditing
                  ? 'Actualizar Regla'
                  : 'Crear Regla'}
              </button>
            </div>
          </form>
        </div>
      </div>
    </div>
  );
}
