/**
 * SensorTable Component - Tabla responsive de sensores del catálogo
 *
 * Muestra sensores con:
 * - Información básica (nombre, tipo, protocolo)
 * - Configuración (GPIO, calibración)
 * - Estado (activo/inactivo, built-in/custom)
 * - Acciones (editar, activar/desactivar, eliminar)
 */

import { SensorCatalog } from '../../types';

interface SensorTableProps {
  sensors: SensorCatalog[];
  onEdit: (sensor: SensorCatalog) => void;
  onActivate: (sensor: SensorCatalog) => void;
  onDeactivate: (sensor: SensorCatalog) => void;
  onDelete: (sensor: SensorCatalog) => void;
}

export default function SensorTable({
  sensors,
  onEdit,
  onActivate,
  onDeactivate,
  onDelete,
}: SensorTableProps) {
  const formatNumber = (value: number | null | undefined, decimals: number = 2): string => {
    if (value === null || value === undefined) return '-';
    return value.toFixed(decimals);
  };

  const getSensorTypeBadge = (type: string) => {
    const colors: Record<string, string> = {
      temperature: 'bg-red-100 text-red-800',
      humidity: 'bg-blue-100 text-blue-800',
      pressure: 'bg-purple-100 text-purple-800',
      analog: 'bg-yellow-100 text-yellow-800',
      digital: 'bg-green-100 text-green-800',
      custom: 'bg-gray-100 text-gray-800',
    };

    return colors[type] || 'bg-gray-100 text-gray-800';
  };

  const getProtocolBadge = (protocol: string | null) => {
    if (!protocol) return null;

    const colors: Record<string, string> = {
      OneWire: 'bg-indigo-100 text-indigo-800',
      I2C: 'bg-cyan-100 text-cyan-800',
      SPI: 'bg-teal-100 text-teal-800',
      ADC: 'bg-orange-100 text-orange-800',
      Digital: 'bg-green-100 text-green-800',
      UART: 'bg-pink-100 text-pink-800',
      Modbus: 'bg-purple-100 text-purple-800',
    };

    return colors[protocol] || 'bg-gray-100 text-gray-800';
  };

  return (
    <div className="overflow-x-auto">
      <table className="min-w-full divide-y divide-gray-200">
        <thead className="bg-gray-50">
          <tr>
            <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
              Sensor
            </th>
            <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
              Tipo
            </th>
            <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
              Protocolo / GPIO
            </th>
            <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
              Calibración
            </th>
            <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
              Rango
            </th>
            <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
              Estado
            </th>
            <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase tracking-wider">
              Acciones
            </th>
          </tr>
        </thead>
        <tbody className="bg-white divide-y divide-gray-200">
          {sensors.map((sensor) => (
            <tr key={sensor.id} className="hover:bg-gray-50">
              {/* Sensor Info */}
              <td className="px-6 py-4">
                <div className="flex items-center">
                  <div>
                    <div className="text-sm font-medium text-gray-900 flex items-center gap-2">
                      {sensor.name}
                      {sensor.is_builtin && (
                        <span className="px-2 py-0.5 text-xs font-medium rounded bg-blue-100 text-blue-800">
                          Built-in
                        </span>
                      )}
                    </div>
                    {sensor.description && (
                      <div className="text-sm text-gray-500 max-w-xs truncate">
                        {sensor.description}
                      </div>
                    )}
                    {sensor.model && (
                      <div className="text-xs text-gray-400">
                        {sensor.manufacturer ? `${sensor.manufacturer} - ` : ''}
                        {sensor.model}
                      </div>
                    )}
                  </div>
                </div>
              </td>

              {/* Tipo */}
              <td className="px-6 py-4 whitespace-nowrap">
                <span
                  className={`px-3 py-1 inline-flex text-xs leading-5 font-semibold rounded-full ${getSensorTypeBadge(
                    sensor.sensor_type
                  )}`}
                >
                  {sensor.sensor_type}
                </span>
              </td>

              {/* Protocolo / GPIO */}
              <td className="px-6 py-4">
                {sensor.protocol && (
                  <span
                    className={`px-2 py-1 inline-flex text-xs leading-5 font-semibold rounded ${getProtocolBadge(
                      sensor.protocol
                    )}`}
                  >
                    {sensor.protocol}
                  </span>
                )}
                {sensor.gpio_pin !== null && (
                  <div className="text-xs text-gray-500 mt-1">GPIO {sensor.gpio_pin}</div>
                )}
                {sensor.i2c_address && (
                  <div className="text-xs text-gray-500 mt-1">I2C: {sensor.i2c_address}</div>
                )}
              </td>

              {/* Calibración */}
              <td className="px-6 py-4 text-sm text-gray-900">
                {sensor.calibration_offset !== 0 || sensor.calibration_factor !== 1 ? (
                  <div>
                    <div className="text-xs">
                      Offset: {formatNumber(sensor.calibration_offset, 3)}
                    </div>
                    <div className="text-xs">
                      Factor: {formatNumber(sensor.calibration_factor, 3)}
                    </div>
                  </div>
                ) : (
                  <span className="text-gray-400 text-xs">Sin calibración</span>
                )}
              </td>

              {/* Rango */}
              <td className="px-6 py-4 text-sm text-gray-900">
                {sensor.value_min !== null || sensor.value_max !== null ? (
                  <div className="text-xs">
                    {formatNumber(sensor.value_min)} - {formatNumber(sensor.value_max)} {sensor.unit}
                  </div>
                ) : (
                  <span className="text-gray-400 text-xs">-</span>
                )}
              </td>

              {/* Estado */}
              <td className="px-6 py-4 whitespace-nowrap">
                <span
                  className={`px-3 py-1 inline-flex text-xs leading-5 font-semibold rounded-full ${
                    sensor.is_active
                      ? 'bg-green-100 text-green-800'
                      : 'bg-gray-100 text-gray-800'
                  }`}
                >
                  {sensor.is_active ? 'Activo' : 'Inactivo'}
                </span>
              </td>

              {/* Acciones */}
              <td className="px-6 py-4 whitespace-nowrap text-right text-sm font-medium">
                <div className="flex justify-end gap-2">
                  {/* Editar */}
                  <button
                    onClick={() => onEdit(sensor)}
                    className="text-purple-600 hover:text-purple-900 font-medium"
                    title="Editar sensor"
                  >
                    Editar
                  </button>

                  {/* Activar/Desactivar */}
                  {sensor.is_active ? (
                    <button
                      onClick={() => onDeactivate(sensor)}
                      className="text-yellow-600 hover:text-yellow-900 font-medium"
                      title="Desactivar sensor"
                    >
                      Desactivar
                    </button>
                  ) : (
                    <button
                      onClick={() => onActivate(sensor)}
                      className="text-green-600 hover:text-green-900 font-medium"
                      title="Activar sensor"
                    >
                      Activar
                    </button>
                  )}

                  {/* Eliminar (solo custom) */}
                  {!sensor.is_builtin && (
                    <button
                      onClick={() => onDelete(sensor)}
                      className="text-red-600 hover:text-red-900 font-medium"
                      title="Eliminar sensor"
                    >
                      Eliminar
                    </button>
                  )}
                </div>
              </td>
            </tr>
          ))}
        </tbody>
      </table>

      {sensors.length === 0 && (
        <div className="text-center py-8 text-gray-500">
          No hay sensores para mostrar
        </div>
      )}
    </div>
  );
}
