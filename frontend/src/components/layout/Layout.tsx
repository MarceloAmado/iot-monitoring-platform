/**
 * Layout principal con IMLayout (IdeaMakers Design System)
 *
 * Wrapper que configura el layout completo con navegación
 */

import React, { useMemo, useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import { IMLayout } from './IMLayout';
import { NotificationsModal } from '@/components/alerts/NotificationsModal';
import { usePermissions } from '@/hooks/usePermissions';
import { listAlertHistory } from '@/services/alertService';
import type { NavItem } from './IMSidebar';
import type { BreadcrumbItem } from './IMTopbar';

// ========================================
// NAV ITEMS CONFIGURATION
// ========================================

const NAV_ITEMS: NavItem[] = [
  {
    id: 'dashboard',
    label: 'Dashboard',
    href: '/dashboard',
    icon: (
      <svg fill="none" viewBox="0 0 24 24" stroke="currentColor">
        <path
          strokeLinecap="round"
          strokeLinejoin="round"
          strokeWidth={2}
          d="M3 12l2-2m0 0l7-7 7 7M5 10v10a1 1 0 001 1h3m10-11l2 2m-2-2v10a1 1 0 01-1 1h-3m-6 0a1 1 0 001-1v-4a1 1 0 011-1h2a1 1 0 011 1v4a1 1 0 001 1m-6 0h6"
        />
      </svg>
    ),
  },
  {
    id: 'devices',
    label: 'Dispositivos',
    href: '/devices',
    icon: (
      <svg fill="none" viewBox="0 0 24 24" stroke="currentColor">
        <path
          strokeLinecap="round"
          strokeLinejoin="round"
          strokeWidth={2}
          d="M9 3v2m6-2v2M9 19v2m6-2v2M5 9H3m2 6H3m18-6h-2m2 6h-2M7 19h10a2 2 0 002-2V7a2 2 0 00-2-2H7a2 2 0 00-2 2v10a2 2 0 002 2zM9 9h6v6H9V9z"
        />
      </svg>
    ),
  },
  {
    id: 'alerts',
    label: 'Alertas',
    href: '/alerts',
    icon: (
      <svg fill="none" viewBox="0 0 24 24" stroke="currentColor">
        <path
          strokeLinecap="round"
          strokeLinejoin="round"
          strokeWidth={2}
          d="M15 17h5l-1.405-1.405A2.032 2.032 0 0118 14.158V11a6.002 6.002 0 00-4-5.659V5a2 2 0 10-4 0v.341C7.67 6.165 6 8.388 6 11v3.159c0 .538-.214 1.055-.595 1.436L4 17h5m6 0v1a3 3 0 11-6 0v-1m6 0H9"
        />
      </svg>
    ),
  },
  {
    id: 'health',
    label: 'Salud',
    href: '/health',
    icon: (
      <svg fill="none" viewBox="0 0 24 24" stroke="currentColor">
        <path
          strokeLinecap="round"
          strokeLinejoin="round"
          strokeWidth={2}
          d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z"
        />
      </svg>
    ),
  },
  {
    id: 'locations',
    label: 'Ubicaciones',
    href: '/locations',
    icon: (
      <svg fill="none" viewBox="0 0 24 24" stroke="currentColor">
        <path
          strokeLinecap="round"
          strokeLinejoin="round"
          strokeWidth={2}
          d="M17.657 16.657L13.414 20.9a1.998 1.998 0 01-2.827 0l-4.244-4.243a8 8 0 1111.314 0z"
        />
        <path
          strokeLinecap="round"
          strokeLinejoin="round"
          strokeWidth={2}
          d="M15 11a3 3 0 11-6 0 3 3 0 016 0z"
        />
      </svg>
    ),
    requiresAdmin: true,
  },
  {
    id: 'users',
    label: 'Usuarios',
    href: '/users',
    icon: (
      <svg fill="none" viewBox="0 0 24 24" stroke="currentColor">
        <path
          strokeLinecap="round"
          strokeLinejoin="round"
          strokeWidth={2}
          d="M12 4.354a4 4 0 110 5.292M15 21H3v-1a6 6 0 0112 0v1zm0 0h6v-1a6 6 0 00-9-5.197M13 7a4 4 0 11-8 0 4 4 0 018 0z"
        />
      </svg>
    ),
    requiresAdmin: true,
  },
  {
    id: 'firmware',
    label: 'Firmware OTA',
    href: '/firmware',
    icon: (
      <svg fill="none" viewBox="0 0 24 24" stroke="currentColor">
        <path
          strokeLinecap="round"
          strokeLinejoin="round"
          strokeWidth={2}
          d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-8l-4-4m0 0L8 8m4-4v12"
        />
      </svg>
    ),
    requiresAdmin: true,
  },
  {
    id: 'sensors',
    label: 'Catálogo de Sensores',
    href: '/sensors',
    icon: (
      <svg fill="none" viewBox="0 0 24 24" stroke="currentColor">
        <path
          strokeLinecap="round"
          strokeLinejoin="round"
          strokeWidth={2}
          d="M19.428 15.428a2 2 0 00-1.022-.547l-2.387-.477a6 6 0 00-3.86.517l-.318.158a6 6 0 01-3.86.517L6.05 15.21a2 2 0 00-1.806.547M8 4h8l-1 1v5.172a2 2 0 00.586 1.414l5 5c1.26 1.26.367 3.414-1.415 3.414H4.828c-1.782 0-2.674-2.154-1.414-3.414l5-5A2 2 0 009 10.172V5L8 4z"
        />
      </svg>
    ),
    requiresAdmin: true,
  },
  {
    id: 'profile',
    label: 'Mi Perfil',
    href: '/profile',
    icon: (
      <svg fill="none" viewBox="0 0 24 24" stroke="currentColor">
        <path
          strokeLinecap="round"
          strokeLinejoin="round"
          strokeWidth={2}
          d="M16 7a4 4 0 11-8 0 4 4 0 018 0zM12 14a7 7 0 00-7 7h14a7 7 0 00-7-7z"
        />
      </svg>
    ),
  },
  {
    id: 'settings',
    label: 'Configuración',
    href: '/settings',
    icon: (
      <svg fill="none" viewBox="0 0 24 24" stroke="currentColor">
        <path
          strokeLinecap="round"
          strokeLinejoin="round"
          strokeWidth={2}
          d="M10.325 4.317c.426-1.756 2.924-1.756 3.35 0a1.724 1.724 0 002.573 1.066c1.543-.94 3.31.826 2.37 2.37a1.724 1.724 0 001.065 2.572c1.756.426 1.756 2.924 0 3.35a1.724 1.724 0 00-1.066 2.573c.94 1.543-.826 3.31-2.37 2.37a1.724 1.724 0 00-2.572 1.065c-.426 1.756-2.924 1.756-3.35 0a1.724 1.724 0 00-2.573-1.066c-1.543.94-3.31-.826-2.37-2.37a1.724 1.724 0 00-1.065-2.572c-1.756-.426-1.756-2.924 0-3.35a1.724 1.724 0 001.066-2.573c-.94-1.543.826-3.31 2.37-2.37.996.608 2.296.07 2.572-1.065z"
        />
        <path
          strokeLinecap="round"
          strokeLinejoin="round"
          strokeWidth={2}
          d="M15 12a3 3 0 11-6 0 3 3 0 016 0z"
        />
      </svg>
    ),
  },
];

// ========================================
// TYPES
// ========================================

interface LayoutProps {
  children: React.ReactNode;
  breadcrumbs?: BreadcrumbItem[];
  title?: string;
  contentPadding?: 'none' | 'sm' | 'default' | 'lg';
  contentClassName?: string;
}

// ========================================
// COMPONENT
// ========================================

export const Layout = ({
  children,
  breadcrumbs,
  title,
  contentPadding = 'default',
  contentClassName,
}: LayoutProps) => {
  const { canManageUsers, isAdmin } = usePermissions();

  const [notificationsOpen, setNotificationsOpen] = useState(false);

  // Alertas sin reconocer (la campana). Se refresca solo y también
  // cuando useWebSocket invalida ['alerts'] al llegar alert_triggered.
  const { data: unacknowledgedAlerts } = useQuery({
    queryKey: ['alerts', 'unacknowledged'],
    queryFn: () => listAlertHistory({ acknowledged: false, limit: 20 }),
    refetchInterval: 60000,
  });

  const notificationCount = unacknowledgedAlerts?.length ?? 0;

  const handleNotificationsClick = () => {
    setNotificationsOpen(true);
  };

  // Filtrar items de navegación según permisos del usuario
  const filteredNavItems = useMemo(() => {
    return NAV_ITEMS.filter((item) => {
      // Si el item no requiere admin, mostrarlo siempre
      if (!item.requiresAdmin) {
        return true;
      }

      // Si requiere admin, verificar permisos específicos
      if (item.id === 'users') {
        return canManageUsers();
      }

      if (item.id === 'sensors') {
        return isAdmin();
      }

      // Por defecto, si tiene requiresAdmin, verificar isAdmin()
      return isAdmin();
    });
  }, [canManageUsers, isAdmin]);

  return (
    <IMLayout
      navItems={filteredNavItems}
      breadcrumbs={breadcrumbs}
      title={title}
      notificationCount={notificationCount}
      onNotificationsClick={handleNotificationsClick}
      contentPadding={contentPadding}
      contentClassName={contentClassName}
    >
      {children}
      <NotificationsModal
        isOpen={notificationsOpen}
        onClose={() => setNotificationsOpen(false)}
      />
    </IMLayout>
  );
};

export default Layout;
