/**
 * Firmware Page - Gestión de versiones de firmware OTA
 *
 * Permite:
 * - Ver todas las versiones de firmware
 * - Filtrar por estabilidad
 * - Subir nuevas versiones (.bin)
 * - Editar metadata (notas, estabilidad, compatibilidad)
 * - Marcar una versión como "latest"
 * - Eliminar versiones
 */

import { useState, useRef } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { Layout } from '@/components/layout/Layout';
import { IMCard, IMButton, IMBadge, IMModal } from '@/components/common';
import firmwareService, { FirmwareVersion, FirmwareUploadData } from '../services/firmwareService';

function formatFileSize(bytes: number): string {
  if (bytes < 1024) return `${bytes} B`;
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
  return `${(bytes / (1024 * 1024)).toFixed(2)} MB`;
}

function formatDate(dateStr: string): string {
  return new Date(dateStr).toLocaleDateString('es-AR', {
    year: 'numeric',
    month: 'short',
    day: 'numeric',
    hour: '2-digit',
    minute: '2-digit',
  });
}

export default function Firmware() {
  const queryClient = useQueryClient();
  const fileInputRef = useRef<HTMLInputElement>(null);

  // Estado local
  const [onlyStable, setOnlyStable] = useState(false);
  const [showUploadModal, setShowUploadModal] = useState(false);
  const [editingFirmware, setEditingFirmware] = useState<FirmwareVersion | null>(null);
  const [uploadForm, setUploadForm] = useState({
    version: '',
    release_notes: '',
    is_stable: true,
    min_compatible_version: '',
    file: null as File | null,
  });
  const [editForm, setEditForm] = useState({
    release_notes: '',
    is_stable: true,
    min_compatible_version: '',
  });

  // Queries
  const { data: firmwares, isLoading, error } = useQuery({
    queryKey: ['firmware', onlyStable],
    queryFn: () => firmwareService.getVersions(onlyStable || undefined),
  });

  // Mutations
  const uploadMutation = useMutation({
    mutationFn: (data: FirmwareUploadData) => firmwareService.upload(data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['firmware'] });
      closeUploadModal();
    },
  });

  const updateMutation = useMutation({
    mutationFn: ({ id, data }: { id: number; data: Record<string, unknown> }) =>
      firmwareService.update(id, data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['firmware'] });
      setEditingFirmware(null);
    },
  });

  const deleteMutation = useMutation({
    mutationFn: (id: number) => firmwareService.delete(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['firmware'] });
    },
  });

  const markLatestMutation = useMutation({
    mutationFn: (id: number) => firmwareService.markAsLatest(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['firmware'] });
    },
  });

  // Handlers
  const closeUploadModal = () => {
    setShowUploadModal(false);
    setUploadForm({ version: '', release_notes: '', is_stable: true, min_compatible_version: '', file: null });
    if (fileInputRef.current) fileInputRef.current.value = '';
  };

  const handleUpload = async () => {
    if (!uploadForm.file || !uploadForm.version) {
      alert('Versión y archivo .bin son obligatorios');
      return;
    }
    try {
      await uploadMutation.mutateAsync({
        version: uploadForm.version,
        file: uploadForm.file,
        release_notes: uploadForm.release_notes || undefined,
        is_stable: uploadForm.is_stable,
        min_compatible_version: uploadForm.min_compatible_version || undefined,
      });
    } catch (error: any) {
      alert(`Error al subir firmware: ${error.response?.data?.detail || error.message}`);
    }
  };

  const handleEdit = (fw: FirmwareVersion) => {
    setEditingFirmware(fw);
    setEditForm({
      release_notes: fw.release_notes || '',
      is_stable: fw.is_stable,
      min_compatible_version: fw.min_compatible_version || '',
    });
  };

  const handleSaveEdit = async () => {
    if (!editingFirmware) return;
    try {
      await updateMutation.mutateAsync({
        id: editingFirmware.id,
        data: {
          release_notes: editForm.release_notes || null,
          is_stable: editForm.is_stable,
          min_compatible_version: editForm.min_compatible_version || null,
        },
      });
    } catch (error: any) {
      alert(`Error: ${error.response?.data?.detail || error.message}`);
    }
  };

  const handleDelete = async (fw: FirmwareVersion) => {
    if (window.confirm(`¿ELIMINAR firmware v${fw.version}? Esta acción no se puede deshacer.`)) {
      try {
        await deleteMutation.mutateAsync(fw.id);
      } catch (error: any) {
        alert(`Error: ${error.response?.data?.detail || error.message}`);
      }
    }
  };

  const handleMarkLatest = async (fw: FirmwareVersion) => {
    if (window.confirm(`¿Marcar v${fw.version} como versión más reciente?`)) {
      try {
        await markLatestMutation.mutateAsync(fw.id);
      } catch (error: any) {
        alert(`Error: ${error.response?.data?.detail || error.message}`);
      }
    }
  };

  // Stats
  const totalVersions = firmwares?.length ?? 0;
  const stableVersions = firmwares?.filter((f) => f.is_stable).length ?? 0;
  const latestVersion = firmwares?.find((f) => f.is_latest);

  // Error state
  if (error) {
    return (
      <Layout
        title="Firmware OTA"
        breadcrumbs={[{ label: 'Inicio', href: '/' }, { label: 'Firmware OTA' }]}
      >
        <div className="max-w-2xl mx-auto mt-8">
          <div className="bg-im-danger-light border border-im-danger rounded-md p-4">
            <div className="flex items-start gap-3">
              <svg className="w-5 h-5 text-im-danger flex-shrink-0 mt-0.5" fill="currentColor" viewBox="0 0 20 20">
                <path fillRule="evenodd" d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-7 4a1 1 0 11-2 0 1 1 0 012 0zm-1-9a1 1 0 00-1 1v4a1 1 0 102 0V6a1 1 0 00-1-1z" clipRule="evenodd" />
              </svg>
              <div className="flex-1">
                <h3 className="text-sm font-semibold text-im-danger">Error al cargar firmware</h3>
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
      title="Firmware OTA"
      breadcrumbs={[{ label: 'Inicio', href: '/' }, { label: 'Firmware OTA' }]}
    >
      {/* Page Header */}
      <div className="flex justify-between items-start mb-6">
        <div>
          <h1 className="font-montserrat text-3xl font-bold text-im-blue">Firmware OTA</h1>
          <p className="text-im-neutral-500 mt-1">
            Gestión de versiones de firmware para dispositivos ESP32
          </p>
        </div>
        <IMButton variant="primary" size="md" onClick={() => setShowUploadModal(true)}>
          + Subir Firmware
        </IMButton>
      </div>

      {/* Stats Cards */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4 lg:gap-6 mb-8">
        <IMCard hoverable className="hover-lift">
          <div className="flex items-start justify-between">
            <div className="flex-1">
              <p className="text-sm font-medium text-im-neutral-500 mb-1">Total Versiones</p>
              <p className="text-3xl font-bold text-im-neutral-900">{totalVersions}</p>
            </div>
            <div className="p-3 rounded-md text-im-blue bg-im-blue/10">
              <svg className="w-6 h-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-8l-4-4m0 0L8 8m4-4v12" />
              </svg>
            </div>
          </div>
        </IMCard>

        <IMCard hoverable className="hover-lift">
          <div className="flex items-start justify-between">
            <div className="flex-1">
              <p className="text-sm font-medium text-im-neutral-500 mb-1">Estables</p>
              <p className="text-3xl font-bold text-im-success">{stableVersions}</p>
            </div>
            <div className="p-3 rounded-md text-im-success bg-im-success-light">
              <svg className="w-6 h-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m5.618-4.016A11.955 11.955 0 0112 2.944a11.955 11.955 0 01-8.618 3.04A12.02 12.02 0 003 9c0 5.591 3.824 10.29 9 11.622 5.176-1.332 9-6.03 9-11.622 0-1.042-.133-2.052-.382-3.016z" />
              </svg>
            </div>
          </div>
        </IMCard>

        <IMCard hoverable className="hover-lift">
          <div className="flex items-start justify-between">
            <div className="flex-1">
              <p className="text-sm font-medium text-im-neutral-500 mb-1">Versión Actual</p>
              <p className="text-3xl font-bold text-im-orange">
                {latestVersion ? `v${latestVersion.version}` : 'N/A'}
              </p>
            </div>
            <div className="p-3 rounded-md text-im-orange bg-im-orange/10">
              <svg className="w-6 h-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 10V3L4 14h7v7l9-11h-7z" />
              </svg>
            </div>
          </div>
        </IMCard>
      </div>

      {/* Filtro */}
      <IMCard padding="md" className="mb-6">
        <label className="flex items-center cursor-pointer">
          <input
            type="checkbox"
            checked={onlyStable}
            onChange={(e) => setOnlyStable(e.target.checked)}
            className="mr-2 h-4 w-4 rounded border-im-neutral-300 text-im-orange focus:ring-im-orange"
          />
          <span className="text-sm text-im-neutral-700">Mostrar solo versiones estables</span>
        </label>
      </IMCard>

      {/* Tabla */}
      <IMCard padding="none">
        {isLoading ? (
          <div className="flex items-center justify-center py-16">
            <div className="text-center">
              <div className="inline-block w-12 h-12 border-4 border-im-neutral-100 border-t-im-orange rounded-full animate-spin"></div>
              <p className="mt-4 text-im-neutral-500 font-medium">Cargando firmware...</p>
            </div>
          </div>
        ) : !firmwares || firmwares.length === 0 ? (
          <div className="py-16 text-center">
            <svg className="mx-auto h-12 w-12 text-im-neutral-300" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1} d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-8l-4-4m0 0L8 8m4-4v12" />
            </svg>
            <h3 className="mt-4 text-sm font-semibold text-im-neutral-900">
              No hay versiones de firmware
            </h3>
            <p className="mt-1 text-im-neutral-500">
              Sube la primera versión para comenzar
            </p>
            <div className="mt-6">
              <IMButton variant="primary" onClick={() => setShowUploadModal(true)}>
                + Subir Firmware
              </IMButton>
            </div>
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="min-w-full divide-y divide-im-neutral-200">
              <thead className="bg-im-neutral-50">
                <tr>
                  <th className="px-6 py-3 text-left text-xs font-medium text-im-neutral-500 uppercase tracking-wider">Versión</th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-im-neutral-500 uppercase tracking-wider">Estado</th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-im-neutral-500 uppercase tracking-wider">Tamaño</th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-im-neutral-500 uppercase tracking-wider">MD5</th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-im-neutral-500 uppercase tracking-wider">Min. Compatible</th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-im-neutral-500 uppercase tracking-wider">Fecha</th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-im-neutral-500 uppercase tracking-wider">Notas</th>
                  <th className="px-6 py-3 text-right text-xs font-medium text-im-neutral-500 uppercase tracking-wider">Acciones</th>
                </tr>
              </thead>
              <tbody className="bg-white divide-y divide-im-neutral-200">
                {firmwares.map((fw) => (
                  <tr key={fw.id} className="hover:bg-im-neutral-50 transition-colors">
                    <td className="px-6 py-4 whitespace-nowrap">
                      <span className="text-sm font-semibold text-im-neutral-900">v{fw.version}</span>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap">
                      <div className="flex gap-1.5">
                        {fw.is_latest && (
                          <IMBadge variant="primary" size="sm">Latest</IMBadge>
                        )}
                        {fw.is_stable ? (
                          <IMBadge variant="success" size="sm">Estable</IMBadge>
                        ) : (
                          <IMBadge variant="warning" size="sm">Beta</IMBadge>
                        )}
                      </div>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-im-neutral-600">
                      {formatFileSize(fw.file_size_bytes)}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap">
                      <code className="text-xs text-im-neutral-500 font-mono">
                        {fw.md5_checksum.substring(0, 12)}...
                      </code>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-im-neutral-600">
                      {fw.min_compatible_version || '-'}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-im-neutral-500">
                      {formatDate(fw.created_at)}
                    </td>
                    <td className="px-6 py-4 text-sm text-im-neutral-600 max-w-xs truncate">
                      {fw.release_notes || '-'}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-right">
                      <div className="flex justify-end gap-2">
                        {!fw.is_latest && (
                          <IMButton
                            variant="ghost"
                            size="sm"
                            onClick={() => handleMarkLatest(fw)}
                            loading={markLatestMutation.isPending}
                          >
                            Latest
                          </IMButton>
                        )}
                        <IMButton variant="secondary" size="sm" onClick={() => handleEdit(fw)}>
                          Editar
                        </IMButton>
                        <IMButton
                          variant="danger"
                          size="sm"
                          onClick={() => handleDelete(fw)}
                          loading={deleteMutation.isPending}
                        >
                          Eliminar
                        </IMButton>
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </IMCard>

      {/* Upload Modal */}
      <IMModal
        isOpen={showUploadModal}
        onClose={closeUploadModal}
        title="Subir Firmware"
        subtitle="Sube un archivo .bin compilado para ESP32"
        size="md"
        footer={
          <div className="flex justify-end gap-3">
            <IMButton variant="secondary" onClick={closeUploadModal}>
              Cancelar
            </IMButton>
            <IMButton
              variant="primary"
              onClick={handleUpload}
              loading={uploadMutation.isPending}
              disabled={!uploadForm.file || !uploadForm.version}
            >
              Subir Firmware
            </IMButton>
          </div>
        }
      >
        <div className="space-y-4">
          <div>
            <label className="im-label">Versión *</label>
            <input
              type="text"
              placeholder="1.0.0"
              value={uploadForm.version}
              onChange={(e) => setUploadForm({ ...uploadForm, version: e.target.value })}
              className="im-input"
            />
            <p className="im-helper-text mt-1">Formato semver (ej: 1.2.3, 2.0.0-beta)</p>
          </div>

          <div>
            <label className="im-label">Archivo .bin *</label>
            <input
              ref={fileInputRef}
              type="file"
              accept=".bin"
              onChange={(e) => setUploadForm({ ...uploadForm, file: e.target.files?.[0] || null })}
              className="im-input file:mr-4 file:py-1 file:px-3 file:rounded-md file:border-0 file:text-sm file:font-medium file:bg-im-orange/10 file:text-im-orange hover:file:bg-im-orange/20"
            />
            {uploadForm.file && (
              <p className="im-helper-text mt-1">
                {uploadForm.file.name} ({formatFileSize(uploadForm.file.size)})
              </p>
            )}
          </div>

          <div>
            <label className="im-label">Notas de Release</label>
            <textarea
              placeholder="Cambios en esta versión..."
              value={uploadForm.release_notes}
              onChange={(e) => setUploadForm({ ...uploadForm, release_notes: e.target.value })}
              className="im-input"
              rows={3}
            />
          </div>

          <div>
            <label className="im-label">Versión Mínima Compatible</label>
            <input
              type="text"
              placeholder="0.0.0 (opcional)"
              value={uploadForm.min_compatible_version}
              onChange={(e) => setUploadForm({ ...uploadForm, min_compatible_version: e.target.value })}
              className="im-input"
            />
            <p className="im-helper-text mt-1">Versión mínima de firmware desde la cual se puede actualizar</p>
          </div>

          <div>
            <label className="flex items-center cursor-pointer">
              <input
                type="checkbox"
                checked={uploadForm.is_stable}
                onChange={(e) => setUploadForm({ ...uploadForm, is_stable: e.target.checked })}
                className="mr-2 h-4 w-4 rounded border-im-neutral-300 text-im-orange focus:ring-im-orange"
              />
              <span className="text-sm text-im-neutral-700">Versión estable</span>
            </label>
          </div>
        </div>
      </IMModal>

      {/* Edit Modal */}
      <IMModal
        isOpen={editingFirmware !== null}
        onClose={() => setEditingFirmware(null)}
        title={`Editar v${editingFirmware?.version ?? ''}`}
        subtitle="Modificar metadata del firmware"
        size="md"
        footer={
          <div className="flex justify-end gap-3">
            <IMButton variant="secondary" onClick={() => setEditingFirmware(null)}>
              Cancelar
            </IMButton>
            <IMButton
              variant="primary"
              onClick={handleSaveEdit}
              loading={updateMutation.isPending}
            >
              Guardar
            </IMButton>
          </div>
        }
      >
        <div className="space-y-4">
          <div>
            <label className="im-label">Notas de Release</label>
            <textarea
              value={editForm.release_notes}
              onChange={(e) => setEditForm({ ...editForm, release_notes: e.target.value })}
              className="im-input"
              rows={3}
            />
          </div>

          <div>
            <label className="im-label">Versión Mínima Compatible</label>
            <input
              type="text"
              placeholder="0.0.0 (opcional)"
              value={editForm.min_compatible_version}
              onChange={(e) => setEditForm({ ...editForm, min_compatible_version: e.target.value })}
              className="im-input"
            />
          </div>

          <div>
            <label className="flex items-center cursor-pointer">
              <input
                type="checkbox"
                checked={editForm.is_stable}
                onChange={(e) => setEditForm({ ...editForm, is_stable: e.target.checked })}
                className="mr-2 h-4 w-4 rounded border-im-neutral-300 text-im-orange focus:ring-im-orange"
              />
              <span className="text-sm text-im-neutral-700">Versión estable</span>
            </label>
          </div>
        </div>
      </IMModal>
    </Layout>
  );
}
