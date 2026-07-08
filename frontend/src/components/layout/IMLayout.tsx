/**
 * IMLayout - Main Layout Wrapper Component
 *
 * Layout completo con Sidebar + Topbar + Main Content
 * Maneja responsive, estado collapsed, mobile drawer
 */

import React, { useState, useEffect } from 'react';
import clsx from 'clsx';
import { IMSidebar, NavItem } from './IMSidebar';
import { IMTopbar, BreadcrumbItem } from './IMTopbar';

// ========================================
// TYPES
// ========================================

export interface IMLayoutProps {
  /**
   * Contenido principal
   */
  children: React.ReactNode;

  /**
   * Items de navegación del sidebar
   */
  navItems: NavItem[];

  /**
   * Breadcrumbs para el topbar
   */
  breadcrumbs?: BreadcrumbItem[];

  /**
   * Page title (si no hay breadcrumbs)
   */
  title?: string;

  /**
   * Número de notificaciones no leídas
   */
  notificationCount?: number;

  /**
   * Callback cuando se clickea en notificaciones
   */
  onNotificationsClick?: () => void;

  /**
   * Clases CSS para el main content
   */
  contentClassName?: string;

  /**
   * Padding del main content
   * @default 'default'
   */
  contentPadding?: 'none' | 'sm' | 'default' | 'lg';
}

// ========================================
// COMPONENT
// ========================================

export const IMLayout: React.FC<IMLayoutProps> = ({
  children,
  navItems,
  breadcrumbs,
  title,
  notificationCount,
  onNotificationsClick,
  contentClassName,
  contentPadding = 'default',
}) => {
  // ========================================
  // STATE
  // ========================================

  const [sidebarCollapsed, setSidebarCollapsed] = useState(false);
  const [mobileSidebarOpen, setMobileSidebarOpen] = useState(false);

  // ========================================
  // EFFECTS
  // ========================================

  // Load collapsed state from localStorage
  useEffect(() => {
    const saved = localStorage.getItem('sidebar-collapsed');
    if (saved !== null) {
      setSidebarCollapsed(saved === 'true');
    }
  }, []);

  // Save collapsed state to localStorage
  const handleToggleCollapsed = () => {
    const newState = !sidebarCollapsed;
    setSidebarCollapsed(newState);
    localStorage.setItem('sidebar-collapsed', String(newState));
  };

  // Close mobile sidebar on route change
  useEffect(() => {
    setMobileSidebarOpen(false);
  }, [breadcrumbs, title]);

  // Prevent body scroll when mobile sidebar is open
  useEffect(() => {
    if (mobileSidebarOpen) {
      document.body.style.overflow = 'hidden';
    } else {
      document.body.style.overflow = '';
    }

    return () => {
      document.body.style.overflow = '';
    };
  }, [mobileSidebarOpen]);

  // ========================================
  // STYLES
  // ========================================

  const mainStyles = clsx(
    'min-h-screen bg-im-bg',
    'transition-all duration-300',
    // Desktop margin (for sidebar)
    sidebarCollapsed ? 'lg:ml-sidebar-collapsed' : 'lg:ml-sidebar-expanded'
  );

  const contentPaddingStyles = {
    none: 'p-0',
    sm: 'p-4',
    default: 'p-4 lg:p-6',
    lg: 'p-6 lg:p-8',
  };

  const contentStyles = clsx(
    'min-h-[calc(100vh-var(--topbar-height))]',
    contentPaddingStyles[contentPadding],
    contentClassName
  );

  // ========================================
  // RENDER
  // ========================================

  return (
    <div className="relative">
      {/* Sidebar */}
      <IMSidebar
        collapsed={sidebarCollapsed}
        onToggle={handleToggleCollapsed}
        navItems={navItems}
        mobileOpen={mobileSidebarOpen}
        onMobileToggle={() => setMobileSidebarOpen(false)}
      />

      {/* Main Content Area */}
      <div className={mainStyles}>
        {/* Topbar */}
        <IMTopbar
          breadcrumbs={breadcrumbs}
          title={title}
          onMobileMenuToggle={() => setMobileSidebarOpen(true)}
          notificationCount={notificationCount}
          onNotificationsClick={onNotificationsClick}
        />

        {/* Page Content */}
        <main className={contentStyles}>{children}</main>
      </div>
    </div>
  );
};

export default IMLayout;
