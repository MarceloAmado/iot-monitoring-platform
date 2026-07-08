/**
 * Componente para controlar visibilidad basada en roles.
 *
 * Uso:
 * <RoleGate roles={['super_admin', 'service_admin']}>
 *   <button>Solo admins ven esto</button>
 * </RoleGate>
 */

import { ReactNode } from 'react';
import { useAuth } from '@/hooks/useAuth';

interface RoleGateProps {
  children: ReactNode;
  roles: ('super_admin' | 'service_admin' | 'technician' | 'guest')[];
  fallback?: ReactNode;
}

export const RoleGate = ({ children, roles, fallback = null }: RoleGateProps) => {
  const { user } = useAuth();

  // Si no hay usuario, no mostrar nada
  if (!user) {
    return <>{fallback}</>;
  }

  // Verificar si el usuario tiene uno de los roles permitidos
  const hasPermission = roles.includes(user.role);

  if (!hasPermission) {
    return <>{fallback}</>;
  }

  return <>{children}</>;
};

export default RoleGate;
