import React from 'react';
import clsx from 'clsx';

/**
 * Logo - Componente helper para logotipo IdeaMakers
 *
 * Maneja automáticamente SVG/PNG fallback y diferentes variantes
 *
 * @example
 * ```tsx
 * // Navbar
 * <Logo variant="horizontal" height={40} />
 *
 * // Sidebar colapsado
 * <Logo variant="isotipo" height={48} />
 *
 * // Login page
 * <Logo variant="horizontal" height={120} />
 *
 * // Logo blanco (sobre fondo oscuro)
 * <Logo variant="horizontal-white" height={40} />
 * ```
 */

// ========================================
// TYPES
// ========================================

export type LogoVariant = 'horizontal' | 'isotipo' | 'horizontal-white';
export type LogoFormat = 'svg' | 'png';

export interface LogoProps {
  /**
   * Variante del logo
   * @default 'horizontal'
   */
  variant?: LogoVariant;

  /**
   * Altura del logo en píxeles
   * @default 40
   */
  height?: number;

  /**
   * Ancho del logo (opcional, si no se especifica se calcula automáticamente)
   */
  width?: number;

  /**
   * Formato preferido (intenta SVG primero, fallback a PNG)
   * @default 'svg'
   */
  format?: LogoFormat;

  /**
   * Clases CSS adicionales
   */
  className?: string;

  /**
   * OnClick handler (hace el logo clickable)
   */
  onClick?: () => void;

  /**
   * Alt text (por defecto "IdeaMakers")
   */
  alt?: string;
}

// ========================================
// CONSTANTS
// ========================================

const LOGO_PATHS = {
  horizontal: {
    svg: '/assets/logos/ideamakers-horizontal.svg',
    png: '/assets/logos/ideamakers-horizontal.png',
  },
  isotipo: {
    svg: '/assets/logos/ideamakers-isotipo.svg',
    png: '/assets/logos/ideamakers-isotipo.png',
  },
  'horizontal-white': {
    svg: '/assets/logos/ideamakers-white.svg',
    png: '/assets/logos/ideamakers-horizontal.png', // Fallback a color si no existe blanco
  },
};

// ========================================
// COMPONENT
// ========================================

export const Logo: React.FC<LogoProps> = ({
  variant = 'horizontal',
  height = 40,
  width,
  format = 'svg',
  className,
  onClick,
  alt = 'IdeaMakers',
}) => {
  // ========================================
  // LOGIC
  // ========================================

  const logoPath = LOGO_PATHS[variant][format];

  // Auto-calculate width for isotipo (square)
  const calculatedWidth = width || (variant === 'isotipo' ? height : undefined);

  const imgStyles = clsx(
    'object-contain',
    onClick && 'cursor-pointer hover:opacity-90 transition-opacity',
    className
  );

  // ========================================
  // HANDLERS
  // ========================================

  const handleClick = () => {
    if (onClick) {
      onClick();
    }
  };

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (onClick && (e.key === 'Enter' || e.key === ' ')) {
      e.preventDefault();
      onClick();
    }
  };

  // ========================================
  // RENDER
  // ========================================

  if (onClick) {
    return (
      <button
        type="button"
        onClick={handleClick}
        onKeyDown={handleKeyDown}
        className="focus:outline-none focus:ring-4 focus:ring-im-orange-soft/30 rounded"
        aria-label={`${alt} - Ir a inicio`}
      >
        <img
          src={logoPath}
          alt={alt}
          height={height}
          width={calculatedWidth}
          className={imgStyles}
          style={{ height: `${height}px`, width: calculatedWidth ? `${calculatedWidth}px` : 'auto' }}
        />
      </button>
    );
  }

  return (
    <img
      src={logoPath}
      alt={alt}
      height={height}
      width={calculatedWidth}
      className={imgStyles}
      style={{ height: `${height}px`, width: calculatedWidth ? `${calculatedWidth}px` : 'auto' }}
    />
  );
};

// ========================================
// SHORTCUTS (Variantes comunes con tamaños predefinidos)
// ========================================

/**
 * LogoNavbar - Logo para navbar (40px)
 */
export const LogoNavbar: React.FC<Omit<LogoProps, 'variant' | 'height'>> = (props) => (
  <Logo variant="horizontal" height={40} {...props} />
);

/**
 * LogoLogin - Logo para login page (120px)
 */
export const LogoLogin: React.FC<Omit<LogoProps, 'variant' | 'height'>> = (props) => (
  <Logo variant="horizontal" height={120} {...props} />
);

/**
 * LogoSidebar - Isotipo para sidebar colapsado (48px)
 */
export const LogoSidebar: React.FC<Omit<LogoProps, 'variant' | 'height'>> = (props) => (
  <Logo variant="isotipo" height={48} {...props} />
);

/**
 * LogoFooter - Logo para footer (28px)
 */
export const LogoFooter: React.FC<Omit<LogoProps, 'variant' | 'height'>> = (props) => (
  <Logo variant="horizontal" height={28} {...props} />
);

export default Logo;
