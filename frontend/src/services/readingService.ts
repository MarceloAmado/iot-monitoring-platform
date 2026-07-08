/**
 * Servicio para manejo de sensor readings.
 */

import api from './api';
import type { SensorReading } from '@/types';

export interface GetReadingsParams {
  device_id?: number;
  date_from?: string;
  date_to?: string;
  skip?: number;
  limit?: number;
}

export const readingService = {
  /**
   * Obtener lista de readings con filtros
   */
  async getReadings(params?: GetReadingsParams): Promise<SensorReading[]> {
    const response = await api.get<SensorReading[]>('/readings', { params });
    return response.data;
  },

  /**
   * Obtener readings de un device específico en un rango de tiempo
   */
  async getDeviceReadings(
    deviceId: number,
    timeRange: '24h' | '7d' | '30d'
  ): Promise<SensorReading[]> {
    const now = new Date();
    const dateFrom = new Date();

    switch (timeRange) {
      case '24h':
        dateFrom.setHours(now.getHours() - 24);
        break;
      case '7d':
        dateFrom.setDate(now.getDate() - 7);
        break;
      case '30d':
        dateFrom.setDate(now.getDate() - 30);
        break;
    }

    return this.getReadings({
      device_id: deviceId,
      date_from: dateFrom.toISOString(),
      date_to: now.toISOString(),
    });
  },

  /**
   * Obtener un reading por ID
   */
  async getReading(readingId: number): Promise<SensorReading> {
    const response = await api.get<SensorReading>(`/readings/${readingId}`);
    return response.data;
  },
};

export default readingService;
