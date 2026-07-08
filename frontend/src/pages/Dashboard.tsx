/**
 * Dashboard - IdeaMakers IoT Monitoring
 *
 * Vista principal con métricas, widgets y lista de dispositivos
 * Grid responsive: 1 col (mobile) → 2 cols (tablet) → 4 cols (desktop)
 */

import React, { useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import { Link } from 'react-router-dom';
import { formatDistanceToNow } from 'date-fns';
import { es } from 'date-fns/locale';
import { Layout } from '@/components/layout/Layout';
import { IMCard, IMBadge, IMButton, OnlineBadge, OfflineBadge } from '@/components/common';
import { DeviceFormModal } from '@/components/devices/DeviceFormModal';
import { usePermissions } from '@/hooks/usePermissions';
import { useWebSocket } from '@/hooks/useWebSocket';
import deviceService from '@/services/deviceService';
import type { Device } from '@/types';

// ========================================
// HELPER FUNCTIONS
// ========================================

const isOnline = (lastSeenAt: string | null): boolean => {
  if (!lastSeenAt) return false;
  const lastSeen = new Date(lastSeenAt);
  const now = new Date();
  const diffMinutes = (now.getTime() - lastSeen.getTime()) / (1000 * 60);
  return diffMinutes < 10; // Online si visto hace menos de 10 minutos
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

// ========================================
// METRIC CARD COMPONENT
// ========================================

interface MetricCardProps {
  label: string;
  value: number | string;
  color: 'blue' | 'success' | 'danger' | 'warning';
  icon: React.ReactNode;
  trend?: { value: string; isUp: boolean };
}

const MetricCard: React.FC<MetricCardProps> = ({ label, value, color, icon, trend }) => {
  const colorStyles = {
    blue: 'text-im-blue bg-im-blue/10',
    success: 'text-im-success bg-im-success-light',
    danger: 'text-im-danger bg-im-danger-light',
    warning: 'text-im-warning bg-im-warning-light',
  };

  return (
    <IMCard hoverable className="hover-lift">
      <div className="flex items-start justify-between">
        <div className="flex-1">
          <p className="text-sm font-medium text-im-neutral-500 mb-1">{label}</p>
          <p className="text-3xl font-bold text-im-neutral-900">{value}</p>

          {trend && (
            <div className={`flex items-center gap-1 mt-2 text-xs font-medium ${trend.isUp ? 'text-im-success' : 'text-im-danger'}`}>
              <svg className="w-4 h-4" fill="currentColor" viewBox="0 0 20 20">
                {trend.isUp ? (
                  <path fillRule="evenodd" d="M5.293 9.707a1 1 0 010-1.414l4-4a1 1 0 011.414 0l4 4a1 1 0 01-1.414 1.414L11 7.414V15a1 1 0 11-2 0V7.414L6.707 9.707a1 1 0 01-1.414 0z" clipRule="evenodd" />
                ) : (
                  <path fillRule="evenodd" d="M14.707 10.293a1 1 0 010 1.414l-4 4a1 1 0 01-1.414 0l-4-4a1 1 0 111.414-1.414L9 12.586V5a1 1 0 012 0v7.586l2.293-2.293a1 1 0 011.414 0z" clipRule="evenodd" />
                )}
              </svg>
              <span>{trend.value}</span>
            </div>
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
// MAIN COMPONENT
// ========================================

export const Dashboard = () => {
  const { data: devices, isLoading, error } = useQuery<Device[]>({
    queryKey: ['devices'],
    queryFn: () => deviceService.getDevices(),
  });

  // WebSocket: auto-refresh cuando llegan nuevos readings o status updates
  useWebSocket({ dashboard: true });

  // ========================================
  // PERMISSIONS
  // ========================================

  const { canCreateDevice } = usePermissions();

  // ========================================
  // STATE
  // ========================================

  const [isModalOpen, setIsModalOpen] = useState(false);

  // ========================================
  // HANDLERS
  // ========================================

  const handleNewDevice = () => {
    setIsModalOpen(true);
  };

  const handleCloseModal = () => {
    setIsModalOpen(false);
  };

  // ========================================
  // METRICS CALCULATION
  // ========================================

  const metrics = React.useMemo(() => {
    if (!devices) {
      return {
        total: 0,
        online: 0,
        offline: 0,
        maintenance: 0,
      };
    }

    return {
      total: devices.length,
      online: devices.filter((d) => isOnline(d.last_seen_at)).length,
      offline: devices.filter((d) => !isOnline(d.last_seen_at)).length,
      maintenance: devices.filter((d) => d.status === 'maintenance').length,
    };
  }, [devices]);

  // ========================================
  // LOADING STATE
  // ========================================

  if (isLoading) {
    return (
      <Layout title="Dashboard">
        <div className="flex items-center justify-center h-[60vh]">
          <div className="text-center">
            {/* Spinner */}
            <div className="inline-block w-16 h-16 border-4 border-im-neutral-100 border-t-im-orange rounded-full animate-spin"></div>
            <p className="mt-4 text-im-neutral-500 font-medium">Cargando dispositivos...</p>
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
      <Layout title="Dashboard">
        <div className="max-w-2xl mx-auto mt-8">
          <div className="bg-im-danger-light border border-im-danger rounded-md p-4">
            <div className="flex items-start gap-3">
              <svg className="w-5 h-5 text-im-danger flex-shrink-0 mt-0.5" fill="currentColor" viewBox="0 0 20 20">
                <path fillRule="evenodd" d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-7 4a1 1 0 11-2 0 1 1 0 012 0zm-1-9a1 1 0 00-1 1v4a1 1 0 102 0V6a1 1 0 00-1-1z" clipRule="evenodd" />
              </svg>
              <div className="flex-1">
                <h3 className="text-sm font-semibold text-im-danger">Error al cargar dispositivos</h3>
                <p className="text-sm text-im-danger mt-1">No se pudieron cargar los dispositivos. Intenta nuevamente.</p>
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

  return (
    <Layout
      title="Dashboard"
      breadcrumbs={[
        { label: 'Dashboard' }
      ]}
    >
      {/* Page Header */}
      <div className="mb-6">
        <h1 className="font-montserrat text-3xl font-bold text-im-blue">Dashboard</h1>
        <p className="text-im-neutral-500 mt-1">
          Monitoreo de dispositivos IoT en tiempo real
        </p>
      </div>

      {/* ========================================
          METRICS GRID
          ======================================== */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4 lg:gap-6 mb-8">
        <MetricCard
          label="Total Dispositivos"
          value={metrics.total}
          color="blue"
          icon={
            <svg className="w-6 h-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 3v2m6-2v2M9 19v2m6-2v2M5 9H3m2 6H3m18-6h-2m2 6h-2M7 19h10a2 2 0 002-2V7a2 2 0 00-2-2H7a2 2 0 00-2 2v10a2 2 0 002 2zM9 9h6v6H9V9z" />
            </svg>
          }
        />

        <MetricCard
          label="En Línea"
          value={metrics.online}
          color="success"
          icon={
            <svg className="w-6 h-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
            </svg>
          }
          trend={metrics.total > 0 ? { value: `${Math.round((metrics.online / metrics.total) * 100)}%`, isUp: metrics.online > metrics.offline } : undefined}
        />

        <MetricCard
          label="Fuera de Línea"
          value={metrics.offline}
          color="danger"
          icon={
            <svg className="w-6 h-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
            </svg>
          }
        />

        <MetricCard
          label="Mantenimiento"
          value={metrics.maintenance}
          color="warning"
          icon={
            <svg className="w-6 h-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10.325 4.317c.426-1.756 2.924-1.756 3.35 0a1.724 1.724 0 002.573 1.066c1.543-.94 3.31.826 2.37 2.37a1.724 1.724 0 001.065 2.572c1.756.426 1.756 2.924 0 3.35a1.724 1.724 0 00-1.066 2.573c.94 1.543-.826 3.31-2.37 2.37a1.724 1.724 0 00-2.572 1.065c-.426 1.756-2.924 1.756-3.35 0a1.724 1.724 0 00-2.573-1.066c-1.543.94-3.31-.826-2.37-2.37a1.724 1.724 0 00-1.065-2.572c-1.756-.426-1.756-2.924 0-3.35a1.724 1.724 0 001.066-2.573c-.94-1.543.826-3.31 2.37-2.37.996.608 2.296.07 2.572-1.065z" />
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" />
            </svg>
          }
        />
      </div>

      {/* ========================================
          DEVICES TABLE
          ======================================== */}
      <IMCard
        title="Dispositivos"
        subtitle={`${devices?.length || 0} dispositivos registrados`}
        actions={
          canCreateDevice() ? (
            <IMButton
              variant="primary"
              size="sm"
              onClick={handleNewDevice}
            >
              + Nuevo Dispositivo
            </IMButton>
          ) : null
        }
        padding="none"
      >
        {devices && devices.length > 0 ? (
          <div className="overflow-x-auto">
            <table className="im-table">
              <thead>
                <tr>
                  <th>Dispositivo</th>
                  <th>EUI</th>
                  <th>Estado</th>
                  <th>Conexión</th>
                  <th className="hidden lg:table-cell">Última Actividad</th>
                  <th className="text-right">Acciones</th>
                </tr>
              </thead>
              <tbody>
                {devices.map((device) => {
                  const online = isOnline(device.last_seen_at);
                  const statusInfo = getStatusBadge(device.status);

                  return (
                    <tr key={device.id}>
                      {/* Device Info */}
                      <td>
                        <div>
                          <div className="font-semibold text-im-neutral-900">
                            {device.name}
                          </div>
                          {device.firmware_version && (
                            <div className="text-xs text-im-neutral-500 mt-0.5">
                              Firmware v{device.firmware_version}
                            </div>
                          )}
                        </div>
                      </td>

                      {/* EUI */}
                      <td>
                        <code className="text-xs bg-im-neutral-100 px-2 py-1 rounded text-im-neutral-700">
                          {device.device_eui}
                        </code>
                      </td>

                      {/* Status */}
                      <td>
                        <IMBadge variant={statusInfo.variant} size="sm">
                          {statusInfo.label}
                        </IMBadge>
                      </td>

                      {/* Online/Offline */}
                      <td>
                        {online ? (
                          <OnlineBadge size="sm" />
                        ) : (
                          <OfflineBadge size="sm" />
                        )}
                      </td>

                      {/* Last Seen (hidden on mobile) */}
                      <td className="hidden lg:table-cell">
                        {device.last_seen_at ? (
                          <span className="text-im-neutral-500">
                            {formatDistanceToNow(new Date(device.last_seen_at), {
                              addSuffix: true,
                              locale: es,
                            })}
                          </span>
                        ) : (
                          <span className="text-im-neutral-400">Nunca</span>
                        )}
                      </td>

                      {/* Actions */}
                      <td className="text-right">
                        <Link to={`/devices/${device.id}`}>
                          <IMButton variant="ghost" size="sm">
                            Ver detalles →
                          </IMButton>
                        </Link>
                      </td>
                    </tr>
                  );
                })}
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
              No hay dispositivos registrados
            </h3>
            <p className="mt-1 text-im-neutral-500">
              {canCreateDevice()
                ? 'Comienza agregando tu primer dispositivo IoT'
                : 'No tienes dispositivos asignados. Contacta al administrador.'}
            </p>
            {canCreateDevice() && (
              <div className="mt-6">
                <IMButton
                  variant="primary"
                  onClick={handleNewDevice}
                >
                  + Agregar Dispositivo
                </IMButton>
              </div>
            )}
          </div>
        )}
      </IMCard>

      {/* ========================================
          DEVICE FORM MODAL
          ======================================== */}
      <DeviceFormModal
        isOpen={isModalOpen}
        onClose={handleCloseModal}
        device={null}
        onSuccess={() => {
          // Modal se cerrará automáticamente
          // La lista de devices se actualizará automáticamente por invalidación de query
        }}
      />
    </Layout>
  );
};

export default Dashboard;
