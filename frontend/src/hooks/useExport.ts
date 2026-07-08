/**
 * Hook personalizado para exportar datos a CSV.
 */

import { SensorReading, Device } from '@/types';

export const useExport = () => {
  /**
   * Convierte readings a formato CSV
   */
  const prepareReadingsForExport = (
    readings: SensorReading[],
    device?: Device
  ): any[] => {
    return readings.map((reading) => {
      // Extraer todas las claves del data_payload
      const payload = reading.data_payload || {};

      // Crear un objeto plano con todos los datos
      const row: any = {
        id: reading.id,
        device_id: reading.device_id,
        device_name: device?.name || `Device ${reading.device_id}`,
        timestamp: new Date(reading.timestamp).toLocaleString('es-AR'),
        quality_score: reading.quality_score?.toFixed(3) || 'N/A',
        processed: reading.processed ? 'Sí' : 'No',
      };

      // Agregar todas las variables del payload
      Object.keys(payload).forEach((key) => {
        const value = payload[key];
        // Formatear números con 2 decimales
        if (typeof value === 'number') {
          row[key] = value.toFixed(2);
        } else {
          row[key] = value;
        }
      });

      return row;
    });
  };

  /**
   * Genera headers dinámicos basados en los readings
   */
  const generateHeaders = (readings: SensorReading[]): string[] => {
    if (readings.length === 0) return [];

    const baseHeaders = ['id', 'device_id', 'device_name', 'timestamp', 'quality_score', 'processed'];

    // Extraer todas las claves únicas del data_payload
    const payloadKeys = new Set<string>();
    readings.forEach((reading) => {
      if (reading.data_payload) {
        Object.keys(reading.data_payload).forEach((key) => payloadKeys.add(key));
      }
    });

    return [...baseHeaders, ...Array.from(payloadKeys)];
  };

  /**
   * Genera nombre de archivo con timestamp
   */
  const generateFilename = (prefix: string = 'export'): string => {
    const now = new Date();
    const timestamp = now.toISOString().replace(/[:.]/g, '-').slice(0, 19);
    return `${prefix}_${timestamp}.csv`;
  };

  return {
    prepareReadingsForExport,
    generateHeaders,
    generateFilename,
  };
};

export default useExport;
