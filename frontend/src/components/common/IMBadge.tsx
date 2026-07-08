import React from 'react';
import clsx from 'clsx';

/**
 * IMBadge - Componente de badge/pill atómico de IdeaMakers
 *
 * Status pills y badges con variantes de color
 *
 * @example
 * ```tsx
 * <IMBadge variant="success">Online</IMBadge>
 * <IMBadge variant="danger" size="sm">Error</IMBadge>
 * <IMBadge variant="info" leftIcon={<InfoIcon />}>Info</IMBadge>
 * ```
 */

// ========================================
// TYPES
// ========================================

export type IMBadgeVariant =
  | 'success'
  | 'warning'
  | 'danger'
  | 'info'
  | 'neutral'
  | 'primary'
  | 'secondary';

export type IMBadgeSize = 'sm' | 'md' | 'lg';

export interface IMBadgeProps {
  /**
   * Variante de color
   * @default 'neutral'
   */
  variant?: IMBadgeVariant;

  /**
   * Tamaño del badge
   * @default 'md'
   */
  size?: IMBadgeSize;

  /**
   * Contenido del badge
   */
  children: React.ReactNode;

  /**
   * Icono a la izquierda (opcional)
   */
  leftIcon?: React.ReactNode;

  /**
   * Icono a la derecha (opcional)
   */
  rightIcon?: React.ReactNode;

  /**
   * Badge con borde (outline style)
   * @default false
   */
  outline?: boolean;

  /**
   * Badge pill (border-radius full)
   * @default true
   */
  pill?: boolean;

  /**
   * Clases CSS adicionales
   */
  className?: string;

  /**
   * OnClick handler (hace el badge clickable)
   */
  onClick?: () => void;
}

// ========================================
// COMPONENT
// ========================================

export const IMBadge: React.FC<IMBadgeProps> = ({
  variant = 'neutral',
  size = 'md',
  children,
  leftIcon,
  rightIcon,
  outline = false,
  pill = true,
  className,
  onClick,
}) => {
  // ========================================
  // STYLES
  // ========================================

  const baseStyles = clsx(
    'inline-flex items-center justify-center gap-1 font-semibold',
    'transition-all duration-200',
    pill ? 'rounded-full' : 'rounded-md',
    onClick && 'cursor-pointer hover:brightness-90 active:scale-95'
  );

  // Size styles
  const sizeStyles = {
    sm: 'px-2 py-0.5 text-xs',
    md: 'px-2.5 py-0.5 text-xs',
    lg: 'px-3 py-1 text-sm',
  };

  // Variant styles (filled)
  const filledVariantStyles = {
    success: 'bg-im-success-light text-im-success',
    warning: 'bg-im-warning-light text-im-warning',
    danger: 'bg-im-danger-light text-im-danger',
    info: 'bg-im-info-light text-im-info',
    neutral: 'bg-im-neutral-100 text-im-neutral-700',
    primary: 'bg-im-blue/10 text-im-blue',
    secondary: 'bg-im-orange-soft/20 text-im-orange',
  };

  // Variant styles (outline)
  const outlineVariantStyles = {
    success: 'border border-im-success text-im-success bg-transparent',
    warning: 'border border-im-warning text-im-warning bg-transparent',
    danger: 'border border-im-danger text-im-danger bg-transparent',
    info: 'border border-im-info text-im-info bg-transparent',
    neutral: 'border border-im-neutral-300 text-im-neutral-700 bg-transparent',
    primary: 'border border-im-blue text-im-blue bg-transparent',
    secondary: 'border border-im-orange text-im-orange bg-transparent',
  };

  const variantStyles = outline
    ? outlineVariantStyles[variant]
    : filledVariantStyles[variant];

  // ========================================
  // RENDER
  // ========================================

  const BadgeContent = (
    <>
      {leftIcon && <span className="flex-shrink-0">{leftIcon}</span>}
      <span>{children}</span>
      {rightIcon && <span className="flex-shrink-0">{rightIcon}</span>}
    </>
  );

  if (onClick) {
    return (
      <button
        type="button"
        className={clsx(baseStyles, sizeStyles[size], variantStyles, className)}
        onClick={onClick}
      >
        {BadgeContent}
      </button>
    );
  }

  return (
    <span className={clsx(baseStyles, sizeStyles[size], variantStyles, className)}>
      {BadgeContent}
    </span>
  );
};

// ========================================
// DEVICE STATUS BADGES (Shortcuts)
// ========================================

interface DeviceStatusBadgeProps {
  size?: IMBadgeSize;
  className?: string;
  onClick?: () => void;
}

export const OnlineBadge: React.FC<DeviceStatusBadgeProps> = (props) => (
  <IMBadge variant="success" {...props}>
    Online
  </IMBadge>
);

export const OfflineBadge: React.FC<DeviceStatusBadgeProps> = (props) => (
  <IMBadge variant="neutral" {...props}>
    Offline
  </IMBadge>
);

export const MaintenanceBadge: React.FC<DeviceStatusBadgeProps> = (props) => (
  <IMBadge variant="warning" {...props}>
    Mantenimiento
  </IMBadge>
);

export const ErrorBadge: React.FC<DeviceStatusBadgeProps> = (props) => (
  <IMBadge variant="danger" {...props}>
    Error
  </IMBadge>
);

export default IMBadge;
