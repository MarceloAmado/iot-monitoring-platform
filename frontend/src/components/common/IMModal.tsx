import React, { useEffect, useRef } from 'react';
import clsx from 'clsx';
import { IMButton } from './IMButton';

/**
 * IMModal - Componente de modal accesible de IdeaMakers
 *
 * Modal con overlay, focus trap, ESC to close, y accesibilidad WCAG 2.1
 *
 * @example
 * ```tsx
 * <IMModal
 *   isOpen={isOpen}
 *   onClose={() => setIsOpen(false)}
 *   title="Confirmar Eliminación"
 *   variant="danger"
 *   footer={
 *     <>
 *       <IMButton variant="secondary" onClick={onClose}>Cancelar</IMButton>
 *       <IMButton variant="danger" onClick={onConfirm}>Eliminar</IMButton>
 *     </>
 *   }
 * >
 *   <p>¿Estás seguro de eliminar este device?</p>
 * </IMModal>
 * ```
 */

// ========================================
// TYPES
// ========================================

export type IMModalVariant = 'default' | 'danger' | 'success' | 'warning';
export type IMModalSize = 'sm' | 'md' | 'lg' | 'xl' | 'full';

export interface IMModalProps {
  /**
   * Estado de apertura del modal
   */
  isOpen: boolean;

  /**
   * Callback al cerrar el modal
   */
  onClose: () => void;

  /**
   * Título del modal
   */
  title?: string;

  /**
   * Subtítulo o descripción
   */
  subtitle?: string;

  /**
   * Contenido del modal
   */
  children: React.ReactNode;

  /**
   * Footer del modal (botones de acción)
   */
  footer?: React.ReactNode;

  /**
   * Variante de color (afecta el color del título)
   * @default 'default'
   */
  variant?: IMModalVariant;

  /**
   * Tamaño del modal
   * @default 'md'
   */
  size?: IMModalSize;

  /**
   * Mostrar botón de cerrar (X)
   * @default true
   */
  showCloseButton?: boolean;

  /**
   * Cerrar al hacer click en el overlay
   * @default true
   */
  closeOnOverlayClick?: boolean;

  /**
   * Cerrar al presionar ESC
   * @default true
   */
  closeOnEscape?: boolean;

  /**
   * Clases CSS adicionales para el modal content
   */
  className?: string;

  /**
   * Clases CSS para el overlay
   */
  overlayClassName?: string;
}

// ========================================
// COMPONENT
// ========================================

export const IMModal: React.FC<IMModalProps> = ({
  isOpen,
  onClose,
  title,
  subtitle,
  children,
  footer,
  variant = 'default',
  size = 'md',
  showCloseButton = true,
  closeOnOverlayClick = true,
  closeOnEscape = true,
  className,
  overlayClassName,
}) => {
  const modalRef = useRef<HTMLDivElement>(null);
  const previousActiveElement = useRef<HTMLElement | null>(null);

  // ========================================
  // FOCUS TRAP & ACCESSIBILITY
  // ========================================

  useEffect(() => {
    if (isOpen) {
      // Guardar elemento activo antes de abrir el modal
      previousActiveElement.current = document.activeElement as HTMLElement;

      // Mover focus al modal
      modalRef.current?.focus();

      // Prevenir scroll del body
      document.body.style.overflow = 'hidden';
    } else {
      // Restaurar focus al elemento anterior
      previousActiveElement.current?.focus();

      // Restaurar scroll del body
      document.body.style.overflow = '';
    }

    return () => {
      document.body.style.overflow = '';
    };
  }, [isOpen]);

  // ESC key handler
  useEffect(() => {
    if (!isOpen || !closeOnEscape) return;

    const handleEscape = (e: KeyboardEvent) => {
      if (e.key === 'Escape') {
        onClose();
      }
    };

    document.addEventListener('keydown', handleEscape);
    return () => document.removeEventListener('keydown', handleEscape);
  }, [isOpen, closeOnEscape, onClose]);

  // ========================================
  // HANDLERS
  // ========================================

  const handleOverlayClick = (e: React.MouseEvent) => {
    if (e.target === e.currentTarget && closeOnOverlayClick) {
      onClose();
    }
  };

  // ========================================
  // STYLES
  // ========================================

  const sizeStyles = {
    sm: 'max-w-sm',
    md: 'max-w-2xl',
    lg: 'max-w-4xl',
    xl: 'max-w-6xl',
    full: 'max-w-full mx-4',
  };

  const variantTitleColors = {
    default: 'text-im-blue',
    danger: 'text-im-danger',
    success: 'text-im-success',
    warning: 'text-im-warning',
  };

  const overlayStyles = clsx('im-modal-overlay', overlayClassName);

  const modalStyles = clsx(
    'im-modal-content',
    sizeStyles[size],
    'animate-scale-in',
    className
  );

  // ========================================
  // RENDER
  // ========================================

  if (!isOpen) return null;

  return (
    <div
      className={overlayStyles}
      onClick={handleOverlayClick}
      role="dialog"
      aria-modal="true"
      aria-labelledby={title ? 'modal-title' : undefined}
    >
      <div
        ref={modalRef}
        className={modalStyles}
        tabIndex={-1}
        role="document"
      >
        {/* Header */}
        {(title || subtitle || showCloseButton) && (
          <div className="px-6 py-4 border-b border-im-neutral-100">
            <div className="flex items-start justify-between gap-4">
              <div className="flex-1 min-w-0">
                {title && (
                  <h2
                    id="modal-title"
                    className={clsx(
                      'font-montserrat text-xl font-bold',
                      variantTitleColors[variant]
                    )}
                  >
                    {title}
                  </h2>
                )}
                {subtitle && (
                  <p className="text-sm text-im-neutral-500 mt-1">{subtitle}</p>
                )}
              </div>

              {showCloseButton && (
                <button
                  type="button"
                  onClick={onClose}
                  className="flex-shrink-0 text-im-neutral-500 hover:text-im-neutral-900 transition-colors"
                  aria-label="Cerrar modal"
                >
                  <svg
                    className="w-6 h-6"
                    fill="none"
                    viewBox="0 0 24 24"
                    stroke="currentColor"
                  >
                    <path
                      strokeLinecap="round"
                      strokeLinejoin="round"
                      strokeWidth={2}
                      d="M6 18L18 6M6 6l12 12"
                    />
                  </svg>
                </button>
              )}
            </div>
          </div>
        )}

        {/* Body */}
        <div className="px-6 py-4 overflow-y-auto max-h-[60vh]">
          {children}
        </div>

        {/* Footer */}
        {footer && (
          <div className="px-6 py-4 border-t border-im-neutral-100 flex items-center justify-end gap-3">
            {footer}
          </div>
        )}
      </div>
    </div>
  );
};

// ========================================
// CONFIRM MODAL (Shortcut Helper)
// ========================================

export interface IMConfirmModalProps {
  isOpen: boolean;
  onClose: () => void;
  onConfirm: () => void;
  title: string;
  message: string;
  confirmText?: string;
  cancelText?: string;
  variant?: 'danger' | 'warning' | 'success';
  loading?: boolean;
}

export const IMConfirmModal: React.FC<IMConfirmModalProps> = ({
  isOpen,
  onClose,
  onConfirm,
  title,
  message,
  confirmText = 'Confirmar',
  cancelText = 'Cancelar',
  variant = 'danger',
  loading = false,
}) => {
  return (
    <IMModal
      isOpen={isOpen}
      onClose={onClose}
      title={title}
      variant={variant}
      size="sm"
      footer={
        <>
          <IMButton variant="secondary" onClick={onClose} disabled={loading}>
            {cancelText}
          </IMButton>
          <IMButton variant={variant} onClick={onConfirm} loading={loading}>
            {confirmText}
          </IMButton>
        </>
      }
    >
      <p className="text-im-neutral-700">{message}</p>
    </IMModal>
  );
};

export default IMModal;
