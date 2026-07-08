/**
 * Sensor Catalog Service - Cliente API para gestión del catálogo de sensores
 *
 * Métodos disponibles:
 * - getSensors: Listar sensores del catálogo (con filtros)
 * - getSensor: Obtener un sensor específico
 * - createSensor: Crear nuevo sensor personalizado
 * - updateSensor: Actualizar sensor existente
 * - deleteSensor: Eliminar sensor (solo super_admin, no built-in)
 * - activateSensor: Activar sensor desactivado
 * - deactivateSensor: Desactivar sensor (soft delete)
 * - getSensorStats: Obtener estadísticas del catálogo
 */

import api from './api';
import { SensorCatalog, SensorCatalogCreate, SensorCatalogUpdate } from '../types';

/**
 * Parámetros para filtrar sensores
 */
export interface GetSensorsParams {
  sensor_type?: string;
  protocol?: string;
  is_active?: boolean;
  include_builtin?: boolean;
  search?: string;
  skip?: number;
  limit?: number;
}

/**
 * Estadísticas del catálogo de sensores
 */
export interface SensorCatalogStats {
  total: number;
  active: number;
  inactive: number;
  builtin: number;
  custom: number;
  by_type: Record<string, number>;
  by_protocol: Record<string, number>;
}

const sensorService = {
  /**
   * Listar sensores del catálogo
   *
   * @param params - Parámetros de filtrado
   * @returns Array de sensores
   */
  async getSensors(params?: GetSensorsParams): Promise<SensorCatalog[]> {
    const queryParams = new URLSearchParams();

    if (params?.sensor_type) {
      queryParams.append('sensor_type', params.sensor_type);
    }
    if (params?.protocol) {
      queryParams.append('protocol', params.protocol);
    }
    if (params?.is_active !== undefined) {
      queryParams.append('is_active', params.is_active.toString());
    }
    if (params?.include_builtin !== undefined) {
      queryParams.append('include_builtin', params.include_builtin.toString());
    }
    if (params?.search) {
      queryParams.append('search', params.search);
    }
    if (params?.skip !== undefined) {
      queryParams.append('skip', params.skip.toString());
    }
    if (params?.limit !== undefined) {
      queryParams.append('limit', params.limit.toString());
    }

    const queryString = queryParams.toString();
    const url = queryString ? `/sensors?${queryString}` : '/sensors';

    const response = await api.get<SensorCatalog[]>(url);
    return response.data;
  },

  /**
   * Obtener un sensor específico
   *
   * @param sensorId - ID del sensor
   * @returns Sensor
   */
  async getSensor(sensorId: number): Promise<SensorCatalog> {
    const response = await api.get<SensorCatalog>(`/sensors/${sensorId}`);
    return response.data;
  },

  /**
   * Crear nuevo sensor personalizado
   *
   * @param sensorData - Datos del nuevo sensor
   * @returns Sensor creado
   */
  async createSensor(sensorData: SensorCatalogCreate): Promise<SensorCatalog> {
    const response = await api.post<SensorCatalog>('/sensors', sensorData);
    return response.data;
  },

  /**
   * Actualizar sensor existente
   *
   * @param sensorId - ID del sensor
   * @param sensorData - Datos a actualizar
   * @returns Sensor actualizado
   */
  async updateSensor(sensorId: number, sensorData: SensorCatalogUpdate): Promise<SensorCatalog> {
    const response = await api.patch<SensorCatalog>(`/sensors/${sensorId}`, sensorData);
    return response.data;
  },

  /**
   * Eliminar sensor (solo super_admin, no puede eliminar built-in)
   *
   * @param sensorId - ID del sensor
   */
  async deleteSensor(sensorId: number): Promise<void> {
    await api.delete(`/sensors/${sensorId}`);
  },

  /**
   * Activar sensor desactivado
   *
   * @param sensorId - ID del sensor
   * @returns Sensor activado
   */
  async activateSensor(sensorId: number): Promise<SensorCatalog> {
    const response = await api.patch<SensorCatalog>(`/sensors/${sensorId}/activate`);
    return response.data;
  },

  /**
   * Desactivar sensor (soft delete)
   *
   * @param sensorId - ID del sensor
   * @returns Sensor desactivado
   */
  async deactivateSensor(sensorId: number): Promise<SensorCatalog> {
    const response = await api.patch<SensorCatalog>(`/sensors/${sensorId}/deactivate`);
    return response.data;
  },

  /**
   * Obtener estadísticas del catálogo de sensores
   *
   * @returns Estadísticas del catálogo
   */
  async getSensorStats(): Promise<SensorCatalogStats> {
    const response = await api.get<SensorCatalogStats>('/sensors/stats');
    return response.data;
  },

  /**
   * Obtener tipos de sensores disponibles (constantes)
   */
  getSensorTypes(): string[] {
    return ['temperature', 'humidity', 'pressure', 'analog', 'digital', 'custom'];
  },

  /**
   * Obtener protocolos disponibles (constantes)
   */
  getProtocols(): string[] {
    return ['OneWire', 'I2C', 'SPI', 'ADC', 'Digital', 'UART', 'Modbus'];
  },

  /**
   * Obtener unidades comunes por tipo de sensor
   */
  getCommonUnits(sensorType: string): string[] {
    const unitMap: Record<string, string[]> = {
      temperature: ['°C', '°F', 'K'],
      humidity: ['%', '%RH'],
      pressure: ['kPa', 'bar', 'PSI', 'Pa', 'mmHg'],
      analog: ['V', 'mV', 'mA', 'raw'],
      digital: ['on/off', '0/1', 'true/false'],
      custom: ['custom'],
    };

    return unitMap[sensorType] || [''];
  },
};

export default sensorService;
