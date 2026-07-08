/**
 * IMSidebar - Sidebar Navigation Component
 *
 * Sidebar collapsible con navegación del sistema
 * Ancho: 280px (expanded) / 72px (collapsed)
 * Mobile: Hidden, se abre como drawer
 */

import React from 'react';
import { Link, useLocation } from 'react-router-dom';
import clsx from 'clsx';
import { Logo, LogoSidebar } from '@/components/common';
import { useAuth } from '@/hooks/useAuth';

// ========================================
// TYPES
// ========================================

export interface NavItem {
  id: string;
  label: string;
  href: string;
  icon: React.ReactNode;
  requiresAdmin?: boolean;
  badge?: number | string;
}

export interface IMSidebarProps {
  /**
   * Estado colapsado
   */
  collapsed: boolean;

  /**
   * Toggle collapsed state
   */
  onToggle: () => void;

  /**
   * Items de navegación
   */
  navItems: NavItem[];

  /**
   * Mobile sidebar abierto
   */
  mobileOpen?: boolean;

  /**
   * Toggle mobile sidebar
   */
  onMobileToggle?: () => void;
}

// ========================================
// COMPONENT
// ========================================

export const IMSidebar: React.FC<IMSidebarProps> = ({
  collapsed,
  onToggle,
  navItems,
  mobileOpen = false,
  onMobileToggle,
}) => {
  const location = useLocation();
  const { user } = useAuth();

  // Check if user has permission for admin items
  const canAccessItem = (item: NavItem): boolean => {
    if (!item.requiresAdmin) return true;
    return user?.role === 'super_admin' || user?.role === 'service_admin';
  };

  // Check if current path is active
  const isActive = (href: string): boolean => {
    return location.pathname === href || location.pathname.startsWith(href + '/');
  };

  // ========================================
  // STYLES
  // ========================================

  const sidebarStyles = clsx(
    // Base styles
    'fixed top-0 left-0 h-full bg-white border-r border-im-neutral-100',
    'transition-all duration-300 ease-in-out z-sticky',
    'flex flex-col',
    // Desktop width
    collapsed ? 'lg:w-sidebar-collapsed' : 'lg:w-sidebar-expanded',
    // Mobile (drawer)
    'w-sidebar-expanded',
    mobileOpen ? 'translate-x-0' : '-translate-x-full lg:translate-x-0'
  );

  const navItemStyles = (item: NavItem) =>
    clsx(
      'flex items-center gap-3 px-4 py-3 rounded-md',
      'transition-all duration-200',
      'font-medium text-sm',
      'group relative',
      isActive(item.href)
        ? 'bg-im-orange/10 text-im-orange border-l-3 border-im-orange'
        : 'text-im-neutral-700 hover:bg-im-neutral-100 hover:text-im-blue',
      collapsed && 'lg:justify-center',
      !canAccessItem(item) && 'opacity-50 cursor-not-allowed'
    );

  // ========================================
  // RENDER
  // ========================================

  return (
    <>
      {/* Mobile Overlay */}
      {mobileOpen && (
        <div
          className="fixed inset-0 bg-black/50 z-sticky lg:hidden"
          onClick={onMobileToggle}
          aria-hidden="true"
        />
      )}

      {/* Sidebar */}
      <aside className={sidebarStyles}>
        {/* Header */}
        <div className="p-4 border-b border-im-neutral-100 flex items-center justify-between">
          {/* Logo */}
          {collapsed ? (
            <div className="w-full flex justify-center">
              <LogoSidebar />
            </div>
          ) : (
            <Logo variant="horizontal" height={32} />
          )}

          {/* Toggle Button (Desktop only) */}
          <button
            onClick={onToggle}
            className="hidden lg:flex items-center justify-center w-8 h-8 rounded-md hover:bg-im-neutral-100 transition-colors"
            aria-label={collapsed ? 'Expandir sidebar' : 'Colapsar sidebar'}
          >
            <svg
              className={clsx(
                'w-5 h-5 text-im-neutral-500 transition-transform',
                collapsed && 'rotate-180'
              )}
              fill="none"
              viewBox="0 0 24 24"
              stroke="currentColor"
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={2}
                d="M15 19l-7-7 7-7"
              />
            </svg>
          </button>

          {/* Close Button (Mobile only) */}
          <button
            onClick={onMobileToggle}
            className="lg:hidden flex items-center justify-center w-8 h-8 rounded-md hover:bg-im-neutral-100 transition-colors"
            aria-label="Cerrar menú"
          >
            <svg className="w-5 h-5 text-im-neutral-500" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
            </svg>
          </button>
        </div>

        {/* Navigation */}
        <nav className="flex-1 p-4 space-y-1 overflow-y-auto">
          {navItems.map((item) => {
            const isItemActive = isActive(item.href);
            const hasAccess = canAccessItem(item);

            if (!hasAccess && item.requiresAdmin) {
              return null; // Hide items user can't access
            }

            return (
              <Link
                key={item.id}
                to={hasAccess ? item.href : '#'}
                className={navItemStyles(item)}
                onClick={(e) => {
                  if (!hasAccess) e.preventDefault();
                  if (mobileOpen && onMobileToggle) onMobileToggle();
                }}
                aria-current={isItemActive ? 'page' : undefined}
                title={collapsed ? item.label : undefined}
              >
                {/* Icon */}
                <span
                  className={clsx(
                    'flex-shrink-0 w-5 h-5',
                    isItemActive ? 'text-im-orange' : 'text-im-neutral-500 group-hover:text-im-blue'
                  )}
                >
                  {item.icon}
                </span>

                {/* Label (hidden when collapsed on desktop) */}
                <span className={clsx('flex-1 truncate', collapsed && 'lg:hidden')}>
                  {item.label}
                </span>

                {/* Badge (notifications, alerts, etc.) */}
                {item.badge && !collapsed && (
                  <span className="flex-shrink-0 px-2 py-0.5 bg-im-orange text-white text-xs font-semibold rounded-full">
                    {item.badge}
                  </span>
                )}

                {/* Active Indicator (border izquierdo) */}
                {isItemActive && (
                  <span className="absolute left-0 top-0 bottom-0 w-1 bg-im-orange rounded-r-full" />
                )}
              </Link>
            );
          })}
        </nav>

        {/* Footer */}
        <div className="p-4 border-t border-im-neutral-100">
          {/* User Info */}
          {!collapsed && user && (
            <div className="flex items-center gap-3 p-3 rounded-md bg-im-neutral-100">
              {/* Avatar */}
              <div className="flex-shrink-0 w-10 h-10 bg-im-blue rounded-full flex items-center justify-center text-white font-semibold">
                {user.first_name?.[0]}{user.last_name?.[0]}
              </div>

              {/* Info */}
              <div className="flex-1 min-w-0">
                <p className="text-sm font-semibold text-im-neutral-900 truncate">
                  {user.first_name} {user.last_name}
                </p>
                <p className="text-xs text-im-neutral-500 truncate">{user.email}</p>
              </div>
            </div>
          )}

          {/* Collapsed user avatar */}
          {collapsed && user && (
            <div className="flex justify-center">
              <div className="w-10 h-10 bg-im-blue rounded-full flex items-center justify-center text-white font-semibold">
                {user.first_name?.[0]}{user.last_name?.[0]}
              </div>
            </div>
          )}
        </div>
      </aside>
    </>
  );
};

export default IMSidebar;
