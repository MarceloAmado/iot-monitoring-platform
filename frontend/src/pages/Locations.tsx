/**
 * Locations Page - Gestión de Grupos, Ubicaciones y Activos
 *
 * Tabs: Grupos | Ubicaciones | Activos
 * RBAC: super_admin y service_admin pueden crear/editar/eliminar
 */

import { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { Layout } from '@/components/layout/Layout';
import { IMCard, IMButton, IMModal, IMInput, IMBadge } from '@/components/common';
import locationService, {
  type LocationGroup,
  type Location,
  type Asset,
} from '@/services/locationService';

type Tab = 'groups' | 'locations' | 'assets';

export default function Locations() {
  const queryClient = useQueryClient();
  const [activeTab, setActiveTab] = useState<Tab>('groups');
  const [showModal, setShowModal] = useState(false);
  const [modalType, setModalType] = useState<'group' | 'location' | 'asset'>('group');
  const [editingId, setEditingId] = useState<number | null>(null);

  // Form state
  const [formData, setFormData] = useState<Record<string, string>>({});

  // Queries
  const { data: groups = [], isLoading: loadingGroups } = useQuery({
    queryKey: ['location-groups'],
    queryFn: locationService.getLocationGroups,
  });

  const { data: locations = [], isLoading: loadingLocations } = useQuery({
    queryKey: ['locations'],
    queryFn: () => locationService.getLocations(),
  });

  const { data: assets = [], isLoading: loadingAssets } = useQuery({
    queryKey: ['assets'],
    queryFn: () => locationService.getAssets(),
  });

  // Mutations
  const createGroupMutation = useMutation({
    mutationFn: locationService.createLocationGroup,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['location-groups'] });
      closeModal();
    },
  });

  const createLocationMutation = useMutation({
    mutationFn: locationService.createLocation,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['locations'] });
      closeModal();
    },
  });

  const createAssetMutation = useMutation({
    mutationFn: locationService.createAsset,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['assets'] });
      closeModal();
    },
  });

  const updateGroupMutation = useMutation({
    mutationFn: ({ id, data }: { id: number; data: Record<string, string | undefined> }) =>
      locationService.updateLocationGroup(id, data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['location-groups'] });
      closeModal();
    },
  });

  const updateLocationMutation = useMutation({
    mutationFn: ({ id, data }: { id: number; data: { location_group_id?: number; name?: string; code?: string; address?: string } }) =>
      locationService.updateLocation(id, data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['locations'] });
      closeModal();
    },
  });

  const updateAssetMutation = useMutation({
    mutationFn: ({ id, data }: { id: number; data: { location_id?: number; name?: string; type?: string; description?: string } }) =>
      locationService.updateAsset(id, data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['assets'] });
      closeModal();
    },
  });

  const deleteGroupMutation = useMutation({
    mutationFn: locationService.deleteLocationGroup,
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['location-groups'] }),
  });

  const deleteLocationMutation = useMutation({
    mutationFn: locationService.deleteLocation,
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['locations'] }),
  });

  const deleteAssetMutation = useMutation({
    mutationFn: locationService.deleteAsset,
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['assets'] }),
  });

  // Handlers
  const openCreate = (type: 'group' | 'location' | 'asset') => {
    setModalType(type);
    setEditingId(null);
    setFormData({});
    setShowModal(true);
  };

  const openEditGroup = (group: LocationGroup) => {
    setModalType('group');
    setEditingId(group.id);
    setFormData({
      name: group.name,
      description: group.description || '',
    });
    setShowModal(true);
  };

  const openEditLocation = (location: Location) => {
    setModalType('location');
    setEditingId(location.id);
    setFormData({
      location_group_id: String(location.location_group_id),
      name: location.name,
      code: location.code,
      address: location.address || '',
    });
    setShowModal(true);
  };

  const openEditAsset = (asset: Asset) => {
    setModalType('asset');
    setEditingId(asset.id);
    setFormData({
      location_id: String(asset.location_id),
      name: asset.name,
      type: asset.type,
      description: asset.description || '',
    });
    setShowModal(true);
  };

  const closeModal = () => {
    setShowModal(false);
    setEditingId(null);
    setFormData({});
  };

  const handleSubmit = () => {
    if (modalType === 'group') {
      const data = {
        name: formData.name || '',
        description: formData.description,
      };
      if (editingId) {
        updateGroupMutation.mutate({ id: editingId, data });
      } else {
        createGroupMutation.mutate(data);
      }
    } else if (modalType === 'location') {
      const data = {
        location_group_id: parseInt(formData.location_group_id || '0'),
        name: formData.name || '',
        code: formData.code || '',
        address: formData.address,
      };
      if (editingId) {
        updateLocationMutation.mutate({ id: editingId, data });
      } else {
        createLocationMutation.mutate(data);
      }
    } else if (modalType === 'asset') {
      const data = {
        location_id: parseInt(formData.location_id || '0'),
        name: formData.name || '',
        type: formData.type || '',
        description: formData.description,
      };
      if (editingId) {
        updateAssetMutation.mutate({ id: editingId, data });
      } else {
        createAssetMutation.mutate(data);
      }
    }
  };

  const isSubmitting =
    createGroupMutation.isPending ||
    createLocationMutation.isPending ||
    createAssetMutation.isPending ||
    updateGroupMutation.isPending ||
    updateLocationMutation.isPending ||
    updateAssetMutation.isPending;

  const tabs = [
    { id: 'groups' as Tab, label: 'Grupos', count: groups.length },
    { id: 'locations' as Tab, label: 'Ubicaciones', count: locations.length },
    { id: 'assets' as Tab, label: 'Activos', count: assets.length },
  ];

  return (
    <Layout title="Ubicaciones">
      <div className="space-y-6">
        {/* Header */}
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-2xl font-bold text-gray-900">Ubicaciones</h1>
            <p className="text-sm text-gray-500 mt-1">
              Gestiona grupos, ubicaciones y activos del sistema
            </p>
          </div>
          <IMButton
            onClick={() =>
              openCreate(
                activeTab === 'groups' ? 'group' : activeTab === 'locations' ? 'location' : 'asset'
              )
            }
          >
            + Crear{' '}
            {activeTab === 'groups' ? 'Grupo' : activeTab === 'locations' ? 'Ubicación' : 'Activo'}
          </IMButton>
        </div>

        {/* Tabs */}
        <div className="border-b border-gray-200">
          <nav className="flex space-x-8">
            {tabs.map((tab) => (
              <button
                key={tab.id}
                onClick={() => setActiveTab(tab.id)}
                className={`py-2 px-1 border-b-2 text-sm font-medium transition-colors ${
                  activeTab === tab.id
                    ? 'border-im-orange text-im-orange'
                    : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
                }`}
              >
                {tab.label}
                <span className="ml-2 bg-gray-100 text-gray-600 px-2 py-0.5 rounded-full text-xs">
                  {tab.count}
                </span>
              </button>
            ))}
          </nav>
        </div>

        {/* Content */}
        {activeTab === 'groups' && (
          <GroupsTable
            groups={groups}
            loading={loadingGroups}
            onEdit={openEditGroup}
            onDelete={(id) => deleteGroupMutation.mutate(id)}
          />
        )}
        {activeTab === 'locations' && (
          <LocationsTable
            locations={locations}
            groups={groups}
            loading={loadingLocations}
            onEdit={openEditLocation}
            onDelete={(id) => deleteLocationMutation.mutate(id)}
          />
        )}
        {activeTab === 'assets' && (
          <AssetsTable
            assets={assets}
            locations={locations}
            loading={loadingAssets}
            onEdit={openEditAsset}
            onDelete={(id) => deleteAssetMutation.mutate(id)}
          />
        )}

        {/* Create/Edit Modal */}
        <IMModal
          isOpen={showModal}
          onClose={closeModal}
          title={getModalTitle(modalType, editingId !== null)}
        >
          <div className="space-y-4">
            {modalType === 'group' && (
              <>
                <IMInput
                  label="Nombre"
                  value={formData.name || ''}
                  onChange={(e) => setFormData({ ...formData, name: e.target.value })}
                  placeholder="Ej: Hospital Central"
                />
                <IMInput
                  label="Descripción"
                  value={formData.description || ''}
                  onChange={(e) => setFormData({ ...formData, description: e.target.value })}
                  placeholder="Descripción del grupo"
                />
              </>
            )}
            {modalType === 'location' && (
              <>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">Grupo</label>
                  <select
                    className="w-full rounded-lg border border-gray-300 px-3 py-2 text-sm"
                    value={formData.location_group_id || ''}
                    onChange={(e) =>
                      setFormData({ ...formData, location_group_id: e.target.value })
                    }
                  >
                    <option value="">Seleccionar grupo...</option>
                    {groups.map((g) => (
                      <option key={g.id} value={g.id}>
                        {g.name}
                      </option>
                    ))}
                  </select>
                </div>
                <IMInput
                  label="Nombre"
                  value={formData.name || ''}
                  onChange={(e) => setFormData({ ...formData, name: e.target.value })}
                  placeholder="Ej: Laboratorio Principal"
                />
                <IMInput
                  label="Código"
                  value={formData.code || ''}
                  onChange={(e) => setFormData({ ...formData, code: e.target.value })}
                  placeholder="Ej: LAB-001"
                />
                <IMInput
                  label="Dirección"
                  value={formData.address || ''}
                  onChange={(e) => setFormData({ ...formData, address: e.target.value })}
                  placeholder="Dirección (opcional)"
                />
              </>
            )}
            {modalType === 'asset' && (
              <>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">Ubicación</label>
                  <select
                    className="w-full rounded-lg border border-gray-300 px-3 py-2 text-sm"
                    value={formData.location_id || ''}
                    onChange={(e) => setFormData({ ...formData, location_id: e.target.value })}
                  >
                    <option value="">Seleccionar ubicación...</option>
                    {locations.map((l) => (
                      <option key={l.id} value={l.id}>
                        {l.name} ({l.code})
                      </option>
                    ))}
                  </select>
                </div>
                <IMInput
                  label="Nombre"
                  value={formData.name || ''}
                  onChange={(e) => setFormData({ ...formData, name: e.target.value })}
                  placeholder="Ej: Heladera_Lab_001"
                />
                <IMInput
                  label="Tipo"
                  value={formData.type || ''}
                  onChange={(e) => setFormData({ ...formData, type: e.target.value })}
                  placeholder="Ej: refrigerator, incubator, freezer"
                />
                <IMInput
                  label="Descripción"
                  value={formData.description || ''}
                  onChange={(e) => setFormData({ ...formData, description: e.target.value })}
                  placeholder="Descripción (opcional)"
                />
              </>
            )}
            <div className="flex justify-end gap-3 pt-4">
              <IMButton variant="ghost" onClick={closeModal}>
                Cancelar
              </IMButton>
              <IMButton onClick={handleSubmit} loading={isSubmitting}>
                {editingId ? 'Guardar cambios' : 'Crear'}
              </IMButton>
            </div>
          </div>
        </IMModal>
      </div>
    </Layout>
  );
}

// ========================================
// Helper functions
// ========================================

function getModalTitle(type: 'group' | 'location' | 'asset', isEditing: boolean): string {
  switch (type) {
    case 'group':
      return isEditing ? 'Editar Grupo de Ubicaciones' : 'Nuevo Grupo de Ubicaciones';
    case 'location':
      return isEditing ? 'Editar Ubicación' : 'Nueva Ubicación';
    case 'asset':
      return isEditing ? 'Editar Activo' : 'Nuevo Activo';
  }
}

// ========================================
// Sub-components (Tables)
// ========================================

function GroupsTable({
  groups,
  loading,
  onEdit,
  onDelete,
}: {
  groups: LocationGroup[];
  loading: boolean;
  onEdit: (group: LocationGroup) => void;
  onDelete: (id: number) => void;
}) {
  if (loading) return <LoadingSkeleton />;
  if (groups.length === 0) return <EmptyState label="grupos" />;

  return (
    <IMCard>
      <div className="overflow-x-auto">
        <table className="w-full text-sm">
          <thead className="bg-gray-50 text-gray-600 uppercase text-xs">
            <tr>
              <th className="px-4 py-3 text-left">Nombre</th>
              <th className="px-4 py-3 text-left">Descripción</th>
              <th className="px-4 py-3 text-left">Creado</th>
              <th className="px-4 py-3 text-right">Acciones</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-gray-100">
            {groups.map((group) => (
              <tr key={group.id} className="hover:bg-gray-50">
                <td className="px-4 py-3 font-medium text-gray-900">{group.name}</td>
                <td className="px-4 py-3 text-gray-500">{group.description || '-'}</td>
                <td className="px-4 py-3 text-gray-500">
                  {new Date(group.created_at).toLocaleDateString()}
                </td>
                <td className="px-4 py-3 text-right">
                  <div className="inline-flex gap-2">
                    <IMButton variant="ghost" size="sm" onClick={() => onEdit(group)}>
                      Editar
                    </IMButton>
                    <IMButton variant="danger" size="sm" onClick={() => onDelete(group.id)}>
                      Eliminar
                    </IMButton>
                  </div>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </IMCard>
  );
}

function LocationsTable({
  locations,
  groups,
  loading,
  onEdit,
  onDelete,
}: {
  locations: Location[];
  groups: LocationGroup[];
  loading: boolean;
  onEdit: (location: Location) => void;
  onDelete: (id: number) => void;
}) {
  if (loading) return <LoadingSkeleton />;
  if (locations.length === 0) return <EmptyState label="ubicaciones" />;

  const groupMap = Object.fromEntries(groups.map((g) => [g.id, g.name]));

  return (
    <IMCard>
      <div className="overflow-x-auto">
        <table className="w-full text-sm">
          <thead className="bg-gray-50 text-gray-600 uppercase text-xs">
            <tr>
              <th className="px-4 py-3 text-left">Nombre</th>
              <th className="px-4 py-3 text-left">Código</th>
              <th className="px-4 py-3 text-left">Grupo</th>
              <th className="px-4 py-3 text-left">Dirección</th>
              <th className="px-4 py-3 text-right">Acciones</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-gray-100">
            {locations.map((loc) => (
              <tr key={loc.id} className="hover:bg-gray-50">
                <td className="px-4 py-3 font-medium text-gray-900">{loc.name}</td>
                <td className="px-4 py-3">
                  <IMBadge>{loc.code}</IMBadge>
                </td>
                <td className="px-4 py-3 text-gray-500">
                  {groupMap[loc.location_group_id] || '-'}
                </td>
                <td className="px-4 py-3 text-gray-500">{loc.address || '-'}</td>
                <td className="px-4 py-3 text-right">
                  <div className="inline-flex gap-2">
                    <IMButton variant="ghost" size="sm" onClick={() => onEdit(loc)}>
                      Editar
                    </IMButton>
                    <IMButton variant="danger" size="sm" onClick={() => onDelete(loc.id)}>
                      Eliminar
                    </IMButton>
                  </div>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </IMCard>
  );
}

function AssetsTable({
  assets,
  locations,
  loading,
  onEdit,
  onDelete,
}: {
  assets: Asset[];
  locations: Location[];
  loading: boolean;
  onEdit: (asset: Asset) => void;
  onDelete: (id: number) => void;
}) {
  if (loading) return <LoadingSkeleton />;
  if (assets.length === 0) return <EmptyState label="activos" />;

  const locationMap = Object.fromEntries(locations.map((l) => [l.id, l.name]));

  return (
    <IMCard>
      <div className="overflow-x-auto">
        <table className="w-full text-sm">
          <thead className="bg-gray-50 text-gray-600 uppercase text-xs">
            <tr>
              <th className="px-4 py-3 text-left">Nombre</th>
              <th className="px-4 py-3 text-left">Tipo</th>
              <th className="px-4 py-3 text-left">Ubicación</th>
              <th className="px-4 py-3 text-left">Descripción</th>
              <th className="px-4 py-3 text-right">Acciones</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-gray-100">
            {assets.map((asset) => (
              <tr key={asset.id} className="hover:bg-gray-50">
                <td className="px-4 py-3 font-medium text-gray-900">{asset.name}</td>
                <td className="px-4 py-3">
                  <IMBadge>{asset.type}</IMBadge>
                </td>
                <td className="px-4 py-3 text-gray-500">
                  {locationMap[asset.location_id] || '-'}
                </td>
                <td className="px-4 py-3 text-gray-500">{asset.description || '-'}</td>
                <td className="px-4 py-3 text-right">
                  <div className="inline-flex gap-2">
                    <IMButton variant="ghost" size="sm" onClick={() => onEdit(asset)}>
                      Editar
                    </IMButton>
                    <IMButton variant="danger" size="sm" onClick={() => onDelete(asset.id)}>
                      Eliminar
                    </IMButton>
                  </div>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </IMCard>
  );
}

function LoadingSkeleton() {
  return (
    <IMCard>
      <div className="animate-pulse space-y-3 p-4">
        {[...Array(5)].map((_, i) => (
          <div key={i} className="h-10 bg-gray-100 rounded" />
        ))}
      </div>
    </IMCard>
  );
}

function EmptyState({ label }: { label: string }) {
  return (
    <IMCard>
      <div className="text-center py-12 text-gray-500">
        <p className="text-lg">No hay {label} registrados</p>
        <p className="text-sm mt-1">Crea uno nuevo usando el botón de arriba</p>
      </div>
    </IMCard>
  );
}
