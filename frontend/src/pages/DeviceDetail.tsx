/**
 * DeviceDetail - IdeaMakers IoT Monitoring
 *
 * Vista de detalle de dispositivo con layout de 3 columnas:
 * - Sidebar: Metadata y salud del dispositivo
 * - Centro: Gráficos dinámicos con selector temporal
 * - (Responsive: colapsa a 1 col en mobile)
 *
 * Integra: IMCard, IMBadge, IMButton, DynamicChart
 */

import React, { useState } from 'react';
import { useParams } from 'react-router-dom';
import { useQuery } from '@tanstack/react-query';
import { format, formatDistanceToNow } from 'date-fns';
import { es } from 'date-fns/locale';
import { Layout } from '@/components/layout/Layout';
import { IMCard, IMBadge, IMButton, OnlineBadge, OfflineBadge } from '@/components/common';
import { DynamicChart } from '@/components/charts/DynamicChart';
import { ExportButton } from '@/components/common/ExportButton';
import { useWebSocket } from '@/hooks/useWebSocket';
import deviceService from '@/services/deviceService';
import readingService from '@/services/readingService';
import type { Device, SensorReading } from '@/types';

// ========================================
// HELPER FUNCTIONS
// ========================================

const isOnline = (lastSeenAt: string | null): boolean => {
  if (!lastSeenAt) return false;
  const lastSeen = new Date(lastSeenAt);
  const now = new Date();
  const diffMinutes = (now.getTime() - lastSeen.getTime()) / (1000 * 60);
  return diffMinutes < 10;
};

const getStatusBadge = (status: string) => {
  const statusMap: Record<string, { variant: any; label: string }> = {
    active: { variant: 'success', label: 'Activo' },
    inactive: { variant: 'neutral', label: 'Inactivo' },
    maintenance: { variant: 'warning', label: 'Mantenimiento' },
    error: { variant: 'danger', label: 'Error' },
  };
  return statusMap[status] || { variant: 'neutral', label: status };
};

const calculateUptime = (lastSeenAt: string | null): string => {
  if (!lastSeenAt) return 'N/A';
  const lastSeen = new Date(lastSeenAt);
  const now = new Date();
  const uptimeHours = Math.max(0, (now.getTime() - lastSeen.getTime()) / (1000 * 60 * 60));
  if (uptimeHours < 24) return `${uptimeHours.toFixed(1)}h`;
  return `${(uptimeHours / 24).toFixed(1)} días`;
};

// ========================================
// METADATA SIDEBAR COMPONENT
// ========================================

interface MetadataSidebarProps {
  device: Device;
  readingsCount: number;
}

const MetadataSidebar: React.FC<MetadataSidebarProps> = ({ device, readingsCount }) => {
  const online = isOnline(device.last_seen_at);
  const statusInfo = getStatusBadge(device.status);

  return (
    <div className="space-y-4">
      {/* Device Health Card */}
      <IMCard title="Estado del Dispositivo" padding="md">
        <div className="space-y-4">
          {/* Connection Status */}
          <div>
            <p className="text-xs text-im-neutral-500 mb-1">Conexión</p>
            {online ? (
              <OnlineBadge size="md" />
            ) : (
              <OfflineBadge size="md" />
            )}
          </div>

          {/* Operational Status */}
          <div>
            <p className="text-xs text-im-neutral-500 mb-1">Estado Operacional</p>
            <IMBadge variant={statusInfo.variant} size="md">
              {statusInfo.label}
            </IMBadge>
          </div>

          {/* Last Seen */}
          <div>
            <p className="text-xs text-im-neutral-500 mb-1">Última Actividad</p>
            <p className="text-sm font-semibold text-im-neutral-900">
              {device.last_seen_at ? (
                <>
                  {formatDistanceToNow(new Date(device.last_seen_at), {
                    addSuffix: true,
                    locale: es,
                  })}
                  <span className="block text-xs text-im-neutral-500 mt-0.5">
                    {format(new Date(device.last_seen_at), 'dd/MM/yyyy HH:mm:ss')}
                  </span>
                </>
              ) : (
                <span className="text-im-neutral-400">Nunca visto</span>
              )}
            </p>
          </div>

          {/* Uptime */}
          <div>
            <p className="text-xs text-im-neutral-500 mb-1">Uptime Estimado</p>
            <p className="text-sm font-semibold text-im-neutral-900">
              {calculateUptime(device.last_seen_at)}
            </p>
          </div>
        </div>
      </IMCard>

      {/* Device Info Card */}
      <IMCard title="Información Técnica" padding="md">
        <div className="space-y-3">
          {/* EUI */}
          <div>
            <p className="text-xs text-im-neutral-500 mb-1">Device EUI</p>
            <code className="text-xs bg-im-neutral-100 px-2 py-1 rounded text-im-neutral-700 font-mono break-all">
              {device.device_eui}
            </code>
          </div>

          {/* Firmware */}
          <div>
            <p className="text-xs text-im-neutral-500 mb-1">Firmware Version</p>
            <p className="text-sm font-semibold text-im-neutral-900">
              {device.firmware_version || (
                <span className="text-im-neutral-400">No especificado</span>
              )}
            </p>
          </div>

          {/* Readings Count */}
          <div>
            <p className="text-xs text-im-neutral-500 mb-1">Lecturas Registradas</p>
            <p className="text-sm font-semibold text-im-neutral-900">
              {readingsCount.toLocaleString('es-AR')}
            </p>
          </div>

          {/* Created Date */}
          <div>
            <p className="text-xs text-im-neutral-500 mb-1">Fecha de Registro</p>
            <p className="text-sm font-semibold text-im-neutral-900">
              {format(new Date(device.created_at), 'dd/MM/yyyy', { locale: es })}
            </p>
          </div>
        </div>
      </IMCard>

      {/* Metadata Card (if available) */}
      {device.extra_data && Object.keys(device.extra_data).length > 0 && (
        <IMCard title="Metadata Adicional" padding="md">
          <div className="space-y-2">
            {Object.entries(device.extra_data).map(([key, value]) => (
              <div key={key}>
                <p className="text-xs text-im-neutral-500">{key}</p>
                <p className="text-sm text-im-neutral-900">
                  {typeof value === 'object' ? JSON.stringify(value) : String(value)}
                </p>
              </div>
            ))}
          </div>
        </IMCard>
      )}
    </div>
  );
};

// ========================================
// MAIN COMPONENT
// ========================================

export const DeviceDetail = () => {
  const { id } = useParams<{ id: string }>();
  const deviceId = parseInt(id || '0');
  const [timeRange, setTimeRange] = useState<'24h' | '7d' | '30d'>('24h');

  // ========================================
  // DATA FETCHING
  // ========================================

  const { data: device, isLoading: deviceLoading, error: deviceError } = useQuery<Device>({
    queryKey: ['device', deviceId],
    queryFn: () => deviceService.getDevice(deviceId),
  });

  const { data: readings, isLoading: readingsLoading } = useQuery<SensorReading[]>({
    queryKey: ['readings', deviceId, timeRange],
    queryFn: () => readingService.getDeviceReadings(deviceId, timeRange),
    enabled: !!device,
  });

  // WebSocket: auto-refresh cuando llegan nuevos readings para este device
  useWebSocket({ deviceId });

  // ========================================
  // LOADING STATE
  // ========================================

  if (deviceLoading) {
    return (
      <Layout
        title="Cargando..."
        breadcrumbs={[
          { label: 'Dashboard', href: '/dashboard' },
          { label: 'Dispositivos', href: '/devices' },
          { label: 'Cargando...' },
        ]}
      >
        <div className="flex items-center justify-center h-[60vh]">
          <div className="text-center">
            <div className="inline-block w-16 h-16 border-4 border-im-neutral-100 border-t-im-orange rounded-full animate-spin"></div>
            <p className="mt-4 text-im-neutral-500 font-medium">
              Cargando información del dispositivo...
            </p>
          </div>
        </div>
      </Layout>
    );
  }

  // ========================================
  // ERROR STATE
  // ========================================

  if (deviceError || !device) {
    return (
      <Layout
        title="Error"
        breadcrumbs={[
          { label: 'Dashboard', href: '/dashboard' },
          { label: 'Dispositivos', href: '/devices' },
          { label: 'Error' },
        ]}
      >
        <div className="max-w-2xl mx-auto mt-8">
          <div className="bg-im-danger-light border border-im-danger rounded-md p-4">
            <div className="flex items-start gap-3">
              <svg className="w-5 h-5 text-im-danger flex-shrink-0 mt-0.5" fill="currentColor" viewBox="0 0 20 20">
                <path fillRule="evenodd" d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-7 4a1 1 0 11-2 0 1 1 0 012 0zm-1-9a1 1 0 00-1 1v4a1 1 0 102 0V6a1 1 0 00-1-1z" clipRule="evenodd" />
              </svg>
              <div className="flex-1">
                <h3 className="text-sm font-semibold text-im-danger">
                  Dispositivo no encontrado
                </h3>
                <p className="text-sm text-im-danger mt-1">
                  No se pudo cargar la información del dispositivo con ID {deviceId}.
                </p>
              </div>
            </div>
          </div>
        </div>
      </Layout>
    );
  }

  // ========================================
  // TIME RANGE OPTIONS
  // ========================================

  const timeRangeOptions = [
    { value: '24h' as const, label: 'Últimas 24h' },
    { value: '7d' as const, label: 'Últimos 7 días' },
    { value: '30d' as const, label: 'Últimos 30 días' },
  ];

  // ========================================
  // MAIN RENDER
  // ========================================

  return (
    <Layout
      title={device.name}
      breadcrumbs={[
        { label: 'Dashboard', href: '/dashboard' },
        { label: 'Dispositivos', href: '/devices' },
        { label: device.name },
      ]}
    >
      {/* Page Header */}
      <div className="mb-6">
        <h1 className="font-montserrat text-3xl font-bold text-im-blue">{device.name}</h1>
        <p className="text-im-neutral-500 mt-1">
          Monitoreo en tiempo real de variables del sensor
        </p>
      </div>

      {/* 3-Column Layout (Responsive) */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
        {/* ========================================
            LEFT SIDEBAR - Metadata (3 cols en desktop)
            ======================================== */}
        <div className="lg:col-span-3">
          <MetadataSidebar device={device} readingsCount={readings?.length || 0} />
        </div>

        {/* ========================================
            CENTER COLUMN - Charts (9 cols en desktop)
            ======================================== */}
        <div className="lg:col-span-9 space-y-6">
          {/* Time Range Selector + Export */}
          <IMCard padding="md">
            <div className="flex items-center justify-between flex-wrap gap-4">
              <div>
                <h2 className="text-lg font-semibold text-im-neutral-900 mb-2">
                  Rango Temporal
                </h2>
                <div className="flex gap-2">
                  {timeRangeOptions.map((option) => (
                    <IMButton
                      key={option.value}
                      size="sm"
                      variant={timeRange === option.value ? 'primary' : 'secondary'}
                      onClick={() => setTimeRange(option.value)}
                    >
                      {option.label}
                    </IMButton>
                  ))}
                </div>
              </div>

              {/* Export Button */}
              <div>
                <ExportButton data={readings || []} device={device} />
              </div>
            </div>
          </IMCard>

          {/* Dynamic Chart */}
          <IMCard title="Gráfico de Variables" subtitle="Auto-discovery de sensores" padding="lg">
            {readingsLoading ? (
              <div className="flex items-center justify-center h-[400px]">
                <div className="text-center">
                  <div className="inline-block w-12 h-12 border-4 border-im-neutral-100 border-t-im-orange rounded-full animate-spin"></div>
                  <p className="mt-3 text-im-neutral-500 text-sm">Cargando gráfico...</p>
                </div>
              </div>
            ) : (
              <DynamicChart
                deviceId={deviceId}
                timeRange={timeRange}
                height={450}
              />
            )}
          </IMCard>

          {/* Readings Timeline Table */}
          <IMCard
            title="Timeline de Lecturas"
            subtitle={`Últimas ${Math.min(readings?.length || 0, 20)} lecturas registradas`}
            padding="none"
          >
            {readings && readings.length > 0 ? (
              <div className="overflow-x-auto">
                <table className="im-table">
                  <thead>
                    <tr>
                      <th>Timestamp</th>
                      <th className="hidden md:table-cell">Temperatura</th>
                      <th className="hidden md:table-cell">Humedad</th>
                      <th>Calidad</th>
                      <th className="hidden lg:table-cell">Raw Payload</th>
                    </tr>
                  </thead>
                  <tbody>
                    {readings.slice(0, 20).map((reading) => (
                      <tr key={reading.id}>
                        {/* Timestamp */}
                        <td>
                          <div className="text-sm font-medium text-im-neutral-900">
                            {format(new Date(reading.timestamp), 'HH:mm:ss')}
                          </div>
                          <div className="text-xs text-im-neutral-500">
                            {format(new Date(reading.timestamp), 'dd/MM/yyyy')}
                          </div>
                        </td>

                        {/* Temperature */}
                        <td className="hidden md:table-cell">
                          {reading.data_payload.temp_c !== undefined ? (
                            <span className="text-sm font-medium text-im-neutral-900">
                              {reading.data_payload.temp_c.toFixed(1)} °C
                            </span>
                          ) : (
                            <span className="text-sm text-im-neutral-400">-</span>
                          )}
                        </td>

                        {/* Humidity */}
                        <td className="hidden md:table-cell">
                          {reading.data_payload.humidity_pct !== undefined ? (
                            <span className="text-sm font-medium text-im-neutral-900">
                              {reading.data_payload.humidity_pct.toFixed(1)} %
                            </span>
                          ) : (
                            <span className="text-sm text-im-neutral-400">-</span>
                          )}
                        </td>

                        {/* Quality Score */}
                        <td>
                          <IMBadge
                            variant={(reading.quality_score || 0) > 0.8 ? 'success' : (reading.quality_score || 0) > 0.5 ? 'warning' : 'danger'}
                            size="sm"
                          >
                            {((reading.quality_score || 0) * 100).toFixed(0)}%
                          </IMBadge>
                        </td>

                        {/* Raw Payload (collapsed in mobile) */}
                        <td className="hidden lg:table-cell">
                          <details className="text-xs">
                            <summary className="cursor-pointer text-im-blue hover:text-im-blue-hover">
                              Ver JSON
                            </summary>
                            <pre className="mt-2 p-2 bg-im-neutral-50 rounded text-xs overflow-auto max-w-xs">
                              {JSON.stringify(reading.data_payload, null, 2)}
                            </pre>
                          </details>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            ) : (
              // Empty State
              <div className="py-16 text-center">
                <svg
                  className="mx-auto h-12 w-12 text-im-neutral-300"
                  fill="none"
                  viewBox="0 0 24 24"
                  stroke="currentColor"
                >
                  <path
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    strokeWidth={1}
                    d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z"
                  />
                </svg>
                <h3 className="mt-4 text-sm font-semibold text-im-neutral-900">
                  No hay lecturas disponibles
                </h3>
                <p className="mt-1 text-sm text-im-neutral-500">
                  Este dispositivo no ha enviado datos en el rango seleccionado
                </p>
              </div>
            )}
          </IMCard>
        </div>
      </div>
    </Layout>
  );
};

export default DeviceDetail;
