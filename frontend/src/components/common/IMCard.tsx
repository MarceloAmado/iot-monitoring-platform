import React from 'react';
import clsx from 'clsx';

/**
 * IMCard - Componente de card atómico de IdeaMakers
 *
 * Card con header, body y footer opcionales
 *
 * @example
 * ```tsx
 * <IMCard
 *   title="Device Status"
 *   actions={<button>Ver más</button>}
 *   footer={<p>Última actualización: hace 2 min</p>}
 * >
 *   <p>Contenido del card</p>
 * </IMCard>
 * ```
 */

// ========================================
// TYPES
// ========================================

export interface IMCardProps {
  /**
   * Contenido principal del card
   */
  children: React.ReactNode;

  /**
   * Título del card (opcional, aparece en header)
   */
  title?: string;

  /**
   * Subtítulo o descripción (opcional, aparece en header)
   */
  subtitle?: string;

  /**
   * Acciones en el header (botones, iconos, etc.)
   */
  actions?: React.ReactNode;

  /**
   * Footer del card (opcional)
   */
  footer?: React.ReactNode;

  /**
   * Padding del body
   * @default 'md'
   */
  padding?: 'none' | 'sm' | 'md' | 'lg';

  /**
   * Hover effect (eleva el card)
   * @default false
   */
  hoverable?: boolean;

  /**
   * Clickable (cursor pointer + hover)
   * @default false
   */
  clickable?: boolean;

  /**
   * OnClick handler (si clickable)
   */
  onClick?: () => void;

  /**
   * Clases CSS adicionales
   */
  className?: string;

  /**
   * Clases CSS para el header
   */
  headerClassName?: string;

  /**
   * Clases CSS para el body
   */
  bodyClassName?: string;

  /**
   * Clases CSS para el footer
   */
  footerClassName?: string;
}

// ========================================
// COMPONENT
// ========================================

export const IMCard: React.FC<IMCardProps> = ({
  children,
  title,
  subtitle,
  actions,
  footer,
  padding = 'md',
  hoverable = false,
  clickable = false,
  onClick,
  className,
  headerClassName,
  bodyClassName,
  footerClassName,
}) => {
  // ========================================
  // STYLES
  // ========================================

  const cardStyles = clsx(
    'im-card',
    hoverable && 'im-card-hover hover-lift',
    clickable && 'cursor-pointer',
    className
  );

  const paddingStyles = {
    none: 'p-0',
    sm: 'p-2',
    md: 'p-4',
    lg: 'p-6',
  };

  const bodyStyles = clsx(paddingStyles[padding], bodyClassName);

  const hasHeader = title || subtitle || actions;

  // ========================================
  // RENDER
  // ========================================

  return (
    <div
      className={cardStyles}
      onClick={clickable ? onClick : undefined}
      role={clickable ? 'button' : undefined}
      tabIndex={clickable ? 0 : undefined}
      onKeyDown={
        clickable
          ? (e) => {
              if (e.key === 'Enter' || e.key === ' ') {
                e.preventDefault();
                onClick?.();
              }
            }
          : undefined
      }
    >
      {/* Header */}
      {hasHeader && (
        <div className={clsx('im-card-header', headerClassName)}>
          <div className="flex items-start justify-between gap-4">
            <div className="flex-1 min-w-0">
              {title && (
                <h3 className="font-montserrat text-lg font-semibold text-im-blue truncate">
                  {title}
                </h3>
              )}
              {subtitle && (
                <p className="text-sm text-im-neutral-500 mt-1">{subtitle}</p>
              )}
            </div>

            {actions && (
              <div className="flex-shrink-0 flex items-center gap-2">
                {actions}
              </div>
            )}
          </div>
        </div>
      )}

      {/* Body */}
      <div className={bodyStyles}>{children}</div>

      {/* Footer */}
      {footer && (
        <div className={clsx('im-card-footer', footerClassName)}>{footer}</div>
      )}
    </div>
  );
};

export default IMCard;
