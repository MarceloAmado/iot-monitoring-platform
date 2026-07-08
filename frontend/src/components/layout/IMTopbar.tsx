/**
 * IMTopbar - Top Navigation Bar Component
 *
 * Barra superior con breadcrumb, search, notifications y user menu
 * Height: 64px (var(--topbar-height))
 */

import React, { useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import clsx from 'clsx';
import { IMBadge } from '@/components/common';
import { useAuth } from '@/hooks/useAuth';

// ========================================
// TYPES
// ========================================

export interface BreadcrumbItem {
  label: string;
  href?: string;
}

export interface IMTopbarProps {
  /**
   * Breadcrumb items
   */
  breadcrumbs?: BreadcrumbItem[];

  /**
   * Page title (si no hay breadcrumbs)
   */
  title?: string;

  /**
   * Toggle mobile sidebar
   */
  onMobileMenuToggle?: () => void;

  /**
   * Número de notificaciones no leídas
   */
  notificationCount?: number;

  /**
   * Callback cuando se clickea en notificaciones
   */
  onNotificationsClick?: () => void;
}

// ========================================
// COMPONENT
// ========================================

export const IMTopbar: React.FC<IMTopbarProps> = ({
  breadcrumbs,
  title,
  onMobileMenuToggle,
  notificationCount = 0,
  onNotificationsClick,
}) => {
  const navigate = useNavigate();
  const { user, logout } = useAuth();
  const [showUserMenu, setShowUserMenu] = useState(false);

  // ========================================
  // HANDLERS
  // ========================================

  const handleLogout = () => {
    logout();
    navigate('/login');
  };

  // ========================================
  // RENDER
  // ========================================

  return (
    <header className="sticky top-0 z-sticky bg-white border-b border-im-neutral-100 h-topbar">
      <div className="h-full px-4 lg:px-6 flex items-center justify-between gap-4">
        {/* Left: Mobile Menu + Breadcrumb/Title */}
        <div className="flex items-center gap-4 flex-1 min-w-0">
          {/* Mobile Menu Button */}
          <button
            onClick={onMobileMenuToggle}
            className="lg:hidden flex items-center justify-center w-10 h-10 rounded-md hover:bg-im-neutral-100 transition-colors"
            aria-label="Abrir menú"
          >
            <svg className="w-6 h-6 text-im-neutral-700" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 6h16M4 12h16M4 18h16" />
            </svg>
          </button>

          {/* Breadcrumb */}
          {breadcrumbs && breadcrumbs.length > 0 ? (
            <nav aria-label="Breadcrumb" className="hidden md:block">
              <ol className="flex items-center gap-2">
                {breadcrumbs.map((item, index) => (
                  <li key={index} className="flex items-center gap-2">
                    {index > 0 && (
                      <svg
                        className="w-4 h-4 text-im-neutral-300"
                        fill="currentColor"
                        viewBox="0 0 20 20"
                      >
                        <path
                          fillRule="evenodd"
                          d="M7.293 14.707a1 1 0 010-1.414L10.586 10 7.293 6.707a1 1 0 011.414-1.414l4 4a1 1 0 010 1.414l-4 4a1 1 0 01-1.414 0z"
                          clipRule="evenodd"
                        />
                      </svg>
                    )}

                    {item.href ? (
                      <Link
                        to={item.href}
                        className="text-sm font-medium text-im-neutral-500 hover:text-im-blue transition-colors"
                      >
                        {item.label}
                      </Link>
                    ) : (
                      <span className="text-sm font-semibold text-im-neutral-900">
                        {item.label}
                      </span>
                    )}
                  </li>
                ))}
              </ol>
            </nav>
          ) : (
            // Title fallback si no hay breadcrumbs
            title && (
              <h1 className="font-montserrat text-xl font-bold text-im-blue truncate">
                {title}
              </h1>
            )
          )}
        </div>

        {/* Right: Search, Notifications, User Menu */}
        <div className="flex items-center gap-2">
          {/* Search (Desktop only) */}
          <div className="hidden xl:block">
            <div className="relative">
              <input
                type="text"
                placeholder="Buscar..."
                className="w-64 pl-10 pr-4 py-2 border border-im-neutral-300 rounded-md text-sm focus:outline-none focus:ring-2 focus:ring-im-orange-soft/30 focus:border-im-orange transition-all"
              />
              <svg
                className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-im-neutral-500"
                fill="none"
                viewBox="0 0 24 24"
                stroke="currentColor"
              >
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={2}
                  d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z"
                />
              </svg>
            </div>
          </div>

          {/* Notifications */}
          <button
            onClick={onNotificationsClick}
            className="relative flex items-center justify-center w-10 h-10 rounded-md hover:bg-im-neutral-100 transition-colors"
            aria-label="Notificaciones"
          >
            <svg className="w-5 h-5 text-im-neutral-700" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={2}
                d="M15 17h5l-1.405-1.405A2.032 2.032 0 0118 14.158V11a6.002 6.002 0 00-4-5.659V5a2 2 0 10-4 0v.341C7.67 6.165 6 8.388 6 11v3.159c0 .538-.214 1.055-.595 1.436L4 17h5m6 0v1a3 3 0 11-6 0v-1m6 0H9"
              />
            </svg>

            {/* Badge */}
            {notificationCount > 0 && (
              <span className="absolute top-1 right-1 w-5 h-5 bg-im-danger text-white text-xs font-bold rounded-full flex items-center justify-center">
                {notificationCount > 9 ? '9+' : notificationCount}
              </span>
            )}
          </button>

          {/* User Menu */}
          <div className="relative">
            <button
              onClick={() => setShowUserMenu(!showUserMenu)}
              className="flex items-center gap-2 p-2 rounded-md hover:bg-im-neutral-100 transition-colors"
              aria-label="Menú de usuario"
              aria-expanded={showUserMenu}
            >
              {/* Avatar */}
              <div className="w-8 h-8 bg-im-blue rounded-full flex items-center justify-center text-white text-sm font-semibold">
                {user?.first_name?.[0]}{user?.last_name?.[0]}
              </div>

              {/* Name (hidden on mobile) */}
              <span className="hidden lg:block text-sm font-medium text-im-neutral-900">
                {user?.first_name}
              </span>

              {/* Chevron */}
              <svg
                className={clsx(
                  'w-4 h-4 text-im-neutral-500 transition-transform',
                  showUserMenu && 'rotate-180'
                )}
                fill="none"
                viewBox="0 0 24 24"
                stroke="currentColor"
              >
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
              </svg>
            </button>

            {/* Dropdown Menu */}
            {showUserMenu && (
              <>
                {/* Backdrop (para cerrar) */}
                <div
                  className="fixed inset-0 z-dropdown"
                  onClick={() => setShowUserMenu(false)}
                  aria-hidden="true"
                />

                {/* Menu */}
                <div className="absolute right-0 mt-2 w-56 bg-white rounded-md shadow-im-modal border border-im-neutral-100 z-dropdown animate-scale-in">
                  {/* User Info */}
                  <div className="p-3 border-b border-im-neutral-100">
                    <p className="text-sm font-semibold text-im-neutral-900">
                      {user?.first_name} {user?.last_name}
                    </p>
                    <p className="text-xs text-im-neutral-500 truncate">{user?.email}</p>
                    <IMBadge variant="primary" size="sm" className="mt-2">
                      {user?.role}
                    </IMBadge>
                  </div>

                  {/* Menu Items */}
                  <div className="py-1">
                    <Link
                      to="/profile"
                      className="flex items-center gap-3 px-4 py-2 text-sm text-im-neutral-700 hover:bg-im-neutral-100 transition-colors"
                      onClick={() => setShowUserMenu(false)}
                    >
                      <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                        <path
                          strokeLinecap="round"
                          strokeLinejoin="round"
                          strokeWidth={2}
                          d="M16 7a4 4 0 11-8 0 4 4 0 018 0zM12 14a7 7 0 00-7 7h14a7 7 0 00-7-7z"
                        />
                      </svg>
                      Mi Perfil
                    </Link>

                    <Link
                      to="/settings"
                      className="flex items-center gap-3 px-4 py-2 text-sm text-im-neutral-700 hover:bg-im-neutral-100 transition-colors"
                      onClick={() => setShowUserMenu(false)}
                    >
                      <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
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
                      Configuración
                    </Link>
                  </div>

                  {/* Logout */}
                  <div className="border-t border-im-neutral-100 py-1">
                    <button
                      onClick={handleLogout}
                      className="w-full flex items-center gap-3 px-4 py-2 text-sm text-im-danger hover:bg-im-danger-light transition-colors"
                    >
                      <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                        <path
                          strokeLinecap="round"
                          strokeLinejoin="round"
                          strokeWidth={2}
                          d="M17 16l4-4m0 0l-4-4m4 4H7m6 4v1a3 3 0 01-3 3H6a3 3 0 01-3-3V7a3 3 0 013-3h4a3 3 0 013 3v1"
                        />
                      </svg>
                      Cerrar Sesión
                    </button>
                  </div>
                </div>
              </>
            )}
          </div>
        </div>
      </div>
    </header>
  );
};

export default IMTopbar;
