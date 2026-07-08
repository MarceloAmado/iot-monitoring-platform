# Frontend - Sistema de Monitoreo IoT

## Stack Tecnológico

- **Framework:** React 18
- **Lenguaje:** TypeScript 5
- **Build Tool:** Vite 5
- **Routing:** React Router DOM 6
- **State Management:** TanStack Query 5 (React Query)
- **HTTP Client:** Axios
- **Charts:** Recharts 2
- **Styling:** Tailwind CSS 3
- **Date Formatting:** date-fns

## Estructura del Proyecto

```
frontend/
├── src/
│   ├── components/          # Componentes reutilizables
│   │   ├── auth/           # Login, ProtectedRoute
│   │   ├── layout/         # Navbar, Sidebar, Layout
│   │   ├── devices/        # (Futuro) Componentes de devices
│   │   └── charts/         # (Futuro) Gráficos dinámicos
│   ├── pages/              # Páginas principales
│   │   ├── Login.tsx
│   │   ├── Dashboard.tsx
│   │   └── DeviceDetail.tsx
│   ├── services/           # Servicios API
│   │   ├── api.ts          # Axios instance
│   │   ├── authService.ts
│   │   ├── deviceService.ts
│   │   └── readingService.ts
│   ├── hooks/              # Custom hooks
│   │   └── useAuth.ts
│   ├── types/              # TypeScript types
│   │   └── index.ts
│   ├── styles/             # Estilos globales
│   │   └── globals.css
│   ├── App.tsx             # App principal
│   └── main.tsx            # Entry point
├── public/                 # Assets estáticos
├── package.json
├── vite.config.ts
├── tsconfig.json
├── tailwind.config.js
├── Dockerfile
└── nginx.conf
```

## Instalación y Desarrollo

### Requisitos
- Node.js 18+
- npm o yarn

### Instalación

```bash
cd frontend
npm install
```

### Variables de Entorno

Crea un archivo `.env` basado en `.env.example`:

```bash
cp .env.example .env
```

Variables disponibles:
- `VITE_API_BASE_URL`: URL del backend API (default: http://localhost:8000/api/v1)

### Desarrollo

```bash
npm run dev
```

La aplicación estará disponible en `http://localhost:3000`

### Build de Producción

```bash
npm run build
npm run preview  # Preview del build
```

## Características Implementadas

### Autenticación
- ✅ Login con JWT
- ✅ Logout
- ✅ Rutas protegidas
- ✅ Interceptor Axios para agregar token automáticamente
- ✅ Redirección automática al expirar token

### Dashboard
- ✅ Lista de devices con estado
- ✅ Estadísticas rápidas (total, en línea, fuera de línea, mantenimiento)
- ✅ Detección de devices online/offline (< 10 minutos)
- ✅ Formateo de fechas relativas ("hace 5 minutos")

### Device Detail
- ✅ Información del device
- ✅ Gráfico de temperatura y humedad (últimas 24h)
- ✅ Tabla de lecturas recientes
- ✅ Quality score con badges

## Componentes Principales

### Layout System
- **Navbar**: Muestra usuario, rol y botón de logout
- **Sidebar**: Navegación principal
- **Layout**: Wrapper que combina Navbar + Sidebar

### Auth System
- **LoginForm**: Formulario de login con validación
- **ProtectedRoute**: HOC para proteger rutas

### Services
- **api.ts**: Configuración de Axios con interceptors
- **authService**: Login, logout, getCurrentUser
- **deviceService**: CRUD de devices
- **readingService**: Obtener readings con filtros

## Hooks Personalizados

### useAuth
Hook completo para autenticación:
```typescript
const {
  user,                // Usuario actual
  isLoading,           // Estado de carga
  isAuthenticated,     // Booleano de autenticación
  login,               // Función para login
  loginLoading,        // Estado de login
  loginError,          // Error de login
  logout,              // Función para logout
} = useAuth();
```

## Estilos y Theming

### Tailwind CSS
Clases personalizadas definidas en `globals.css`:

**Buttons:**
- `.btn-primary`: Botón primario
- `.btn-secondary`: Botón secundario
- `.btn-danger`: Botón de peligro

**Cards:**
- `.card`: Card base con sombra

**Badges:**
- `.badge-green`: Verde (activo/online)
- `.badge-red`: Rojo (error/offline)
- `.badge-yellow`: Amarillo (warning/maintenance)
- `.badge-gray`: Gris (inactivo)

**Forms:**
- `.input`: Input text estándar
- `.label`: Label de formulario

## Gráficos

### Recharts
Implementación de gráfico de líneas en `DeviceDetail.tsx`:
- Eje izquierdo: Temperatura (°C)
- Eje derecho: Humedad (%)
- Responsive
- Tooltip con información

## Docker

### Build de imagen

```bash
docker build -t iot-frontend .
```

### Run container

```bash
docker run -p 3000:80 \
  -e VITE_API_BASE_URL=http://localhost:8000/api/v1 \
  iot-frontend
```

## Próximas Funcionalidades (Sprint 3)

- [ ] Gráficos dinámicos (auto-discovery de variables)
- [ ] Página de Alertas
- [ ] Configuración de reglas de alertas
- [ ] Notificaciones en tiempo real (WebSockets)
- [ ] Exportar datos a CSV
- [ ] Dark mode

## Testing

(Pendiente implementación en Sprint 3)

```bash
npm run test
```

## Linting

```bash
npm run lint
```

## Convenciones de Código

### TypeScript
- Usar tipos explícitos siempre que sea posible
- Evitar `any`, preferir `unknown` si es necesario
- Interfaces para props de componentes

### Componentes
- Functional components con hooks
- Props destructuring
- Export named + export default

### Naming
- Componentes: `PascalCase`
- Hooks: `useCamelCase`
- Funciones: `camelCase`
- Constantes: `UPPER_SNAKE_CASE`

### Organización de imports
```typescript
// 1. React imports
import { useState } from 'react';

// 2. Third-party imports
import { useQuery } from '@tanstack/react-query';

// 3. Local imports
import { useAuth } from '@/hooks/useAuth';
import type { User } from '@/types';
```

## Troubleshooting

### Error de CORS
Verificar que el backend tenga configurado correctamente CORS con el origin del frontend.

### Token expirado
El interceptor de Axios maneja automáticamente tokens expirados y redirige a login.

### No se muestran devices
Verificar que:
1. El backend esté corriendo
2. Hay datos seed ejecutados
3. La URL del API es correcta en `.env`

---

**Última actualización:** 2025-10-16
**Sprint:** 2
**Status:** ✅ Frontend MVP Completado
