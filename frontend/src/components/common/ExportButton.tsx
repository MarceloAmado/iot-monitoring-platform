/**
 * Componente para botón de exportación a CSV.
 */

import { CSVLink } from 'react-csv';
import { SensorReading, Device } from '@/types';
import { useExport } from '@/hooks/useExport';

interface ExportButtonProps {
  data: SensorReading[];
  device?: Device;
  filename?: string;
  className?: string;
}

export const ExportButton = ({
  data,
  device,
  filename,
  className = '',
}: ExportButtonProps) => {
  const { prepareReadingsForExport, generateHeaders, generateFilename } = useExport();

  // Si no hay datos, deshabilitar el botón
  if (!data || data.length === 0) {
    return (
      <button
        disabled
        className={`px-4 py-2 bg-gray-300 text-gray-500 rounded-lg cursor-not-allowed ${className}`}
      >
        📥 Exportar CSV (Sin datos)
      </button>
    );
  }

  // Preparar datos para exportación
  const csvData = prepareReadingsForExport(data, device);
  const headers = generateHeaders(data);
  const csvFilename = filename || generateFilename(device?.name || 'readings');

  return (
    <CSVLink
      data={csvData}
      headers={headers.map((h) => ({ label: h, key: h }))}
      filename={csvFilename}
      className={`inline-block px-4 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700 transition ${className}`}
      target="_blank"
    >
      📥 Exportar CSV ({data.length} registros)
    </CSVLink>
  );
};

export default ExportButton;
