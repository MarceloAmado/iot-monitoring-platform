/**
 * Device Health Dashboard
 *
 * Página que muestra métricas de salud de todos los devices:
 * - Estado online/offline
 * - Calidad de señal WiFi (RSSI)
 * - Uptime, memoria, batería
 * - Total de readings
 * - Alertas activas
 */

import React from 'react';
import { useQuery } from '@tanstack/react-query';
import { formatDistanceToNow } from 'date-fns';
import { es } from 'date-fns/locale';
import { Layout } from '@/components/layout/Layout';
import { IMCard, IMBadge, OnlineBadge, OfflineBadge } from '@/components/common';
import deviceService from '@/services/deviceService';
import type { DeviceHealthMetrics } from '@/types';

// ========================================
// HELPER FUNCTIONS
// ========================================

const getWiFiQualityColor = (quality: string | null): string => {
  if (!quality) return 'text-im-neutral-400';

  switch (quality) {
    case 'Excellent':
      return 'text-im-success';
    case 'Good':
      return 'text-im-blue';
    case 'Fair':
      return 'text-im-warning';
    case 'Poor':
    case 'Very Poor':
      return 'text-im-danger';
    default:
      return 'text-im-neutral-400';
  }
};

const getBatteryColor = (percentage: number | null): string => {
  if (!percentage) return 'text-im-neutral-400';

  if (percentage >= 80) return 'text-im-success';
  if (percentage >= 50) return 'text-im-blue';
  if (percentage >= 20) return 'text-im-warning';
  return 'text-im-danger';
};

const formatBytes = (bytes: number | null): string => {
  if (!bytes) return 'N/A';

  const kb = bytes / 1024;
  if (kb < 1024) return `${kb.toFixed(1)} KB`;

  const mb = kb / 1024;
  return `${mb.toFixed(2)} MB`;
};

// ========================================
// METRIC CARD COMPONENT
// ========================================

interface MetricCardProps {
  label: string;
  value: number | string;
  color: 'blue' | 'success' | 'danger' | 'warning' | 'neutral';
  icon: React.ReactNode;
  subtitle?: string;
}

const MetricCard: React.FC<MetricCardProps> = ({ label, value, color, icon, subtitle }) => {
  const colorStyles = {
    blue: 'text-im-blue bg-im-blue/10',
    success: 'text-im-success bg-im-success-light',
    danger: 'text-im-danger bg-im-danger-light',
    warning: 'text-im-warning bg-im-warning-light',
    neutral: 'text-im-neutral-500 bg-im-neutral-100',
  };

  return (
    <IMCard hoverable className="hover-lift">
      <div className="flex items-start justify-between">
        <div className="flex-1">
          <p className="text-sm font-medium text-im-neutral-500 mb-1">{label}</p>
          <p className="text-3xl font-bold text-im-neutral-900">{value}</p>
          {subtitle && (
            <p className="text-xs text-im-neutral-400 mt-1">{subtitle}</p>
          )}
        </div>

        <div className={`p-3 rounded-md ${colorStyles[color]}`}>
          {icon}
        </div>
      </div>
    </IMCard>
  );
};

// ========================================
// DEVICE ROW COMPONENT
// ========================================

interface DeviceRowProps {
  device: DeviceHealthMetrics;
}

const DeviceRow: React.FC<DeviceRowProps> = ({ device }) => {
  return (
    <tr className="hover:bg-im-neutral-50 transition-colors">
      {/* Device Info */}
      <td>
        <div>
          <div className="font-semibold text-im-neutral-900">{device.name}</div>
          <div className="text-xs text-im-neutral-500 mt-0.5">
            {device.device_eui}
          </div>
          {device.location_name && (
            <div className="text-xs text-im-neutral-400 mt-0.5">
              📍 {device.location_name}
            </div>
          )}
        </div>
      </td>

      {/* Status */}
      <td>
        {device.is_online ? (
          <OnlineBadge size="sm" />
        ) : (
          <OfflineBadge size="sm" />
        )}
      </td>

      {/* WiFi Quality */}
      <td>
        {device.wifi_quality ? (
          <div className="flex items-center gap-2">
            <span className={`font-medium ${getWiFiQualityColor(device.wifi_quality)}`}>
              {device.wifi_quality}
            </span>
            {device.rssi_dbm && (
              <span className="text-xs text-im-neutral-400">
                ({device.rssi_dbm} dBm)
              </span>
            )}
          </div>
        ) : (
          <span className="text-im-neutral-400">N/A</span>
        )}
      </td>

      {/* Uptime */}
      <td className="hidden lg:table-cell">
        {device.uptime_hours ? (
          <span className="text-im-neutral-700">
            {device.uptime_hours.toFixed(1)}h
          </span>
        ) : (
          <span className="text-im-neutral-400">N/A</span>
        )}
      </td>

      {/* Memoria */}
      <td className="hidden xl:table-cell">
        {device.free_heap_bytes ? (
          <span className="text-im-neutral-700">
            {formatBytes(device.free_heap_bytes)}
          </span>
        ) : (
          <span className="text-im-neutral-400">N/A</span>
        )}
      </td>

      {/* Batería */}
      <td>
        {device.battery_percentage !== null ? (
          <div className="flex items-center gap-2">
            <span className={`font-medium ${getBatteryColor(device.battery_percentage)}`}>
              {device.battery_percentage}%
            </span>
            {device.battery_mv && (
              <span className="text-xs text-im-neutral-400">
                ({device.battery_mv} mV)
              </span>
            )}
          </div>
        ) : (
          <span className="text-im-neutral-400">N/A</span>
        )}
      </td>

      {/* Readings 24h */}
      <td className="hidden lg:table-cell">
        <div>
          <div className="font-medium text-im-neutral-900">
            {device.readings_last_24h}
          </div>
          <div className="text-xs text-im-neutral-400">
            Total: {device.total_readings}
          </div>
        </div>
      </td>

      {/* Alertas */}
      <td>
        {device.active_alerts_count > 0 ? (
          <IMBadge variant="danger" size="sm">
            {device.active_alerts_count} alertas
          </IMBadge>
        ) : (
          <span className="text-im-neutral-400">Sin alertas</span>
        )}
      </td>

      {/* Última Actividad */}
      <td className="hidden xl:table-cell">
        {device.last_seen_at ? (
          <span className="text-im-neutral-500 text-sm">
            {formatDistanceToNow(new Date(device.last_seen_at), {
              addSuffix: true,
              locale: es,
            })}
          </span>
        ) : (
          <span className="text-im-neutral-400">Nunca</span>
        )}
      </td>
    </tr>
  );
};

// ========================================
// MAIN COMPONENT
// ========================================

export default function DeviceHealth() {
  const { data: dashboard, isLoading, error } = useQuery({
    queryKey: ['device-health-dashboard'],
    queryFn: () => deviceService.getHealthDashboard(),
    refetchInterval: 60000, // Refetch cada 60 segundos
  });

  // ========================================
  // LOADING STATE
  // ========================================

  if (isLoading) {
    return (
      <Layout title="Salud de Dispositivos">
        <div className="flex items-center justify-center h-[60vh]">
          <div className="text-center">
            <div className="inline-block w-16 h-16 border-4 border-im-neutral-100 border-t-im-orange rounded-full animate-spin"></div>
            <p className="mt-4 text-im-neutral-500 font-medium">Cargando métricas de salud...</p>
          </div>
        </div>
      </Layout>
    );
  }

  // ========================================
  // ERROR STATE
  // ========================================

  if (error) {
    return (
      <Layout title="Salud de Dispositivos">
        <div className="max-w-2xl mx-auto mt-8">
          <div className="bg-im-danger-light border border-im-danger rounded-md p-4">
            <div className="flex items-start gap-3">
              <svg className="w-5 h-5 text-im-danger flex-shrink-0 mt-0.5" fill="currentColor" viewBox="0 0 20 20">
                <path fillRule="evenodd" d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-7 4a1 1 0 11-2 0 1 1 0 012 0zm-1-9a1 1 0 00-1 1v4a1 1 0 102 0V6a1 1 0 00-1-1z" clipRule="evenodd" />
              </svg>
              <div className="flex-1">
                <h3 className="text-sm font-semibold text-im-danger">Error al cargar métricas</h3>
                <p className="text-sm text-im-danger mt-1">No se pudieron cargar las métricas de salud. Intenta nuevamente.</p>
              </div>
            </div>
          </div>
        </div>
      </Layout>
    );
  }

  // ========================================
  // MAIN RENDER
  // ========================================

  if (!dashboard) {
    return null;
  }

  return (
    <Layout
      title="Salud de Dispositivos"
      breadcrumbs={[
        { label: 'Salud' }
      ]}
    >
      {/* Page Header */}
      <div className="mb-6">
        <h1 className="font-montserrat text-3xl font-bold text-im-blue">Salud de Dispositivos</h1>
        <p className="text-im-neutral-500 mt-1">
          Monitoreo de métricas de salud en tiempo real
        </p>
      </div>

      {/* ========================================
          METRICS GRID
          ======================================== */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4 lg:gap-6 mb-8">
        <MetricCard
          label="Total Dispositivos"
          value={dashboard.total_devices}
          color="blue"
          icon={
            <svg className="w-6 h-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 3v2m6-2v2M9 19v2m6-2v2M5 9H3m2 6H3m18-6h-2m2 6h-2M7 19h10a2 2 0 002-2V7a2 2 0 00-2-2H7a2 2 0 00-2 2v10a2 2 0 002 2zM9 9h6v6H9V9z" />
            </svg>
          }
        />

        <MetricCard
          label="Online"
          value={dashboard.devices_online}
          color="success"
          icon={
            <svg className="w-6 h-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
            </svg>
          }
          subtitle={`${dashboard.total_devices > 0 ? Math.round((dashboard.devices_online / dashboard.total_devices) * 100) : 0}% del total`}
        />

        <MetricCard
          label="Offline"
          value={dashboard.devices_offline}
          color={dashboard.devices_offline > 0 ? 'danger' : 'neutral'}
          icon={
            <svg className="w-6 h-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
            </svg>
          }
        />

        <MetricCard
          label="Con Alertas"
          value={dashboard.devices_with_alerts}
          color={dashboard.devices_with_alerts > 0 ? 'warning' : 'neutral'}
          icon={
            <svg className="w-6 h-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 17h5l-1.405-1.405A2.032 2.032 0 0118 14.158V11a6.002 6.002 0 00-4-5.659V5a2 2 0 10-4 0v.341C7.67 6.165 6 8.388 6 11v3.159c0 .538-.214 1.055-.595 1.436L4 17h5m6 0v1a3 3 0 11-6 0v-1m6 0H9" />
            </svg>
          }
        />
      </div>

      {/* ========================================
          ADDITIONAL METRICS (WiFi)
          ======================================== */}
      {dashboard.avg_rssi !== null && (
        <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 lg:gap-6 mb-8">
          <IMCard>
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-im-neutral-500">RSSI Promedio</p>
                <p className="text-2xl font-bold text-im-neutral-900 mt-1">
                  {dashboard.avg_rssi.toFixed(1)} dBm
                </p>
              </div>
              <div className="p-3 rounded-md bg-im-blue/10 text-im-blue">
                <svg className="w-6 h-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8.111 16.404a5.5 5.5 0 017.778 0M12 20h.01m-7.08-7.071c3.904-3.905 10.236-3.905 14.141 0M1.394 9.393c5.857-5.857 15.355-5.857 21.213 0" />
                </svg>
              </div>
            </div>
          </IMCard>

          <IMCard>
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-im-neutral-500">Señal Débil</p>
                <p className="text-2xl font-bold text-im-neutral-900 mt-1">
                  {dashboard.devices_poor_signal} devices
                </p>
                {dashboard.total_devices > 0 && (
                  <p className="text-xs text-im-neutral-400 mt-1">
                    {Math.round((dashboard.devices_poor_signal / dashboard.total_devices) * 100)}% del total
                  </p>
                )}
              </div>
              <div className={`p-3 rounded-md ${dashboard.devices_poor_signal > 0 ? 'bg-im-warning/10 text-im-warning' : 'bg-im-neutral-100 text-im-neutral-500'}`}>
                <svg className="w-6 h-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
                </svg>
              </div>
            </div>
          </IMCard>
        </div>
      )}

      {/* ========================================
          DEVICES TABLE
          ======================================== */}
      <IMCard
        title="Dispositivos"
        subtitle={`${dashboard.devices.length} dispositivos monitoreados`}
        padding="none"
      >
        {dashboard.devices.length > 0 ? (
          <div className="overflow-x-auto">
            <table className="im-table">
              <thead>
                <tr>
                  <th>Dispositivo</th>
                  <th>Estado</th>
                  <th>WiFi</th>
                  <th className="hidden lg:table-cell">Uptime</th>
                  <th className="hidden xl:table-cell">Memoria</th>
                  <th>Batería</th>
                  <th className="hidden lg:table-cell">Readings 24h</th>
                  <th>Alertas</th>
                  <th className="hidden xl:table-cell">Última Actividad</th>
                </tr>
              </thead>
              <tbody>
                {dashboard.devices.map((device) => (
                  <DeviceRow key={device.device_id} device={device} />
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
                d="M9 3v2m6-2v2M9 19v2m6-2v2M5 9H3m2 6H3m18-6h-2m2 6h-2M7 19h10a2 2 0 002-2V7a2 2 0 00-2-2H7a2 2 0 00-2 2v10a2 2 0 002 2zM9 9h6v6H9V9z"
              />
            </svg>
            <h3 className="mt-4 text-sm font-semibold text-im-neutral-900">
              No hay dispositivos monitoreados
            </h3>
            <p className="mt-1 text-im-neutral-500">
              Agrega dispositivos para comenzar a monitorear su salud
            </p>
          </div>
        )}
      </IMCard>
    </Layout>
  );
}
