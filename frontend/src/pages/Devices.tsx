/**
 * Devices - IdeaMakers IoT Monitoring
 *
 * Listado completo de dispositivos con búsqueda y filtro por estado.
 * El nav lateral y los breadcrumbs de DeviceDetail apuntan a /devices.
 */

import React, { useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import { Link } from 'react-router-dom';
import { formatDistanceToNow } from 'date-fns';
import { es } from 'date-fns/locale';
import { Layout } from '@/components/layout/Layout';
import { IMCard, IMBadge, IMButton, IMInput, OnlineBadge, OfflineBadge } from '@/components/common';
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

const STATUS_FILTERS = [
  { value: 'all', label: 'Todos' },
  { value: 'active', label: 'Activos' },
  { value: 'inactive', label: 'Inactivos' },
  { value: 'maintenance', label: 'Mantenimiento' },
  { value: 'error', label: 'Error' },
];

// ========================================
// MAIN COMPONENT
// ========================================

export const Devices = () => {
  const { data: devices, isLoading, error } = useQuery<Device[]>({
    queryKey: ['devices'],
    queryFn: () => deviceService.getDevices(),
  });

  // WebSocket: auto-refresh cuando llegan nuevos readings o status updates
  useWebSocket({ dashboard: true });

  const { canCreateDevice } = usePermissions();

  const [isModalOpen, setIsModalOpen] = useState(false);
  const [search, setSearch] = useState('');
  const [statusFilter, setStatusFilter] = useState('all');

  // ========================================
  // FILTERED DEVICES
  // ========================================

  const filteredDevices = React.useMemo(() => {
    if (!devices) return [];

    const term = search.trim().toLowerCase();

    return devices.filter((device) => {
      if (statusFilter !== 'all' && device.status !== statusFilter) return false;
      if (!term) return true;
      return (
        device.name.toLowerCase().includes(term) ||
        device.device_eui.toLowerCase().includes(term)
      );
    });
  }, [devices, search, statusFilter]);

  // ========================================
  // LOADING STATE
  // ========================================

  if (isLoading) {
    return (
      <Layout title="Dispositivos">
        <div className="flex items-center justify-center h-[60vh]">
          <div className="text-center">
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
      <Layout title="Dispositivos">
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
      title="Dispositivos"
      breadcrumbs={[
        { label: 'Dashboard', href: '/dashboard' },
        { label: 'Dispositivos' },
      ]}
    >
      {/* Page Header */}
      <div className="mb-6">
        <h1 className="font-montserrat text-3xl font-bold text-im-blue">Dispositivos</h1>
        <p className="text-im-neutral-500 mt-1">
          Listado completo de dispositivos IoT registrados
        </p>
      </div>

      {/* ========================================
          FILTERS
          ======================================== */}
      <div className="flex flex-col sm:flex-row gap-3 mb-6">
        <div className="flex-1 max-w-md">
          <IMInput
            placeholder="Buscar por nombre o EUI..."
            value={search}
            onChange={(e) => setSearch(e.target.value)}
          />
        </div>
        <div className="flex gap-2 flex-wrap">
          {STATUS_FILTERS.map((filter) => (
            <IMButton
              key={filter.value}
              variant={statusFilter === filter.value ? 'primary' : 'ghost'}
              size="sm"
              onClick={() => setStatusFilter(filter.value)}
            >
              {filter.label}
            </IMButton>
          ))}
        </div>
      </div>

      {/* ========================================
          DEVICES TABLE
          ======================================== */}
      <IMCard
        title="Dispositivos"
        subtitle={`${filteredDevices.length} de ${devices?.length || 0} dispositivos`}
        actions={
          canCreateDevice() ? (
            <IMButton
              variant="primary"
              size="sm"
              onClick={() => setIsModalOpen(true)}
            >
              + Nuevo Dispositivo
            </IMButton>
          ) : null
        }
        padding="none"
      >
        {filteredDevices.length > 0 ? (
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
                {filteredDevices.map((device) => {
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
              {devices && devices.length > 0
                ? 'Sin resultados para los filtros aplicados'
                : 'No hay dispositivos registrados'}
            </h3>
            <p className="mt-1 text-im-neutral-500">
              {devices && devices.length > 0
                ? 'Probá con otro término de búsqueda o filtro de estado.'
                : canCreateDevice()
                  ? 'Comienza agregando tu primer dispositivo IoT'
                  : 'No tienes dispositivos asignados. Contacta al administrador.'}
            </p>
            {canCreateDevice() && (!devices || devices.length === 0) && (
              <div className="mt-6">
                <IMButton variant="primary" onClick={() => setIsModalOpen(true)}>
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
        onClose={() => setIsModalOpen(false)}
        device={null}
        onSuccess={() => {
          // La lista se actualiza por invalidación de query
        }}
      />
    </Layout>
  );
};

export default Devices;
