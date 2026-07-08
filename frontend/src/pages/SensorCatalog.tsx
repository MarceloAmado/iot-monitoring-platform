/**
 * SensorCatalog Page - Administración del catálogo de sensores
 *
 * Permite:
 * - Ver todos los sensores (built-in y custom)
 * - Filtrar por tipo, protocolo, estado
 * - Buscar sensores
 * - Crear nuevos sensores personalizados
 * - Editar sensores existentes (excepto built-in)
 * - Activar/Desactivar sensores
 * - Eliminar sensores custom (solo super_admin)
 * - Ver estadísticas del catálogo
 */

import { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { Layout } from '@/components/layout/Layout';
import { IMCard, IMButton } from '@/components/common';
import sensorService from '../services/sensorService';
import { SensorCatalog as SensorCatalogType } from '../types';
import SensorTable from '../components/sensors/SensorTable';
import SensorModal from '../components/sensors/SensorModal';

export default function SensorCatalog() {
  const queryClient = useQueryClient();

  // Estado local
  const [showModal, setShowModal] = useState(false);
  const [editingSensor, setEditingSensor] = useState<SensorCatalogType | null>(null);
  const [filters, setFilters] = useState({
    sensor_type: '',
    protocol: '',
    is_active: undefined as boolean | undefined,
    include_builtin: true,
    search: '',
  });

  // Queries
  const { data: sensors, isLoading, error } = useQuery({
    queryKey: ['sensors', filters],
    queryFn: () => sensorService.getSensors({
      ...filters,
      is_active: filters.is_active,
    }),
  });

  const { data: stats } = useQuery({
    queryKey: ['sensor-stats'],
    queryFn: () => sensorService.getSensorStats(),
  });

  // Mutations
  const activateMutation = useMutation({
    mutationFn: (sensorId: number) => sensorService.activateSensor(sensorId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['sensors'] });
      queryClient.invalidateQueries({ queryKey: ['sensor-stats'] });
    },
  });

  const deactivateMutation = useMutation({
    mutationFn: (sensorId: number) => sensorService.deactivateSensor(sensorId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['sensors'] });
      queryClient.invalidateQueries({ queryKey: ['sensor-stats'] });
    },
  });

  const deleteMutation = useMutation({
    mutationFn: (sensorId: number) => sensorService.deleteSensor(sensorId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['sensors'] });
      queryClient.invalidateQueries({ queryKey: ['sensor-stats'] });
    },
  });

  // Handlers
  const handleCreateNew = () => {
    setEditingSensor(null);
    setShowModal(true);
  };

  const handleEdit = (sensor: SensorCatalogType) => {
    setEditingSensor(sensor);
    setShowModal(true);
  };

  const handleActivate = async (sensor: SensorCatalogType) => {
    if (window.confirm(`¿Activar sensor "${sensor.name}"?`)) {
      try {
        await activateMutation.mutateAsync(sensor.id);
      } catch (error: any) {
        alert(`Error: ${error.response?.data?.detail || error.message}`);
      }
    }
  };

  const handleDeactivate = async (sensor: SensorCatalogType) => {
    if (window.confirm(`¿Desactivar sensor "${sensor.name}"?`)) {
      try {
        await deactivateMutation.mutateAsync(sensor.id);
      } catch (error: any) {
        alert(`Error: ${error.response?.data?.detail || error.message}`);
      }
    }
  };

  const handleDelete = async (sensor: SensorCatalogType) => {
    if (sensor.is_builtin) {
      alert('No se pueden eliminar sensores built-in');
      return;
    }

    if (window.confirm(`¿ELIMINAR sensor "${sensor.name}"? Esta acción no se puede deshacer.`)) {
      try {
        await deleteMutation.mutateAsync(sensor.id);
      } catch (error: any) {
        alert(`Error: ${error.response?.data?.detail || error.message}`);
      }
    }
  };

  const handleModalClose = () => {
    setShowModal(false);
    setEditingSensor(null);
  };

  const handleModalSuccess = () => {
    setShowModal(false);
    setEditingSensor(null);
    queryClient.invalidateQueries({ queryKey: ['sensors'] });
    queryClient.invalidateQueries({ queryKey: ['sensor-stats'] });
  };

  // Error state
  if (error) {
    return (
      <Layout
        title="Catálogo de Sensores"
        breadcrumbs={[{ label: 'Inicio', href: '/' }, { label: 'Catálogo de Sensores' }]}
      >
        <div className="max-w-2xl mx-auto mt-8">
          <div className="bg-im-danger-light border border-im-danger rounded-md p-4">
            <div className="flex items-start gap-3">
              <svg className="w-5 h-5 text-im-danger flex-shrink-0 mt-0.5" fill="currentColor" viewBox="0 0 20 20">
                <path fillRule="evenodd" d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-7 4a1 1 0 11-2 0 1 1 0 012 0zm-1-9a1 1 0 00-1 1v4a1 1 0 102 0V6a1 1 0 00-1-1z" clipRule="evenodd" />
              </svg>
              <div className="flex-1">
                <h3 className="text-sm font-semibold text-im-danger">Error al cargar sensores</h3>
                <p className="text-sm text-im-danger mt-1">{(error as Error).message}</p>
              </div>
            </div>
          </div>
        </div>
      </Layout>
    );
  }

  return (
    <Layout
      title="Catálogo de Sensores"
      breadcrumbs={[{ label: 'Inicio', href: '/' }, { label: 'Catálogo de Sensores' }]}
    >
      {/* Page Header */}
      <div className="flex justify-between items-start mb-6">
        <div>
          <h1 className="font-montserrat text-3xl font-bold text-im-blue">Catálogo de Sensores</h1>
          <p className="text-im-neutral-500 mt-1">
            Gestión de sensores built-in y personalizados
          </p>
        </div>
        <IMButton
          variant="primary"
          size="md"
          onClick={handleCreateNew}
        >
          + Nuevo Sensor
        </IMButton>
      </div>

      {/* Stats Cards */}
      {stats && (
        <div className="grid grid-cols-1 md:grid-cols-3 lg:grid-cols-5 gap-4 lg:gap-6 mb-8">
          <IMCard hoverable className="hover-lift">
            <div className="flex items-start justify-between">
              <div className="flex-1">
                <p className="text-sm font-medium text-im-neutral-500 mb-1">Total</p>
                <p className="text-3xl font-bold text-im-neutral-900">{stats.total}</p>
              </div>
              <div className="p-3 rounded-md text-im-blue bg-im-blue/10">
                <svg className="w-6 h-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 3v2m6-2v2M9 19v2m6-2v2M5 9H3m2 6H3m18-6h-2m2 6h-2M7 19h10a2 2 0 002-2V7a2 2 0 00-2-2H7a2 2 0 00-2 2v10a2 2 0 002 2zM9 9h6v6H9V9z" />
                </svg>
              </div>
            </div>
          </IMCard>

          <IMCard hoverable className="hover-lift">
            <div className="flex items-start justify-between">
              <div className="flex-1">
                <p className="text-sm font-medium text-im-neutral-500 mb-1">Activos</p>
                <p className="text-3xl font-bold text-im-success">{stats.active}</p>
              </div>
              <div className="p-3 rounded-md text-im-success bg-im-success-light">
                <svg className="w-6 h-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
                </svg>
              </div>
            </div>
          </IMCard>

          <IMCard hoverable className="hover-lift">
            <div className="flex items-start justify-between">
              <div className="flex-1">
                <p className="text-sm font-medium text-im-neutral-500 mb-1">Inactivos</p>
                <p className="text-3xl font-bold text-im-neutral-500">{stats.inactive}</p>
              </div>
              <div className="p-3 rounded-md text-im-neutral-500 bg-im-neutral-100">
                <svg className="w-6 h-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M18.364 18.364A9 9 0 005.636 5.636m12.728 12.728A9 9 0 015.636 5.636m12.728 12.728L5.636 5.636" />
                </svg>
              </div>
            </div>
          </IMCard>

          <IMCard hoverable className="hover-lift">
            <div className="flex items-start justify-between">
              <div className="flex-1">
                <p className="text-sm font-medium text-im-neutral-500 mb-1">Built-in</p>
                <p className="text-3xl font-bold text-im-blue">{stats.builtin}</p>
              </div>
              <div className="p-3 rounded-md text-im-blue bg-im-blue/10">
                <svg className="w-6 h-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 3v4M3 5h4M6 17v4m-2-2h4m5-16l2.286 6.857L21 12l-5.714 2.143L13 21l-2.286-6.857L5 12l5.714-2.143L13 3z" />
                </svg>
              </div>
            </div>
          </IMCard>

          <IMCard hoverable className="hover-lift">
            <div className="flex items-start justify-between">
              <div className="flex-1">
                <p className="text-sm font-medium text-im-neutral-500 mb-1">Personalizados</p>
                <p className="text-3xl font-bold text-im-orange">{stats.custom}</p>
              </div>
              <div className="p-3 rounded-md text-im-orange bg-im-orange/10">
                <svg className="w-6 h-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 6V4m0 2a2 2 0 100 4m0-4a2 2 0 110 4m-6 8a2 2 0 100-4m0 4a2 2 0 110-4m0 4v2m0-6V4m6 6v10m6-2a2 2 0 100-4m0 4a2 2 0 110-4m0 4v2m0-6V4" />
                </svg>
              </div>
            </div>
          </IMCard>
        </div>
      )}

      {/* Filtros */}
      <IMCard padding="md" className="mb-6">
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
          {/* Búsqueda */}
          <div>
            <label className="im-label">Buscar</label>
            <input
              type="text"
              placeholder="Nombre, modelo, fabricante..."
              value={filters.search}
              onChange={(e) => setFilters({ ...filters, search: e.target.value })}
              className="im-input"
            />
          </div>

          {/* Tipo de sensor */}
          <div>
            <label className="im-label">Tipo de Sensor</label>
            <select
              value={filters.sensor_type}
              onChange={(e) => setFilters({ ...filters, sensor_type: e.target.value })}
              className="im-input"
            >
              <option value="">Todos</option>
              {sensorService.getSensorTypes().map((type) => (
                <option key={type} value={type}>
                  {type}
                </option>
              ))}
            </select>
          </div>

          {/* Protocolo */}
          <div>
            <label className="im-label">Protocolo</label>
            <select
              value={filters.protocol}
              onChange={(e) => setFilters({ ...filters, protocol: e.target.value })}
              className="im-input"
            >
              <option value="">Todos</option>
              {sensorService.getProtocols().map((protocol) => (
                <option key={protocol} value={protocol}>
                  {protocol}
                </option>
              ))}
            </select>
          </div>

          {/* Estado */}
          <div>
            <label className="im-label">Estado</label>
            <select
              value={filters.is_active === undefined ? '' : filters.is_active.toString()}
              onChange={(e) =>
                setFilters({
                  ...filters,
                  is_active: e.target.value === '' ? undefined : e.target.value === 'true',
                })
              }
              className="im-input"
            >
              <option value="">Todos</option>
              <option value="true">Activos</option>
              <option value="false">Inactivos</option>
            </select>
          </div>
        </div>

        {/* Checkbox Built-in */}
        <div className="mt-4">
          <label className="flex items-center cursor-pointer">
            <input
              type="checkbox"
              checked={filters.include_builtin}
              onChange={(e) => setFilters({ ...filters, include_builtin: e.target.checked })}
              className="mr-2 h-4 w-4 rounded border-im-neutral-300 text-im-orange focus:ring-im-orange"
            />
            <span className="text-sm text-im-neutral-700">Incluir sensores built-in</span>
          </label>
        </div>
      </IMCard>

      {/* Tabla de sensores */}
      <IMCard padding="none">
        {isLoading ? (
          <div className="flex items-center justify-center py-16">
            <div className="text-center">
              <div className="inline-block w-12 h-12 border-4 border-im-neutral-100 border-t-im-orange rounded-full animate-spin"></div>
              <p className="mt-4 text-im-neutral-500 font-medium">Cargando sensores...</p>
            </div>
          </div>
        ) : !sensors || sensors.length === 0 ? (
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
              No se encontraron sensores
            </h3>
            <p className="mt-1 text-im-neutral-500">
              No hay sensores con los filtros aplicados
            </p>
            <div className="mt-6">
              <IMButton
                variant="primary"
                onClick={handleCreateNew}
              >
                + Crear Sensor Personalizado
              </IMButton>
            </div>
          </div>
        ) : (
          <SensorTable
            sensors={sensors}
            onEdit={handleEdit}
            onActivate={handleActivate}
            onDeactivate={handleDeactivate}
            onDelete={handleDelete}
          />
        )}
      </IMCard>

      {/* Modal de crear/editar */}
      {showModal && (
        <SensorModal
          sensor={editingSensor}
          onClose={handleModalClose}
          onSuccess={handleModalSuccess}
        />
      )}
    </Layout>
  );
}
