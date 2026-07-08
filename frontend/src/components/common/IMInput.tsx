import React, { forwardRef } from 'react';
import clsx from 'clsx';

/**
 * IMInput - Componente de input atómico de IdeaMakers
 *
 * Soporte para input, textarea, select con validación y estados
 *
 * @example
 * ```tsx
 * <IMInput
 *   label="Email"
 *   type="email"
 *   placeholder="tu@email.com"
 *   helperText="Ingresa tu email corporativo"
 *   error={errors.email}
 * />
 * ```
 */

// ========================================
// TYPES
// ========================================

export type IMInputVariant = 'input' | 'textarea' | 'select';

export interface IMInputProps extends Omit<React.InputHTMLAttributes<HTMLInputElement>, 'size'> {
  /**
   * Tipo de input (por defecto usa <input>)
   * @default 'input'
   */
  variant?: IMInputVariant;

  /**
   * Label del input
   */
  label?: string;

  /**
   * Texto de ayuda debajo del input
   */
  helperText?: string;

  /**
   * Mensaje de error (si existe, muestra estado de error)
   */
  error?: string;

  /**
   * Estado de éxito (muestra borde verde)
   */
  success?: boolean;

  /**
   * Icono a la izquierda (opcional)
   */
  leftIcon?: React.ReactNode;

  /**
   * Icono a la derecha (opcional)
   */
  rightIcon?: React.ReactNode;

  /**
   * Full width (ancho completo)
   * @default true
   */
  fullWidth?: boolean;

  /**
   * Clases CSS adicionales para el input
   */
  className?: string;

  /**
   * Clases CSS para el container
   */
  containerClassName?: string;

  /**
   * Opciones para select (si variant="select")
   */
  options?: Array<{ value: string | number; label: string; disabled?: boolean }>;

  /**
   * Filas para textarea (si variant="textarea")
   * @default 4
   */
  rows?: number;
}

// ========================================
// COMPONENT
// ========================================

export const IMInput = forwardRef<HTMLInputElement | HTMLTextAreaElement | HTMLSelectElement, IMInputProps>(
  (
    {
      variant = 'input',
      label,
      helperText,
      error,
      success = false,
      leftIcon,
      rightIcon,
      fullWidth = true,
      className,
      containerClassName,
      options,
      rows = 4,
      id,
      disabled,
      required,
      ...rest
    },
    ref
  ) => {
    // Generate unique ID if not provided
    const inputId = id || `im-input-${Math.random().toString(36).substr(2, 9)}`;
    const errorId = `${inputId}-error`;
    const helperId = `${inputId}-helper`;

    // ========================================
    // STYLES
    // ========================================

    const containerStyles = clsx(
      fullWidth ? 'w-full' : 'w-auto',
      containerClassName
    );

    const baseInputStyles = clsx(
      'w-full px-3 py-2 rounded-md',
      'text-im-neutral-900 placeholder:text-im-neutral-500',
      'border transition-all duration-200',
      'focus:outline-none focus:ring-4',
      'disabled:opacity-50 disabled:cursor-not-allowed disabled:bg-im-neutral-100',
      className
    );

    const variantStyles = error
      ? 'border-im-danger focus:ring-im-danger/30 focus:border-im-danger'
      : success
      ? 'border-im-success focus:ring-im-success/30 focus:border-im-success'
      : 'border-im-neutral-300 focus:ring-im-orange-soft/30 focus:border-im-orange';

    const inputStyles = clsx(baseInputStyles, variantStyles);

    // Container with icons
    const hasIcons = leftIcon || rightIcon;

    // ========================================
    // RENDER INPUT
    // ========================================

    const renderInput = () => {
      if (variant === 'textarea') {
        return (
          <textarea
            ref={ref as React.Ref<HTMLTextAreaElement>}
            id={inputId}
            className={inputStyles}
            disabled={disabled}
            aria-invalid={!!error}
            aria-describedby={error ? errorId : helperText ? helperId : undefined}
            aria-required={required}
            rows={rows}
            {...(rest as React.TextareaHTMLAttributes<HTMLTextAreaElement>)}
          />
        );
      }

      if (variant === 'select') {
        return (
          <select
            ref={ref as React.Ref<HTMLSelectElement>}
            id={inputId}
            className={inputStyles}
            disabled={disabled}
            aria-invalid={!!error}
            aria-describedby={error ? errorId : helperText ? helperId : undefined}
            aria-required={required}
            {...(rest as React.SelectHTMLAttributes<HTMLSelectElement>)}
          >
            {options?.map((option) => (
              <option
                key={option.value}
                value={option.value}
                disabled={option.disabled}
              >
                {option.label}
              </option>
            ))}
          </select>
        );
      }

      // Default: input
      return (
        <input
          ref={ref as React.Ref<HTMLInputElement>}
          id={inputId}
          className={inputStyles}
          disabled={disabled}
          aria-invalid={!!error}
          aria-describedby={error ? errorId : helperText ? helperId : undefined}
          aria-required={required}
          {...(rest as React.InputHTMLAttributes<HTMLInputElement>)}
        />
      );
    };

    // ========================================
    // RENDER
    // ========================================

    return (
      <div className={containerStyles}>
        {/* Label */}
        {label && (
          <label htmlFor={inputId} className="im-label">
            {label}
            {required && <span className="text-im-danger ml-1">*</span>}
          </label>
        )}

        {/* Input with icons */}
        {hasIcons ? (
          <div className="relative">
            {leftIcon && (
              <div className="absolute left-3 top-1/2 -translate-y-1/2 text-im-neutral-500">
                {leftIcon}
              </div>
            )}

            <div className={clsx(leftIcon && 'pl-10', rightIcon && 'pr-10')}>
              {renderInput()}
            </div>

            {rightIcon && (
              <div className="absolute right-3 top-1/2 -translate-y-1/2 text-im-neutral-500">
                {rightIcon}
              </div>
            )}
          </div>
        ) : (
          renderInput()
        )}

        {/* Error message */}
        {error && (
          <p id={errorId} className="im-error-text" role="alert">
            {error}
          </p>
        )}

        {/* Helper text (solo si no hay error) */}
        {!error && helperText && (
          <p id={helperId} className="im-helper-text">
            {helperText}
          </p>
        )}
      </div>
    );
  }
);

IMInput.displayName = 'IMInput';

export default IMInput;
