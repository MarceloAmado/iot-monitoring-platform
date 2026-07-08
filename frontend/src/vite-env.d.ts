/// <reference types="vite/client" />

interface ImportMetaEnv {
  readonly VITE_API_BASE_URL: string
  // Agregar más variables de entorno aquí si es necesario
}

interface ImportMeta {
  readonly env: ImportMetaEnv
}
