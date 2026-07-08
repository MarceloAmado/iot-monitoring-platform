/**
 * DeviceFormModal - Modal para crear/editar dispositivos
 *
 * Formulario completo con validación para agregar nuevos dispositivos
 * o editar dispositivos existentes.
 */

import React, { useState, useEffect } from 'react';
import { useMutation, useQueryClient } from '@tanstack/react-query';
import { IMModal, IMInput, IMButton } from '@/components/common';
import deviceService from '@/services/deviceService';
import type { Device } from '@/types';

// ========================================
// HELPER: GENERADOR DE DEVICE EUI
// ========================================

/**
 * Genera un Device EUI único basado en timestamp + random
 * Formato: ESP32_YYYYMMDD_HHMM_XXXX
 *
 * Ejemplo: ESP32_20251023_1430_A7B3
 */
const generateDeviceEUI = (): string => {
  const now = new Date();

  // Fecha: YYYYMMDD
  const year = now.getFullYear();
  const month = String(now.getMonth() + 1).padStart(2, '0');
  const day = String(now.getDate()).padStart(2, '0');
  const datePart = `${year}${month}${day}`;

  // Hora: HHMM
  const hours = String(now.getHours()).padStart(2, '0');
  const minutes = String(now.getMinutes()).padStart(2, '0');
  const timePart = `${hours}${minutes}`;

  // Random: 4 caracteres hexadecimales
  const randomPart = Math.random().toString(16).substring(2, 6).toUpperCase();

  return `ESP32_${datePart}_${timePart}_${randomPart}`;
};

// ========================================
// TYPES
// ========================================

interface DeviceFormModalProps {
  /**
   * Estado de apertura del modal
   */
  isOpen: boolean;

  /**
   * Callback al cerrar el modal
   */
  onClose: () => void;

  /**
   * Device a editar (si es null, crea uno nuevo)
   */
  device?: Device | null;

  /**
   * Callback opcional después de guardar exitosamente
   */
  onSuccess?: () => void;
}

interface DeviceFormData {
  device_eui: string;
  name: string;
  status: 'active' | 'inactive' | 'maintenance' | 'error';
  firmware_version: string;
  asset_id: string; // Usar string para el formulario (vacío = null)
}

// ========================================
// COMPONENT
// ========================================

export const DeviceFormModal: React.FC<DeviceFormModalProps> = ({
  isOpen,
  onClose,
  device,
  onSuccess,
}) => {
  const queryClient = useQueryClient();
  const isEditMode = !!device;

  // ========================================
  // STATE
  // ========================================

  const [formData, setFormData] = useState<DeviceFormData>({
    device_eui: '',
    name: '',
    status: 'active',
    firmware_version: '',
    asset_id: '',
  });

  const [errors, setErrors] = useState<Partial<Record<keyof DeviceFormData, string>>>({});

  // ========================================
  // EFFECTS
  // ========================================

  // Cargar datos del device si es modo edición
  useEffect(() => {
    if (isOpen && device) {
      setFormData({
        device_eui: device.device_eui,
        name: device.name,
        status: device.status,
        firmware_version: device.firmware_version || '',
        asset_id: device.asset_id?.toString() || '',
      });
      setErrors({});
    } else if (isOpen && !device) {
      // Reset form para nuevo device
      setFormData({
        device_eui: '',
        name: '',
        status: 'active',
        firmware_version: '',
        asset_id: '',
      });
      setErrors({});
    }
  }, [isOpen, device]);

  // ========================================
  // MUTATIONS
  // ========================================

  const createMutation = useMutation({
    mutationFn: (data: Partial<Device>) => deviceService.createDevice(data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['devices'] });
      onSuccess?.();
      onClose();
    },
    onError: (error: any) => {
      console.error('Error creando device:', error);

      // Manejo de error de Device EUI duplicado
      if (error?.response?.status === 400 && error?.response?.data?.detail) {
        const detail = error.response.data.detail;
        if (detail.includes('ya existe')) {
          setErrors((prev) => ({
            ...prev,
            device_eui: 'Este Device EUI ya está registrado. Por favor genera uno nuevo.',
          }));
          return;
        }
      }

      // Error genérico
      alert('Error al crear el dispositivo. Por favor intenta nuevamente.');
    },
  });

  const updateMutation = useMutation({
    mutationFn: ({ id, data }: { id: number; data: Partial<Device> }) =>
      deviceService.updateDevice(id, data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['devices'] });
      queryClient.invalidateQueries({ queryKey: ['device', device?.id] });
      onSuccess?.();
      onClose();
    },
    onError: (error: any) => {
      console.error('Error actualizando device:', error);
      alert('Error al actualizar el dispositivo. Por favor intenta nuevamente.');
    },
  });

  // ========================================
  // HANDLERS
  // ========================================

  const handleChange = (
    e: React.ChangeEvent<HTMLInputElement | HTMLSelectElement>
  ) => {
    const { name, value } = e.target;
    setFormData((prev) => ({
      ...prev,
      [name]: value,
    }));

    // Limpiar error del campo al escribir
    if (errors[name as keyof DeviceFormData]) {
      setErrors((prev) => ({
        ...prev,
        [name]: undefined,
      }));
    }
  };

  const validate = (): boolean => {
    const newErrors: Partial<Record<keyof DeviceFormData, string>> = {};

    // Device EUI (requerido, único)
    if (!formData.device_eui.trim()) {
      newErrors.device_eui = 'El Device EUI es requerido';
    } else if (formData.device_eui.length > 64) {
      newErrors.device_eui = 'El Device EUI no puede exceder 64 caracteres';
    }

    // Name (requerido)
    if (!formData.name.trim()) {
      newErrors.name = 'El nombre es requerido';
    } else if (formData.name.length > 128) {
      newErrors.name = 'El nombre no puede exceder 128 caracteres';
    }

    // Firmware version (opcional pero con límite)
    if (formData.firmware_version && formData.firmware_version.length > 20) {
      newErrors.firmware_version = 'La versión no puede exceder 20 caracteres';
    }

    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();

    if (!validate()) {
      return;
    }

    // Preparar datos para envío
    const submitData: Partial<Device> = {
      device_eui: formData.device_eui.trim(),
      name: formData.name.trim(),
      status: formData.status,
      firmware_version: formData.firmware_version.trim() || null,
      asset_id: formData.asset_id ? parseInt(formData.asset_id, 10) : null,
    };

    if (isEditMode && device) {
      updateMutation.mutate({ id: device.id, data: submitData });
    } else {
      createMutation.mutate(submitData);
    }
  };

  const handleCancel = () => {
    if (createMutation.isPending || updateMutation.isPending) {
      return; // No permitir cerrar mientras se guarda
    }
    onClose();
  };

  const handleGenerateEUI = () => {
    const newEUI = generateDeviceEUI();
    setFormData((prev) => ({
      ...prev,
      device_eui: newEUI,
    }));

    // Limpiar error si existía
    if (errors.device_eui) {
      setErrors((prev) => ({
        ...prev,
        device_eui: undefined,
      }));
    }
  };

  // ========================================
  // RENDER
  // ========================================

  const isLoading = createMutation.isPending || updateMutation.isPending;

  return (
    <IMModal
      isOpen={isOpen}
      onClose={handleCancel}
      title={isEditMode ? 'Editar Dispositivo' : 'Nuevo Dispositivo'}
      subtitle={
        isEditMode
          ? 'Actualiza la información del dispositivo'
          : 'Completa los datos para registrar un nuevo dispositivo IoT'
      }
      size="md"
      footer={
        <>
          <IMButton
            variant="secondary"
            onClick={handleCancel}
            disabled={isLoading}
          >
            Cancelar
          </IMButton>
          <IMButton
            variant="primary"
            onClick={handleSubmit}
            loading={isLoading}
          >
            {isEditMode ? 'Guardar Cambios' : 'Crear Dispositivo'}
          </IMButton>
        </>
      }
    >
      <form onSubmit={handleSubmit} className="space-y-4">
        {/* Device EUI con botón de generación automática */}
        <div>
          <label className="im-label">
            Device EUI
            <span className="text-im-danger ml-1">*</span>
          </label>

          <div className="flex gap-2 mt-1">
            <div className="flex-1">
              <IMInput
                name="device_eui"
                value={formData.device_eui}
                onChange={handleChange}
                placeholder="ESP32_20251023_1430_A7B3"
                error={errors.device_eui}
                required
                disabled={isEditMode} // No permitir cambiar EUI en modo edición
                maxLength={64}
                containerClassName="mb-0"
              />
            </div>

            {!isEditMode && (
              <IMButton
                type="button"
                variant="secondary"
                onClick={handleGenerateEUI}
                className="flex-shrink-0"
              >
                <svg
                  className="w-5 h-5"
                  fill="none"
                  viewBox="0 0 24 24"
                  stroke="currentColor"
                >
                  <path
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    strokeWidth={2}
                    d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15"
                  />
                </svg>
                <span className="ml-2">Generar</span>
              </IMButton>
            )}
          </div>

          {!errors.device_eui && (
            <p className="im-helper-text">
              {isEditMode
                ? 'El Device EUI no puede modificarse una vez creado'
                : 'Click en "Generar" para crear un EUI único automáticamente (formato: ESP32_YYYYMMDD_HHMM_XXXX)'}
            </p>
          )}
        </div>

        {/* Name */}
        <IMInput
          label="Nombre"
          name="name"
          value={formData.name}
          onChange={handleChange}
          placeholder="Sensor de Temperatura - Laboratorio"
          error={errors.name}
          helperText="Nombre descriptivo del dispositivo"
          required
          maxLength={128}
        />

        {/* Status */}
        <IMInput
          variant="select"
          label="Estado"
          name="status"
          value={formData.status}
          onChange={handleChange}
          error={errors.status}
          options={[
            { value: 'active', label: 'Activo' },
            { value: 'inactive', label: 'Inactivo' },
            { value: 'maintenance', label: 'Mantenimiento' },
            { value: 'error', label: 'Error' },
          ]}
          required
        />

        {/* Firmware Version */}
        <IMInput
          label="Versión de Firmware"
          name="firmware_version"
          value={formData.firmware_version}
          onChange={handleChange}
          placeholder="v1.0.0"
          error={errors.firmware_version}
          helperText="Versión del firmware instalado (opcional)"
          maxLength={20}
        />

        {/* Asset ID */}
        <IMInput
          label="ID de Asset"
          name="asset_id"
          type="number"
          value={formData.asset_id}
          onChange={handleChange}
          placeholder="1"
          error={errors.asset_id}
          helperText="ID del asset físico al que está asignado (opcional)"
          min={1}
        />

        {/* Info adicional */}
        <div className="bg-im-blue/5 border border-im-blue/20 rounded-md p-4 mt-4">
          <div className="flex items-start gap-3">
            <svg
              className="w-5 h-5 text-im-blue flex-shrink-0 mt-0.5"
              fill="currentColor"
              viewBox="0 0 20 20"
            >
              <path
                fillRule="evenodd"
                d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-7-4a1 1 0 11-2 0 1 1 0 012 0zM9 9a1 1 0 000 2v3a1 1 0 001 1h1a1 1 0 100-2v-3a1 1 0 00-1-1H9z"
                clipRule="evenodd"
              />
            </svg>
            <div className="text-sm text-im-neutral-700">
              <p className="font-semibold text-im-blue mb-1">
                Configuración del dispositivo ESP32
              </p>
              <p>
                Una vez creado, configura el ESP32 con el Zero-Config WiFi
                usando el Device EUI ingresado. El device comenzará a enviar
                datos automáticamente.
              </p>
            </div>
          </div>
        </div>
      </form>
    </IMModal>
  );
};

export default DeviceFormModal;
