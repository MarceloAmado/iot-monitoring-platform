/**
 * Upload Service - Servicio para manejo de archivos
 *
 * Funcionalidades:
 * - Upload de imágenes de perfil
 * - Eliminación de imágenes
 * - Validación de archivos
 */

import api from './api';

export interface UploadResponse {
  url: string;
  filename: string;
  message: string;
}

const uploadService = {
  /**
   * Sube una foto de perfil para el usuario actual
   * @param file - Archivo de imagen a subir
   * @returns URL de la imagen subida
   */
  async uploadProfilePicture(file: File): Promise<UploadResponse> {
    const formData = new FormData();
    formData.append('file', file);

    const response = await api.post<UploadResponse>(
      '/uploads/upload-profile-picture',
      formData,
      {
        headers: {
          'Content-Type': 'multipart/form-data',
        },
      }
    );

    return response.data;
  },

  /**
   * Elimina la foto de perfil del usuario actual
   * @param filename - Nombre del archivo a eliminar
   * @returns Mensaje de confirmación
   */
  async deleteProfilePicture(filename: string): Promise<{ message: string }> {
    const response = await api.delete<{ message: string }>(
      `/uploads/profile-pictures/${filename}`
    );

    return response.data;
  },

  /**
   * Construye la URL completa para una imagen de perfil
   * @param url - URL relativa de la imagen
   * @returns URL completa
   */
  getImageUrl(url: string | null): string | null {
    if (!url) return null;

    // Si ya es una URL completa (data: URL o http), retornarla tal cual
    if (url.startsWith('data:') || url.startsWith('http')) {
      return url;
    }

    // Construir URL completa desde el backend
    const baseUrl = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000/api/v1';

    // Eliminar /api/v1 del final si existe para evitar duplicación
    const cleanBaseUrl = baseUrl.replace(/\/api\/v1$/, '');

    return `${cleanBaseUrl}${url}`;
  },

  /**
   * Valida que un archivo sea una imagen válida
   * @param file - Archivo a validar
   * @returns Objeto con resultado de validación
   */
  validateImageFile(file: File): { valid: boolean; error?: string } {
    // Validar tipo de archivo
    const allowedTypes = ['image/jpeg', 'image/png', 'image/gif', 'image/webp'];
    if (!allowedTypes.includes(file.type)) {
      return {
        valid: false,
        error: 'Tipo de archivo no permitido. Debe ser JPG, PNG, GIF o WebP',
      };
    }

    // Validar tamaño (máximo 5MB)
    const maxSize = 5 * 1024 * 1024; // 5MB en bytes
    if (file.size > maxSize) {
      return {
        valid: false,
        error: 'La imagen no puede superar los 5MB',
      };
    }

    return { valid: true };
  },
};

export default uploadService;
