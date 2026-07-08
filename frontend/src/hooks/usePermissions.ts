/**
 * Hook personalizado para verificar permisos basados en roles.
 */

import { useAuth } from './useAuth';

type UserRole = 'super_admin' | 'service_admin' | 'technician' | 'guest';

export const usePermissions = () => {
  const { user } = useAuth();

  /**
   * Verifica si el usuario tiene uno de los roles especificados
   */
  const hasRole = (roles: UserRole | UserRole[]): boolean => {
    if (!user) return false;

    const roleArray = Array.isArray(roles) ? roles : [roles];
    return roleArray.includes(user.role);
  };

  /**
   * Verifica si el usuario es super admin
   */
  const isSuperAdmin = (): boolean => {
    return user?.role === 'super_admin';
  };

  /**
   * Verifica si el usuario es admin (super_admin o service_admin)
   */
  const isAdmin = (): boolean => {
    return user?.role === 'super_admin' || user?.role === 'service_admin';
  };

  /**
   * Verifica si el usuario es técnico
   */
  const isTechnician = (): boolean => {
    return user?.role === 'technician';
  };

  /**
   * Verifica si el usuario es invitado
   */
  const isGuest = (): boolean => {
    return user?.role === 'guest';
  };

  /**
   * Verifica si el usuario puede crear/editar/eliminar
   */
  const canWrite = (): boolean => {
    return isAdmin();
  };

  /**
   * Verifica si el usuario puede solo leer
   */
  const canOnlyRead = (): boolean => {
    return isTechnician() || isGuest();
  };

  /**
   * Verifica si el usuario tiene acceso a una location específica
   */
  const canAccessLocation = (locationId: number): boolean => {
    if (!user) return false;

    // Super admin tiene acceso a todo
    if (user.role === 'super_admin') return true;

    // Otros roles: verificar allowed_location_ids
    if (!user.allowed_location_ids || user.allowed_location_ids.length === 0) {
      return false;
    }

    return user.allowed_location_ids.includes(locationId);
  };

  /**
   * Verifica si el usuario puede crear devices
   */
  const canCreateDevice = (): boolean => {
    return isAdmin();
  };

  /**
   * Verifica si el usuario puede editar devices
   */
  const canEditDevice = (): boolean => {
    return isAdmin();
  };

  /**
   * Verifica si el usuario puede eliminar devices
   */
  const canDeleteDevice = (): boolean => {
    return isAdmin();
  };

  /**
   * Verifica si el usuario puede gestionar usuarios
   */
  const canManageUsers = (): boolean => {
    return isSuperAdmin();
  };

  /**
   * Verifica si el usuario puede gestionar reglas de alertas
   */
  const canManageAlertRules = (): boolean => {
    return isAdmin();
  };

  /**
   * Obtiene los IDs de locations permitidas
   * @returns null si es super_admin (acceso a todo), array si tiene restricciones
   */
  const getAccessibleLocationIds = (): number[] | null => {
    if (!user) return [];
    if (user.role === 'super_admin') return null;
    return user.allowed_location_ids || [];
  };

  return {
    hasRole,
    isSuperAdmin,
    isAdmin,
    isTechnician,
    isGuest,
    canWrite,
    canOnlyRead,
    canAccessLocation,
    canCreateDevice,
    canEditDevice,
    canDeleteDevice,
    canManageUsers,
    canManageAlertRules,
    getAccessibleLocationIds,
    role: user?.role,
  };
};

export default usePermissions;
