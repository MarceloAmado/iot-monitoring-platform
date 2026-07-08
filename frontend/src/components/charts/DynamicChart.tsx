/**
 * Componente de gráfico dinámico que auto-genera visualizaciones
 * basándose en el schema del dispositivo (auto-discovery).
 *
 * Características:
 * - Detecta automáticamente las variables del sensor
 * - Asigna colores y unidades desde el backend
 * - Soporta múltiples variables en el mismo gráfico
 * - Responsive y con loading states
 */

import { useQuery } from '@tanstack/react-query';
import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
  TooltipProps,
} from 'recharts';
import { format } from 'date-fns';
import { es } from 'date-fns/locale';
import deviceService from '@/services/deviceService';
import readingService from '@/services/readingService';
import type { SensorReading } from '@/types';

interface DynamicChartProps {
  deviceId: number;
  timeRange?: '24h' | '7d' | '30d';
  height?: number;
  title?: string;
}

/**
 * Colores de fallback si el backend no devuelve color
 * Paleta IdeaMakers + complementarios
 */
const FALLBACK_COLORS = [
  '#F57C20', // IdeaMakers Orange
  '#0F3C57', // IdeaMakers Deep Blue
  '#5E9FB4', // IdeaMakers Blue Light
  '#F9A45C', // IdeaMakers Orange Soft
  '#22C55E', // Success Green
  '#EAB308', // Warning Yellow
  '#EF4444', // Danger Red
  '#8B5CF6', // Purple
];

/**
 * Tooltip personalizado con formato mejorado
 */
const CustomTooltip = ({
  active,
  payload,
  label,
}: TooltipProps<number, string>) => {
  if (!active || !payload || !payload.length) return null;

  return (
    <div className="bg-white border border-im-neutral-200 rounded-lg shadow-im-card p-3">
      <p className="text-sm font-semibold text-im-neutral-700 mb-2">{label}</p>
      {payload.map((entry, index) => (
        <div key={index} className="flex items-center gap-2 text-sm">
          <div
            className="w-3 h-3 rounded-full"
            style={{ backgroundColor: entry.color }}
          />
          <span className="text-im-neutral-600">{entry.name}:</span>
          <span className="font-semibold text-im-neutral-900">
            {typeof entry.value === 'number' ? entry.value.toFixed(2) : entry.value}
          </span>
        </div>
      ))}
    </div>
  );
};

/**
 * Componente principal de gráfico dinámico
 */
export const DynamicChart = ({
  deviceId,
  timeRange = '24h',
  height = 400,
  title,
}: DynamicChartProps) => {
  // 1. Fetch schema del device (auto-discovery de variables)
  const { data: schema, isLoading: schemaLoading, error: schemaError } = useQuery({
    queryKey: ['device-schema', deviceId],
    queryFn: () => deviceService.getDeviceSchema(deviceId),
    staleTime: 5 * 60 * 1000, // Cache 5 minutos (schema no cambia frecuentemente)
  });

  // 2. Fetch readings
  const { data: readings, isLoading: readingsLoading, error: readingsError } = useQuery({
    queryKey: ['readings', deviceId, timeRange],
    queryFn: () => readingService.getDeviceReadings(deviceId, timeRange),
    refetchInterval: 60 * 1000, // Refetch cada 1 minuto
  });

  // Estados de carga
  if (schemaLoading || readingsLoading) {
    return (
      <div className="flex items-center justify-center" style={{ height }}>
        <div className="text-center">
          <div className="inline-block animate-spin rounded-full h-8 w-8 border-b-2 border-im-orange mb-2"></div>
          <p className="text-im-neutral-600 text-sm">
            {schemaLoading ? 'Cargando schema...' : 'Cargando datos...'}
          </p>
        </div>
      </div>
    );
  }

  // Manejo de errores
  if (schemaError || readingsError) {
    return (
      <div className="bg-im-danger-light border border-im-danger text-im-danger px-4 py-3 rounded-md">
        <p className="font-semibold">Error al cargar el gráfico</p>
        <p className="text-sm mt-1">
          {schemaError ? 'No se pudo obtener el schema del dispositivo' : 'No se pudieron obtener los datos'}
        </p>
      </div>
    );
  }

  // Sin datos
  if (!readings || readings.length === 0) {
    return (
      <div className="text-center py-12 text-im-neutral-500" style={{ height }}>
        <svg
          className="mx-auto h-12 w-12 text-im-neutral-400 mb-4"
          fill="none"
          viewBox="0 0 24 24"
          stroke="currentColor"
        >
          <path
            strokeLinecap="round"
            strokeLinejoin="round"
            strokeWidth={2}
            d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z"
          />
        </svg>
        <p className="text-lg font-medium text-im-neutral-900">No hay datos disponibles</p>
        <p className="text-sm mt-1">
          No se encontraron lecturas para el rango seleccionado: {timeRange}
        </p>
      </div>
    );
  }

  // Sin schema
  if (!schema || !schema.variables || schema.variables.length === 0) {
    return (
      <div className="bg-im-warning-light border border-im-warning text-im-warning px-4 py-3 rounded-md">
        <p className="font-semibold">Schema no disponible</p>
        <p className="text-sm mt-1">
          No se pudieron detectar variables del sensor. Verifica que el dispositivo haya enviado al menos una lectura.
        </p>
      </div>
    );
  }

  // 3. Preparar datos para el gráfico
  const chartData = readings.map((reading: SensorReading) => {
    const dataPoint: any = {
      timestamp: format(new Date(reading.timestamp), 'HH:mm', { locale: es }),
      fullTimestamp: format(new Date(reading.timestamp), 'dd/MM/yyyy HH:mm:ss', {
        locale: es,
      }),
    };

    // Agregar cada variable del schema al dataPoint
    schema.variables.forEach((variable) => {
      const value = reading.data_payload[variable.key];
      // Convertir a número si es posible, sino usar valor raw
      dataPoint[variable.key] =
        typeof value === 'number' ? value : value !== undefined ? value : null;
    });

    return dataPoint;
  });

  // 4. Filtrar solo variables numéricas para el gráfico
  const numericVariables = schema.variables.filter((variable) => {
    // Verificar si al menos un reading tiene un valor numérico para esta variable
    return chartData.some(
      (dataPoint) =>
        typeof dataPoint[variable.key] === 'number' &&
        !isNaN(dataPoint[variable.key])
    );
  });

  if (numericVariables.length === 0) {
    return (
      <div className="bg-yellow-50 border border-yellow-200 text-yellow-700 px-4 py-3 rounded-md">
        <p className="font-semibold">Sin datos numéricos</p>
        <p className="text-sm mt-1">
          No se encontraron variables numéricas para graficar.
        </p>
      </div>
    );
  }

  // 5. Renderizar gráfico
  return (
    <div>
      {title && <h3 className="text-lg font-semibold text-im-neutral-900 mb-4">{title}</h3>}

      <ResponsiveContainer width="100%" height={height}>
        <LineChart data={chartData} margin={{ top: 5, right: 30, left: 20, bottom: 5 }}>
          <CartesianGrid strokeDasharray="3 3" stroke="#E5E7EB" />
          <XAxis
            dataKey="timestamp"
            tick={{ fill: '#6B7280', fontSize: 12, fontFamily: 'Open Sans' }}
            stroke="#9CA3AF"
          />
          <YAxis
            tick={{ fill: '#6B7280', fontSize: 12, fontFamily: 'Open Sans' }}
            stroke="#9CA3AF"
          />
          <Tooltip content={<CustomTooltip />} />
          <Legend
            wrapperStyle={{ paddingTop: '20px', fontFamily: 'Open Sans' }}
            iconType="line"
            formatter={(value, entry: any) => {
              const variable = numericVariables.find((v) => v.key === entry.dataKey);
              return variable
                ? `${variable.label} (${variable.unit})`
                : value;
            }}
          />

          {/* Auto-generar líneas para cada variable */}
          {numericVariables.map((variable, index) => (
            <Line
              key={variable.key}
              type="monotone"
              dataKey={variable.key}
              name={variable.key}
              stroke={variable.color || FALLBACK_COLORS[index % FALLBACK_COLORS.length]}
              strokeWidth={2.5}
              dot={false}
              activeDot={{ r: 6, fill: variable.color || FALLBACK_COLORS[index % FALLBACK_COLORS.length] }}
              connectNulls
            />
          ))}
        </LineChart>
      </ResponsiveContainer>

      {/* Metadata del gráfico */}
      <div className="mt-4 pt-4 border-t border-im-neutral-200">
        <div className="flex flex-wrap gap-4 text-sm text-im-neutral-600">
          <div>
            <span className="font-medium text-im-neutral-700">Variables detectadas:</span>{' '}
            <span className="text-im-neutral-900">{numericVariables.length}</span>
          </div>
          <div>
            <span className="font-medium text-im-neutral-700">Puntos de datos:</span>{' '}
            <span className="text-im-neutral-900">{chartData.length}</span>
          </div>
          <div>
            <span className="font-medium text-im-neutral-700">Rango:</span>{' '}
            <span className="text-im-neutral-900">
              {timeRange === '24h' ? 'Últimas 24 horas' : timeRange === '7d' ? 'Últimos 7 días' : 'Últimos 30 días'}
            </span>
          </div>
        </div>
      </div>
    </div>
  );
};

export default DynamicChart;
