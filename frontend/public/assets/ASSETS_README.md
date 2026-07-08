# 📦 Assets Structure - IdeaMakers IoT

**Estructura de archivos de diseño**

---

## 📁 Estructura de Carpetas

```
public/assets/
├── logos/                              # Logotipos IdeaMakers
│   ├── ideamakers-horizontal.svg       # Logo completo horizontal (PRINCIPAL)
│   ├── ideamakers-horizontal.png       # PNG fallback (2x retina)
│   ├── ideamakers-isotipo.svg          # Símbolo/isotipo (sidebar colapsado)
│   ├── ideamakers-isotipo.png          # PNG fallback
│   └── ideamakers-white.svg            # Logo blanco (opcional, para fondos oscuros)
│
├── images/                             # Imágenes generales
│   └── hero-iot-login.jpg              # Hero image para login page
│
└── favicons/                           # Favicons
    ├── favicon.ico                     # 32x32 (legacy browsers)
    ├── favicon-16x16.png               # 16x16
    ├── favicon-32x32.png               # 32x32
    └── apple-touch-icon.png            # 180x180 (iOS)
```

---

## 🎨 Assets Requeridos

### 1. Logos

#### Logo Horizontal (Principal)
**Archivo:** `logos/ideamakers-horizontal.svg` (o `.png`)
- **Uso:** Navbar, Login page, Footer
- **Dimensiones recomendadas:**
  - Height: 40px (navbar)
  - Height: 120px (login page)
  - Height: 28px (footer)
- **Formato:** SVG preferido (escalable), PNG 2x como fallback
- **Fondo:** Transparente
- **Colores:** Full color (azul + naranja)

#### Isotipo/Símbolo
**Archivo:** `logos/ideamakers-isotipo.svg` (o `.png`)
- **Uso:** Sidebar colapsado, favicon source
- **Dimensiones:** Cuadrado (ej: 64x64, 128x128)
- **Formato:** SVG preferido
- **Fondo:** Transparente

#### Logo Blanco (Opcional)
**Archivo:** `logos/ideamakers-white.svg`
- **Uso:** Sobre fondos oscuros (ej: hero section con overlay)
- **Colores:** Monocromático blanco
- **Fondo:** Transparente

---

### 2. Hero Image (Login)

**Archivo:** `images/hero-iot-login.jpg`
- **Uso:** Split layout izquierdo en login page
- **Dimensiones recomendadas:** 1920x1080 (16:9) o superior
- **Estilo:**
  - Tecnológico, cálido, profesional
  - Relacionado con IoT / Sensores / Monitoreo
  - Luz natural, tonos cálidos
  - Alta calidad
- **Formato:** JPG (optimizado) o WebP
- **Peso:** < 500KB (optimizado para web)

**Alternativas si no tenés imagen:**
- Usamos gradiente del brand (azul a naranja)
- Patrón geométrico sutil
- Placeholder temporal

---

### 3. Favicons

#### favicon.ico
**Archivo:** `favicons/favicon.ico`
- **Dimensiones:** 32x32 o multi-size (16, 32, 48)
- **Formato:** ICO (legacy browsers)
- **Generación:** Desde isotipo

#### favicon-16x16.png
**Archivo:** `favicons/favicon-16x16.png`
- **Dimensiones:** 16x16
- **Formato:** PNG

#### favicon-32x32.png
**Archivo:** `favicons/favicon-32x32.png`
- **Dimensiones:** 32x32
- **Formato:** PNG

#### apple-touch-icon.png
**Archivo:** `favicons/apple-touch-icon.png`
- **Dimensiones:** 180x180
- **Formato:** PNG
- **Uso:** iOS home screen icon

---

## 🚀 Instrucciones de Setup

### Paso 1: Copiar Archivos

Copiá tus assets a las rutas indicadas:

```bash
# Ejemplo (Windows)
copy "ruta\origen\logo-horizontal.svg" "public\assets\logos\ideamakers-horizontal.svg"
copy "ruta\origen\isotipo.svg" "public\assets\logos\ideamakers-isotipo.svg"
copy "ruta\origen\hero.jpg" "public\assets\images\hero-iot-login.jpg"
copy "ruta\origen\favicon.ico" "public\assets\favicons\favicon.ico"
```

### Paso 2: Verificar Archivos

```bash
# Desde frontend/
ls public/assets/logos/
ls public/assets/images/
ls public/assets/favicons/
```

**Deberías ver:**
- ✅ Al menos 1 logo (SVG o PNG)
- ✅ Al menos 1 isotipo (SVG o PNG)
- ✅ Hero image (JPG o placeholder)
- ✅ favicon.ico

### Paso 3: Actualizar index.html (automático)

El archivo `index.html` será actualizado automáticamente con:
```html
<link rel="icon" type="image/x-icon" href="/assets/favicons/favicon.ico">
<link rel="icon" type="image/png" sizes="32x32" href="/assets/favicons/favicon-32x32.png">
<link rel="icon" type="image/png" sizes="16x16" href="/assets/favicons/favicon-16x16.png">
<link rel="apple-touch-icon" sizes="180x180" href="/assets/favicons/apple-touch-icon.png">
```

---

## 🎨 Uso en Código

### Logo Component (Helper)

```tsx
import { Logo } from '@/components/common/Logo';

// Navbar (40px)
<Logo variant="horizontal" height={40} />

// Login page (120px)
<Logo variant="horizontal" height={120} />

// Sidebar colapsado (isotipo, 48px)
<Logo variant="isotipo" height={48} />

// Footer (28px)
<Logo variant="horizontal" height={28} />
```

### Uso Directo (sin component)

```tsx
// SVG
<img
  src="/assets/logos/ideamakers-horizontal.svg"
  alt="IdeaMakers"
  className="h-10"
/>

// Hero image
<img
  src="/assets/images/hero-iot-login.jpg"
  alt="IoT Monitoring"
  className="w-full h-full object-cover"
/>
```

---

## 🔧 Generación de Favicons (Opcional)

Si solo tenés el isotipo SVG, podés generar todos los favicons con:

**Opción A: Online (recomendado)**
- https://realfavicongenerator.net/
- Subir isotipo SVG
- Descargar package completo
- Copiar a `public/assets/favicons/`

**Opción B: CLI (si tenés ImageMagick)**
```bash
# Desde isotipo.svg generar PNGs
convert isotipo.svg -resize 16x16 favicon-16x16.png
convert isotipo.svg -resize 32x32 favicon-32x32.png
convert isotipo.svg -resize 180x180 apple-touch-icon.png
convert isotipo.svg -resize 32x32 favicon.ico
```

---

## ✅ Checklist de Assets

- [ ] Logo horizontal SVG (o PNG 2x)
- [ ] Isotipo SVG (o PNG)
- [ ] Hero image login (JPG/WebP)
- [ ] favicon.ico (32x32)
- [ ] favicon-16x16.png
- [ ] favicon-32x32.png
- [ ] apple-touch-icon.png (180x180)

**Archivos opcionales:**
- [ ] Logo blanco SVG
- [ ] Logo horizontal PNG fallback
- [ ] Isotipo PNG fallback

---

## 📊 Estado Actual

**Carpetas creadas:** ✅
- `public/assets/logos/`
- `public/assets/images/`
- `public/assets/favicons/`

**Assets pendientes de copiar:**
- Logo horizontal
- Isotipo
- Hero image
- Favicons

**Próximo paso:** Copiar tus archivos a las rutas indicadas y confirmar.

---

**Última actualización:** 2025-10-22
**Mantenido por:** IdeaMakers Dev Team
