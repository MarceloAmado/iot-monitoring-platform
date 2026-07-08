import React from 'react';
import clsx from 'clsx';

/**
 * IMButton - Componente de botón atómico de IdeaMakers
 *
 * Sistema de diseño IdeaMakers IoT Monitoring
 * Soporte para 4 variantes, 3 tamaños, estados de loading y disabled
 *
 * @example
 * ```tsx
 * <IMButton variant="primary" size="md" onClick={() => alert('Clicked!')}>
 *   Guardar Cambios
 * </IMButton>
 * ```
 */

// ========================================
// TYPES
// ========================================

export type IMButtonVariant = 'primary' | 'secondary' | 'ghost' | 'danger' | 'success' | 'warning';
export type IMButtonSize = 'sm' | 'md' | 'lg';

export interface IMButtonProps extends React.ButtonHTMLAttributes<HTMLButtonElement> {
  /**
   * Variante visual del botón
   * @default 'primary'
   */
  variant?: IMButtonVariant;

  /**
   * Tamaño del botón
   * @default 'md'
   */
  size?: IMButtonSize;

  /**
   * Estado de carga (muestra spinner y deshabilita)
   * @default false
   */
  loading?: boolean;

  /**
   * Contenido del botón
   */
  children: React.ReactNode;

  /**
   * Clases CSS adicionales
   */
  className?: string;

  /**
   * Icono a la izquierda (opcional)
   */
  leftIcon?: React.ReactNode;

  /**
   * Icono a la derecha (opcional)
   */
  rightIcon?: React.ReactNode;

  /**
   * aria-label para accesibilidad (obligatorio si no hay texto)
   */
  ariaLabel?: string;

  /**
   * Botón de ancho completo
   * @default false
   */
  fullWidth?: boolean;
}

// ========================================
// COMPONENT
// ========================================

export const IMButton = React.forwardRef<HTMLButtonElement, IMButtonProps>(
  (
    {
      variant = 'primary',
      size = 'md',
      loading = false,
      children,
      className,
      leftIcon,
      rightIcon,
      ariaLabel,
      fullWidth = false,
      disabled,
      type = 'button',
      ...rest
    },
    ref
  ) => {
    // ========================================
    // STYLES
    // ========================================

    // Base styles (comunes a todos los botones)
    const baseStyles = clsx(
      'inline-flex items-center justify-center gap-2',
      'font-semibold rounded-md',
      'transition-all duration-200',
      'focus:outline-none focus:ring-4',
      'active:scale-95',
      'disabled:opacity-50 disabled:pointer-events-none',
      fullWidth && 'w-full'
    );

    // Variant styles
    const variantStyles = {
      primary: clsx(
        'bg-im-orange text-white',
        'hover:bg-im-orange-hover',
        'focus:ring-im-orange-soft/30'
      ),
      secondary: clsx(
        'bg-white border border-im-blue text-im-blue',
        'hover:bg-im-blue/5',
        'focus:ring-im-blue/20'
      ),
      ghost: clsx(
        'bg-transparent text-im-blue',
        'hover:bg-im-blue/5',
        'focus:ring-im-blue/20'
      ),
      danger: clsx(
        'bg-im-danger text-white',
        'hover:brightness-90',
        'focus:ring-im-danger/30'
      ),
      success: clsx(
        'bg-im-success text-white',
        'hover:brightness-90',
        'focus:ring-im-success/30'
      ),
      warning: clsx(
        'bg-im-warning text-white',
        'hover:brightness-90',
        'focus:ring-im-warning/30'
      ),
    };

    // Size styles
    const sizeStyles = {
      sm: 'px-3 py-1 text-sm',
      md: 'px-4 py-2 text-base',
      lg: 'px-5 py-3 text-lg',
    };

    // Spinner (loading state)
    const spinner = (
      <svg
        className="animate-spin h-4 w-4"
        xmlns="http://www.w3.org/2000/svg"
        fill="none"
        viewBox="0 0 24 24"
        aria-hidden="true"
      >
        <circle
          className="opacity-25"
          cx="12"
          cy="12"
          r="10"
          stroke="currentColor"
          strokeWidth="4"
        />
        <path
          className="opacity-75"
          fill="currentColor"
          d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"
        />
      </svg>
    );

    // ========================================
    // RENDER
    // ========================================

    return (
      <button
        ref={ref}
        type={type}
        className={clsx(baseStyles, variantStyles[variant], sizeStyles[size], className)}
        disabled={disabled || loading}
        aria-label={ariaLabel}
        aria-busy={loading}
        {...rest}
      >
        {/* Left Icon / Spinner (si está loading) */}
        {loading ? spinner : leftIcon}

        {/* Content */}
        <span>{children}</span>

        {/* Right Icon (oculto si está loading) */}
        {!loading && rightIcon}
      </button>
    );
  }
);

// Display name para React DevTools
IMButton.displayName = 'IMButton';

// ========================================
// EXPORT DEFAULT
// ========================================

export default IMButton;
