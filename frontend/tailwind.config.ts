import type { Config } from 'tailwindcss'

/**
 * Tailwind CSS Configuration - IdeaMakers IoT Monitoring
 *
 * Sistema de diseño basado en tokens IdeaMakers
 * Paleta: Azul profundo (#0F3C57) + Naranja creativo (#F57C20)
 *
 * @see design-tokens.json
 */
export default {
  content: [
    './index.html',
    './src/**/*.{js,ts,jsx,tsx}',
  ],
  theme: {
    extend: {
      // ========================================
      // COLORS - IdeaMakers Brand Palette
      // ========================================
      colors: {
        // Brand colors
        'im-blue': '#0F3C57',
        'im-blue-hover': '#0a2d42',
        'im-blue-light': '#1a5170',
        'im-orange': '#F57C20',
        'im-orange-hover': '#e66e12',
        'im-orange-soft': '#F9A45C',
        'im-orange-soft-hover': '#f89740',

        // Background
        'im-bg': '#F5F5F5',
        'im-white': '#FFFFFF',

        // Neutrals
        'im-neutral': {
          900: '#0B1B26',
          700: '#556E7A',
          500: '#9AA9B3',
          300: '#D6E0E6',
          100: '#F0F4F7',
        },

        // Status colors
        'im-success': '#2FB46E',
        'im-success-light': '#e8f6ef',
        'im-warning': '#F2C037',
        'im-warning-light': '#fef8e7',
        'im-danger': '#E04B4B',
        'im-danger-light': '#fde8e8',
        'im-info': '#4A90E2',
        'im-info-light': '#e8f2fc',

        // Device status (semantic colors)
        'device-online': '#2FB46E',
        'device-offline': '#9AA9B3',
        'device-maintenance': '#F2C037',
        'device-error': '#E04B4B',
      },

      // ========================================
      // TYPOGRAPHY
      // ========================================
      fontFamily: {
        sans: ['"Open Sans"', 'ui-sans-serif', 'system-ui'],
        montserrat: ['"Montserrat"', 'sans-serif'],
      },
      fontSize: {
        'xs': ['0.75rem', { lineHeight: '1rem' }],      // 12px
        'sm': ['0.875rem', { lineHeight: '1.25rem' }],  // 14px
        'base': ['1rem', { lineHeight: '1.5rem' }],     // 16px
        'lg': ['1.125rem', { lineHeight: '1.75rem' }],  // 18px
        'xl': ['1.25rem', { lineHeight: '1.75rem' }],   // 20px
        '2xl': ['1.5rem', { lineHeight: '2rem' }],      // 24px
        '3xl': ['1.875rem', { lineHeight: '2.25rem' }], // 30px
        '4xl': ['2.25rem', { lineHeight: '2.5rem' }],   // 36px
      },
      fontWeight: {
        normal: '400',
        medium: '500',
        semibold: '600',
        bold: '700',
        extrabold: '800',
      },

      // ========================================
      // SPACING
      // ========================================
      spacing: {
        'xs': '0.25rem',  // 4px
        'sm': '0.5rem',   // 8px
        'md': '1rem',     // 16px
        'lg': '1.5rem',   // 24px
        'xl': '2rem',     // 32px
        '2xl': '3rem',    // 48px
        '3xl': '4rem',    // 64px

        // Layout-specific
        'sidebar-expanded': '280px',
        'sidebar-collapsed': '72px',
        'topbar': '64px',
      },

      // ========================================
      // BORDER RADIUS
      // ========================================
      borderRadius: {
        'none': '0',
        'sm': '0.375rem',   // 6px
        'md': '0.75rem',    // 12px
        'lg': '1rem',       // 16px
        'full': '9999px',
      },

      // ========================================
      // SHADOWS
      // ========================================
      boxShadow: {
        'im-card': '0 6px 18px rgba(15, 60, 87, 0.08)',
        'im-card-hover': '0 8px 24px rgba(15, 60, 87, 0.12)',
        'im-modal': '0 20px 60px rgba(15, 60, 87, 0.25)',
        'im-focus': '0 0 0 3px rgba(245, 124, 32, 0.15)',
      },

      // ========================================
      // TRANSITIONS
      // ========================================
      transitionDuration: {
        'fast': '150ms',
        'base': '200ms',
        'slow': '300ms',
      },
      transitionTimingFunction: {
        'smooth': 'cubic-bezier(0.4, 0, 0.2, 1)',
      },

      // ========================================
      // Z-INDEX
      // ========================================
      zIndex: {
        'base': '0',
        'dropdown': '10',
        'sticky': '20',
        'modal': '50',
        'toast': '100',
      },

      // ========================================
      // CONTAINER
      // ========================================
      container: {
        center: true,
        padding: {
          DEFAULT: '1rem',
          sm: '1rem',
          md: '1.5rem',
          lg: '2rem',
          xl: '2rem',
          '2xl': '2rem',
        },
        screens: {
          sm: '640px',
          md: '768px',
          lg: '1024px',
          xl: '1280px',
          '2xl': '1440px',
        },
      },

      // ========================================
      // BREAKPOINTS (Explicitly defined for documentation)
      // ========================================
      screens: {
        'sm': '640px',   // Teléfonos grandes / landscape
        'md': '768px',   // Tablets
        'lg': '1024px',  // Laptops
        'xl': '1280px',  // Desktop / dashboards
        '2xl': '1536px', // Pantallas grandes (opcional)
      },

      // ========================================
      // ANIMATIONS
      // ========================================
      keyframes: {
        'fade-in': {
          '0%': { opacity: '0' },
          '100%': { opacity: '1' },
        },
        'slide-up': {
          '0%': { transform: 'translateY(10px)', opacity: '0' },
          '100%': { transform: 'translateY(0)', opacity: '1' },
        },
        'slide-down': {
          '0%': { transform: 'translateY(-10px)', opacity: '0' },
          '100%': { transform: 'translateY(0)', opacity: '1' },
        },
        'scale-in': {
          '0%': { transform: 'scale(0.95)', opacity: '0' },
          '100%': { transform: 'scale(1)', opacity: '1' },
        },
      },
      animation: {
        'fade-in': 'fade-in 200ms ease-out',
        'slide-up': 'slide-up 200ms ease-out',
        'slide-down': 'slide-down 200ms ease-out',
        'scale-in': 'scale-in 200ms ease-out',
      },
    },
  },
  plugins: [],
} satisfies Config
