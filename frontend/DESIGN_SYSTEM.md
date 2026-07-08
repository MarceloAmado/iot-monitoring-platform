# 🎨 IdeaMakers Design System - Guía de Uso

**Sistema de diseño para IoT Monitoring Platform**
**Versión:** 1.0.0
**Fecha:** 2025-10-22

---

## 📋 Tabla de Contenidos

1. [Introducción](#introducción)
2. [Setup y Configuración](#setup-y-configuración)
3. [Design Tokens](#design-tokens)
4. [Componentes Atómicos](#componentes-atómicos)
5. [Paleta de Colores](#paleta-de-colores)
6. [Tipografía](#tipografía)
7. [Espaciado y Grid](#espaciado-y-grid)
8. [Ejemplos de Uso](#ejemplos-de-uso)
9. [Guía de Accesibilidad](#guía-de-accesibilidad)

---

## 🚀 Introducción

Este sistema de diseño implementa la identidad visual de **IdeaMakers** en la plataforma IoT Monitoring, basado en:

- **Paleta principal:** Azul profundo (#0F3C57) + Naranja creativo (#F57C20)
- **Tipografía:** Montserrat (headings) + Open Sans (body)
- **Filosofía:** Mobile-first, accesible, profesional

### Principios de Diseño

1. **Consistencia visual** - Todos los componentes siguen los mismos tokens
2. **Accesibilidad (WCAG 2.1 AA)** - Contraste ≥4.5:1, navegación por teclado
3. **Responsive design** - 5 breakpoints (sm, md, lg, xl, 2xl)
4. **Performance** - Optimizado para dashboards en tiempo real

---

## ⚙️ Setup y Configuración

### 1. Archivos Clave

```
frontend/
├── design-tokens.json          # Tokens de diseño (fuente de verdad)
├── tailwind.config.ts          # Configuración Tailwind con tokens IM
├── src/styles/globals.css      # Estilos globales + Google Fonts
└── src/components/common/      # Componentes atómicos IM
    ├── IMButton.tsx
    ├── IMInput.tsx            (próximo)
    ├── IMCard.tsx             (próximo)
    └── ...
```

### 2. Importar Estilos Globales

En `src/main.tsx`:

```tsx
import './styles/globals.css';
```

### 3. Usar Componentes IM

```tsx
import { IMButton } from '@/components/common/IMButton';

function MyComponent() {
  return (
    <IMButton variant="primary" size="md">
      Guardar Cambios
    </IMButton>
  );
}
```

---

## 🎨 Design Tokens

Los tokens están definidos en `design-tokens.json` y sincronizados con:
- `tailwind.config.ts` (clases de Tailwind)
- `globals.css` (variables CSS)

### Ejemplo de Token

```json
{
  "color": {
    "brand": {
      "deep-blue": "#0F3C57",
      "orange": "#F57C20"
    }
  }
}
```

Uso en código:

```tsx
// Tailwind class
<div className="bg-im-blue text-white">...</div>

// CSS variable
<div style={{ backgroundColor: 'var(--im-blue)' }}>...</div>
```

---

## 🎨 Paleta de Colores

### Colores de Marca

| Nombre | Hex | Uso |
|--------|-----|-----|
| **im-blue** | `#0F3C57` | Color primario, topbar, títulos |
| **im-blue-hover** | `#0a2d42` | Hover state de azul |
| **im-orange** | `#F57C20` | CTAs, accents, botones primarios |
| **im-orange-hover** | `#e66e12` | Hover de naranja |
| **im-orange-soft** | `#F9A45C` | Highlights, notificaciones |

### Colores Neutrales

| Nombre | Hex | Uso |
|--------|-----|-----|
| **im-neutral-900** | `#0B1B26` | Texto principal |
| **im-neutral-700** | `#556E7A` | Texto secundario |
| **im-neutral-500** | `#9AA9B3` | Placeholders, disabled |
| **im-neutral-300** | `#D6E0E6` | Bordes, separadores |
| **im-neutral-100** | `#F0F4F7` | Backgrounds suaves |

### Colores de Estado (Semantic)

| Nombre | Hex | Uso |
|--------|-----|-----|
| **im-success** | `#2FB46E` | Éxito, device online |
| **im-warning** | `#F2C037` | Advertencias, maintenance |
| **im-danger** | `#E04B4B` | Errores, device offline crítico |
| **im-info** | `#4A90E2` | Información, hints |

### Uso en Tailwind

```tsx
// Background
<div className="bg-im-blue">...</div>

// Text color
<h1 className="text-im-orange">Título</h1>

// Border
<input className="border-im-neutral-300 focus:border-im-orange" />

// Status badges
<span className="bg-im-success-light text-im-success">Online</span>
```

---

## 📝 Tipografía

### Fuentes

**Headings (Montserrat):**
```tsx
<h1 className="font-montserrat text-4xl font-bold">Título Grande</h1>
```

**Body (Open Sans):**
```tsx
<p className="font-sans text-base">Texto de cuerpo</p>
```

### Escala Tipográfica

| Clase Tailwind | Tamaño | Uso |
|----------------|--------|-----|
| `text-xs` | 12px | Captions, helper text |
| `text-sm` | 14px | Body pequeño, labels |
| `text-base` | 16px | Body principal |
| `text-lg` | 18px | Subtítulos |
| `text-xl` | 20px | Títulos H3 |
| `text-2xl` | 24px | Títulos H2 |
| `text-3xl` | 30px | Títulos H1 secundarios |
| `text-4xl` | 36px | Títulos H1 principales |

### Font Weights

| Clase | Peso | Uso |
|-------|------|-----|
| `font-normal` | 400 | Body text |
| `font-medium` | 500 | Énfasis suave |
| `font-semibold` | 600 | Buttons, labels |
| `font-bold` | 700 | Headings |
| `font-extrabold` | 800 | Títulos hero |

---

## 📐 Espaciado y Grid

### Sistema de Espaciado

```tsx
// Padding
<div className="p-md">       // 16px (1rem)
<div className="p-lg">       // 24px (1.5rem)
<div className="p-xl">       // 32px (2rem)

// Margin
<div className="mb-md">      // margin-bottom: 16px
<div className="mt-lg">      // margin-top: 24px

// Gap (flex/grid)
<div className="flex gap-md"> // 16px entre elementos
```

### Breakpoints (Mobile-first)

| Breakpoint | Min-width | Uso |
|------------|-----------|-----|
| **base** | 0px | Mobile (default) |
| **sm** | 640px | Teléfonos grandes |
| **md** | 768px | Tablets |
| **lg** | 1024px | Laptops |
| **xl** | 1280px | Desktop dashboards |
| **2xl** | 1536px | Pantallas grandes |

### Ejemplo Responsive

```tsx
<div className="
  grid grid-cols-1       /* Mobile: 1 columna */
  md:grid-cols-2         /* Tablet: 2 columnas */
  lg:grid-cols-3         /* Desktop: 3 columnas */
  gap-4 md:gap-6
">
  <div>Card 1</div>
  <div>Card 2</div>
  <div>Card 3</div>
</div>
```

---

## 🧩 Componentes Atómicos

### IMButton

**Variantes:** primary, secondary, ghost, danger
**Tamaños:** sm, md, lg

```tsx
import { IMButton } from '@/components/common/IMButton';

// Primary button (CTA)
<IMButton variant="primary" size="md">
  Guardar Cambios
</IMButton>

// Secondary button
<IMButton variant="secondary" size="sm">
  Cancelar
</IMButton>

// Ghost button (para menús)
<IMButton variant="ghost">
  Ver Detalles
</IMButton>

// Danger button (destructive)
<IMButton variant="danger">
  Eliminar Device
</IMButton>

// Con loading state
<IMButton variant="primary" loading={isSubmitting}>
  Guardando...
</IMButton>

// Con iconos
<IMButton variant="primary" leftIcon={<SaveIcon />}>
  Guardar
</IMButton>
```

### Utility Classes (globals.css)

#### Botones

```tsx
<button className="im-btn-primary im-btn-md">
  Botón Primario
</button>

<button className="im-btn-secondary im-btn-sm">
  Botón Secundario
</button>
```

#### Cards

```tsx
<div className="im-card">
  <div className="im-card-header">
    <h3>Título del Card</h3>
  </div>
  <p>Contenido del card</p>
  <div className="im-card-footer">
    <button>Acción</button>
  </div>
</div>
```

#### Inputs

```tsx
<label className="im-label">
  Email
</label>
<input
  type="email"
  className="im-input"
  placeholder="tu@email.com"
/>
<span className="im-helper-text">
  Ingresa tu email corporativo
</span>
```

#### Badges (Status Pills)

```tsx
// Success (device online)
<span className="im-badge-success">Online</span>

// Warning (maintenance)
<span className="im-badge-warning">Mantenimiento</span>

// Danger (error)
<span className="im-badge-danger">Error</span>

// Specific device status
<span className="im-status-online">Online</span>
<span className="im-status-offline">Offline</span>
<span className="im-status-maintenance">Mantenimiento</span>
<span className="im-status-error">Error</span>
```

#### Tables

```tsx
<table className="im-table">
  <thead>
    <tr>
      <th>Device</th>
      <th>Status</th>
      <th>Last Seen</th>
    </tr>
  </thead>
  <tbody>
    <tr>
      <td>ESP32_LAB_001</td>
      <td><span className="im-status-online">Online</span></td>
      <td>2 min ago</td>
    </tr>
  </tbody>
</table>
```

---

## 📖 Ejemplos de Uso

### Login Page (Split Layout)

```tsx
<div className="min-h-screen grid lg:grid-cols-2">
  {/* Left: Visual */}
  <div className="hidden lg:block bg-gradient-to-br from-im-blue to-im-blue-light">
    <div className="flex items-center justify-center h-full p-12">
      <img src="/hero-iot.jpg" alt="IoT Monitoring" />
    </div>
  </div>

  {/* Right: Form */}
  <div className="flex items-center justify-center p-6">
    <div className="w-full max-w-md">
      <img src="/logo.svg" alt="IdeaMakers" className="h-12 mb-8" />
      <h1 className="font-montserrat text-3xl font-bold text-im-blue mb-6">
        Iniciar Sesión
      </h1>
      <form className="space-y-4">
        <div>
          <label className="im-label">Email</label>
          <input type="email" className="im-input" />
        </div>
        <div>
          <label className="im-label">Contraseña</label>
          <input type="password" className="im-input" />
        </div>
        <IMButton variant="primary" fullWidth>
          Ingresar
        </IMButton>
      </form>
    </div>
  </div>
</div>
```

### Dashboard Card Grid

```tsx
<div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
  <div className="im-card">
    <h3 className="text-sm font-semibold text-im-neutral-700 mb-2">
      Devices Online
    </h3>
    <p className="text-3xl font-bold text-im-success">12</p>
    <p className="text-xs text-im-neutral-500 mt-1">
      de 15 totales
    </p>
  </div>
  {/* Más cards... */}
</div>
```

---

## ♿ Guía de Accesibilidad

### Principios Clave

1. **Contraste de color:** Mínimo 4.5:1 para texto normal
2. **Navegación por teclado:** Todos los elementos interactivos accesibles con Tab
3. **Focus visible:** Ring naranja en elementos con foco
4. **ARIA labels:** Requeridos en botones sin texto

### Ejemplos

```tsx
// Button con aria-label
<IMButton
  variant="primary"
  ariaLabel="Guardar cambios del dispositivo"
>
  <SaveIcon />
</IMButton>

// Input con aria-describedby
<input
  type="email"
  className="im-input"
  aria-invalid={hasError}
  aria-describedby="email-error"
/>
{hasError && (
  <span id="email-error" className="im-error-text">
    Email inválido
  </span>
)}

// Loading state
<IMButton loading={isLoading} aria-busy={isLoading}>
  Guardando...
</IMButton>
```

### Testing de Accesibilidad

```bash
# Instalar axe-core
npm install -D @axe-core/react

# Usar en desarrollo
import React from 'react';
import ReactDOM from 'react-dom';
if (process.env.NODE_ENV !== 'production') {
  import('@axe-core/react').then(axe => {
    axe.default(React, ReactDOM, 1000);
  });
}
```

---

## 🔄 Próximos Componentes

- [ ] **IMInput** - Input con variantes de error/success
- [ ] **IMCard** - Card con header/footer opcionales
- [ ] **IMBadge** - Pills de status customizables
- [ ] **IMModal** - Modal accesible con overlay
- [ ] **IMTable** - Tabla responsive con sorting
- [ ] **IMSidebar** - Sidebar collapsible
- [ ] **IMTopbar** - Topbar con breadcrumb y user menu

---

## 📚 Recursos

- **Tailwind Docs:** https://tailwindcss.com
- **Montserrat Font:** https://fonts.google.com/specimen/Montserrat
- **WCAG 2.1:** https://www.w3.org/WAI/WCAG21/quickref/
- **Design Tokens W3C:** https://design-tokens.github.io/community-group/format/

---

**Última actualización:** 2025-10-22
**Mantenido por:** IdeaMakers Dev Team
**Versión:** 1.0.0
