/**
 * Users Page - Gestión de usuarios del sistema
 *
 * Funcionalidades:
 * - Listar usuarios con filtros
 * - Crear nuevo usuario
 * - Editar usuario existente
 * - Activar/Desactivar usuarios
 * - Archivar/Desarchivar usuarios
 * - Resetear contraseñas
 * - Exportar a CSV
 */

import { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { Navigate } from 'react-router-dom';
import { Layout } from '@/components/layout/Layout';
import { IMCard, IMButton } from '@/components/common';
import { usePermissions } from '@/hooks/usePermissions';
import userService from '../services/userService';
import UserTable from '../components/users/UserTable';
import UserModal from '../components/users/UserModal';
import { User, UserCreate, UserUpdate } from '../types';

export default function Users() {
  const queryClient = useQueryClient();
  const { canManageUsers } = usePermissions();

  // Estado para filtros
  const [includeArchived, setIncludeArchived] = useState(false);
  const [roleFilter, setRoleFilter] = useState<string>('');
  const [activeFilter, setActiveFilter] = useState<boolean | undefined>(undefined);

  // Estado para modal
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [selectedUser, setSelectedUser] = useState<User | null>(null);
  const [modalMode, setModalMode] = useState<'create' | 'edit'>('create');

  // Query para obtener usuarios
  const { data: users = [], isLoading, error } = useQuery({
    queryKey: ['users', includeArchived, roleFilter, activeFilter],
    queryFn: () => userService.getUsers({
      include_archived: includeArchived,
      role: roleFilter || undefined,
      is_active: activeFilter,
    }),
  });

  // Query para estadísticas
  const { data: stats } = useQuery({
    queryKey: ['user-stats'],
    queryFn: () => userService.getUserStats(),
  });

  // Mutation para crear usuario
  const createMutation = useMutation({
    mutationFn: (userData: UserCreate) => userService.createUser(userData),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['users'] });
      queryClient.invalidateQueries({ queryKey: ['user-stats'] });
      setIsModalOpen(false);
      setSelectedUser(null);
    },
  });

  // Mutation para actualizar usuario
  const updateMutation = useMutation({
    mutationFn: ({ id, data }: { id: number; data: UserUpdate }) =>
      userService.updateUser(id, data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['users'] });
      queryClient.invalidateQueries({ queryKey: ['user-stats'] });
      setIsModalOpen(false);
      setSelectedUser(null);
    },
  });

  // Mutation para activar/desactivar
  const toggleActiveMutation = useMutation({
    mutationFn: ({ id, active }: { id: number; active: boolean }) =>
      active ? userService.activateUser(id) : userService.deactivateUser(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['users'] });
      queryClient.invalidateQueries({ queryKey: ['user-stats'] });
    },
  });

  // Mutation para archivar/desarchivar
  const toggleArchiveMutation = useMutation({
    mutationFn: ({ id, archived }: { id: number; archived: boolean }) =>
      archived ? userService.unarchiveUser(id) : userService.archiveUser(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['users'] });
      queryClient.invalidateQueries({ queryKey: ['user-stats'] });
    },
  });

  // Mutation para resetear password
  const resetPasswordMutation = useMutation({
    mutationFn: (id: number) => userService.resetUserPassword(id),
    onSuccess: (data) => {
      if (data.email_sent) {
        alert(`Contraseña blanqueada. Se envió una contraseña temporal a ${data.email}.`);
      } else if (data.temp_password) {
        // Fallback solo en desarrollo sin SMTP
        alert(`Contraseña temporal generada: ${data.temp_password}\n\nEl email no pudo enviarse; copia esta contraseña y entrégasela al usuario.`);
      } else {
        alert('Contraseña blanqueada, pero el email no pudo enviarse. Reintentá o revisá la configuración SMTP.');
      }
    },
  });

  // RBAC: Solo super_admin puede gestionar usuarios.
  // (El guard va DESPUÉS de los hooks: React exige que se llamen siempre
  // en el mismo orden; un return temprano acá arriba rompía esa regla.)
  if (!canManageUsers()) {
    return <Navigate to="/dashboard" replace />;
  }

  // Handlers
  const handleCreateUser = () => {
    setModalMode('create');
    setSelectedUser(null);
    setIsModalOpen(true);
  };

  const handleEditUser = (user: User) => {
    setModalMode('edit');
    setSelectedUser(user);
    setIsModalOpen(true);
  };

  const handleSaveUser = (userData: UserCreate | UserUpdate) => {
    if (modalMode === 'create') {
      createMutation.mutate(userData as UserCreate);
    } else if (selectedUser) {
      updateMutation.mutate({ id: selectedUser.id, data: userData as UserUpdate });
    }
  };

  const handleToggleActive = (user: User) => {
    if (confirm(`¿Estás seguro de ${user.is_active ? 'desactivar' : 'activar'} a ${user.first_name} ${user.last_name}?`)) {
      toggleActiveMutation.mutate({ id: user.id, active: !user.is_active });
    }
  };

  const handleToggleArchive = (user: User) => {
    if (confirm(`¿Estás seguro de ${user.archived ? 'desarchivar' : 'archivar'} a ${user.first_name} ${user.last_name}?`)) {
      toggleArchiveMutation.mutate({ id: user.id, archived: user.archived });
    }
  };

  const handleResetPassword = (user: User) => {
    if (confirm(`¿Generar una nueva contraseña temporal para ${user.first_name} ${user.last_name}?`)) {
      resetPasswordMutation.mutate(user.id);
    }
  };

  const handleExportCSV = () => {
    const csv = [
      // Header
      ['ID', 'Email', 'Nombre', 'Apellido', 'Rol', 'Activo', 'Archivado', 'Fecha Creación'].join(','),
      // Rows
      ...users.map(user => [
        user.id,
        user.email,
        user.first_name,
        user.last_name,
        user.role,
        user.is_active ? 'Sí' : 'No',
        user.archived ? 'Sí' : 'No',
        new Date(user.created_at).toLocaleDateString(),
      ].join(',')),
    ].join('\n');

    const blob = new Blob([csv], { type: 'text/csv;charset=utf-8;' });
    const link = document.createElement('a');
    link.href = URL.createObjectURL(blob);
    link.download = `usuarios_${new Date().toISOString().split('T')[0]}.csv`;
    link.click();
  };

  // Loading/Error states
  if (isLoading) {
    return (
      <Layout
        title="Usuarios"
        breadcrumbs={[{ label: 'Inicio', href: '/' }, { label: 'Usuarios' }]}
      >
        <div className="flex items-center justify-center h-[60vh]">
          <div className="text-center">
            <div className="inline-block w-16 h-16 border-4 border-im-neutral-100 border-t-im-orange rounded-full animate-spin"></div>
            <p className="mt-4 text-im-neutral-500 font-medium">Cargando usuarios...</p>
          </div>
        </div>
      </Layout>
    );
  }

  if (error) {
    return (
      <Layout
        title="Usuarios"
        breadcrumbs={[{ label: 'Inicio', href: '/' }, { label: 'Usuarios' }]}
      >
        <div className="max-w-2xl mx-auto mt-8">
          <div className="bg-im-danger-light border border-im-danger rounded-md p-4">
            <div className="flex items-start gap-3">
              <svg className="w-5 h-5 text-im-danger flex-shrink-0 mt-0.5" fill="currentColor" viewBox="0 0 20 20">
                <path fillRule="evenodd" d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-7 4a1 1 0 11-2 0 1 1 0 012 0zm-1-9a1 1 0 00-1 1v4a1 1 0 102 0V6a1 1 0 00-1-1z" clipRule="evenodd" />
              </svg>
              <div className="flex-1">
                <h3 className="text-sm font-semibold text-im-danger">Error al cargar usuarios</h3>
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
      title="Gestión de Usuarios"
      breadcrumbs={[{ label: 'Inicio', href: '/' }, { label: 'Usuarios' }]}
    >
      {/* Page Header */}
      <div className="mb-6">
        <h1 className="font-montserrat text-3xl font-bold text-im-blue">Gestión de Usuarios</h1>
        <p className="text-im-neutral-500 mt-1">Administra los usuarios del sistema</p>
      </div>

      {/* Stats Cards */}
      {stats && (
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4 lg:gap-6 mb-8">
          <IMCard hoverable className="hover-lift">
            <div className="flex items-start justify-between">
              <div className="flex-1">
                <p className="text-sm font-medium text-im-neutral-500 mb-1">Total Usuarios</p>
                <p className="text-3xl font-bold text-im-neutral-900">{stats.total}</p>
              </div>
              <div className="p-3 rounded-md text-im-blue bg-im-blue/10">
                <svg className="w-6 h-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 4.354a4 4 0 110 5.292M15 21H3v-1a6 6 0 0112 0v1zm0 0h6v-1a6 6 0 00-9-5.197M13 7a4 4 0 11-8 0 4 4 0 018 0z" />
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
                <p className="text-3xl font-bold text-im-warning">{stats.inactive}</p>
              </div>
              <div className="p-3 rounded-md text-im-warning bg-im-warning-light">
                <svg className="w-6 h-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M18.364 18.364A9 9 0 005.636 5.636m12.728 12.728A9 9 0 015.636 5.636m12.728 12.728L5.636 5.636" />
                </svg>
              </div>
            </div>
          </IMCard>
          <IMCard hoverable className="hover-lift">
            <div className="flex items-start justify-between">
              <div className="flex-1">
                <p className="text-sm font-medium text-im-neutral-500 mb-1">Archivados</p>
                <p className="text-3xl font-bold text-im-neutral-500">{stats.archived}</p>
              </div>
              <div className="p-3 rounded-md text-im-neutral-500 bg-im-neutral-100">
                <svg className="w-6 h-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 8h14M5 8a2 2 0 110-4h14a2 2 0 110 4M5 8v10a2 2 0 002 2h10a2 2 0 002-2V8m-9 4h4" />
                </svg>
              </div>
            </div>
          </IMCard>
        </div>
      )}

      {/* Filters and Actions */}
      <IMCard padding="md" className="mb-6">
        <div className="flex flex-wrap items-center gap-4">
          {/* Filtros */}
          <div className="flex items-center gap-2">
            <label className="flex items-center gap-2 cursor-pointer">
              <input
                type="checkbox"
                checked={includeArchived}
                onChange={(e) => setIncludeArchived(e.target.checked)}
                className="rounded border-im-neutral-300 text-im-orange focus:ring-im-orange"
              />
              <span className="text-sm text-im-neutral-700">Mostrar archivados</span>
            </label>
          </div>

          <div>
            <select
              value={roleFilter}
              onChange={(e) => setRoleFilter(e.target.value)}
              className="im-input text-sm"
            >
              <option value="">Todos los roles</option>
              <option value="super_admin">Super Admin</option>
              <option value="service_admin">Service Admin</option>
              <option value="technician">Técnico</option>
              <option value="guest">Invitado</option>
            </select>
          </div>

          <div>
            <select
              value={activeFilter === undefined ? '' : activeFilter.toString()}
              onChange={(e) => setActiveFilter(e.target.value === '' ? undefined : e.target.value === 'true')}
              className="im-input text-sm"
            >
              <option value="">Todos los estados</option>
              <option value="true">Activos</option>
              <option value="false">Inactivos</option>
            </select>
          </div>

          {/* Spacer */}
          <div className="flex-1"></div>

          {/* Actions */}
          <IMButton
            variant="secondary"
            size="sm"
            onClick={handleExportCSV}
          >
            Exportar CSV
          </IMButton>

          <IMButton
            variant="primary"
            size="sm"
            onClick={handleCreateUser}
          >
            + Nuevo Usuario
          </IMButton>
        </div>
      </IMCard>

      {/* Table */}
      <UserTable
        users={users}
        onEdit={handleEditUser}
        onToggleActive={handleToggleActive}
        onToggleArchive={handleToggleArchive}
        onResetPassword={handleResetPassword}
      />

      {/* Modal */}
      {isModalOpen && (
        <UserModal
          mode={modalMode}
          user={selectedUser}
          onSave={handleSaveUser}
          onClose={() => {
            setIsModalOpen(false);
            setSelectedUser(null);
          }}
          isLoading={createMutation.isPending || updateMutation.isPending}
        />
      )}
    </Layout>
  );
}
