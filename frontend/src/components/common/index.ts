/**
 * IdeaMakers Design System - Componentes Atómicos
 *
 * Export centralizado de todos los componentes del sistema de diseño
 *
 * @example
 * ```tsx
 * import { IMButton, IMInput, IMCard, Logo } from '@/components/common';
 * ```
 */

// ========================================
// BUTTONS
// ========================================
export { IMButton } from './IMButton';
export type { IMButtonProps, IMButtonVariant, IMButtonSize } from './IMButton';

// ========================================
// INPUTS
// ========================================
export { IMInput } from './IMInput';
export type { IMInputProps, IMInputVariant } from './IMInput';

// ========================================
// CARDS
// ========================================
export { IMCard } from './IMCard';
export type { IMCardProps } from './IMCard';

// ========================================
// BADGES
// ========================================
export {
  IMBadge,
  OnlineBadge,
  OfflineBadge,
  MaintenanceBadge,
  ErrorBadge,
} from './IMBadge';
export type { IMBadgeProps, IMBadgeVariant, IMBadgeSize } from './IMBadge';

// ========================================
// MODALS
// ========================================
export { IMModal, IMConfirmModal } from './IMModal';
export type {
  IMModalProps,
  IMConfirmModalProps,
  IMModalVariant,
  IMModalSize,
} from './IMModal';

// ========================================
// LOGO
// ========================================
export { Logo, LogoNavbar, LogoLogin, LogoSidebar, LogoFooter } from './Logo';
export type { LogoProps, LogoVariant, LogoFormat } from './Logo';
