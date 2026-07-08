/**
 * Servicio de autenticación - Login, Logout, obtener usuario actual.
 */

import api from './api';
import type { LoginRequest, TokenResponse, User } from '@/types';

export const authService = {
  /**
   * Login - Obtiene token JWT del backend
   */
  async login(credentials: LoginRequest): Promise<TokenResponse> {
    const response = await api.post<TokenResponse>('/auth/login', credentials);

    // Guardar token en localStorage
    localStorage.setItem('access_token', response.data.access_token);

    return response.data;
  },

  /**
   * Logout - Elimina token del localStorage
   */
  logout(): void {
    localStorage.removeItem('access_token');
    localStorage.removeItem('user');
  },

  /**
   * Obtener usuario actual (GET /auth/me)
   */
  async getCurrentUser(): Promise<User> {
    const response = await api.get<User>('/auth/me');

    // Guardar usuario en localStorage para cache
    localStorage.setItem('user', JSON.stringify(response.data));

    return response.data;
  },

  /**
   * Verificar si hay token guardado
   */
  isAuthenticated(): boolean {
    return !!localStorage.getItem('access_token');
  },

  /**
   * Obtener usuario desde localStorage (cache)
   */
  getCachedUser(): User | null {
    const userStr = localStorage.getItem('user');
    if (!userStr) return null;

    try {
      return JSON.parse(userStr) as User;
    } catch {
      return null;
    }
  },

  /**
   * Actualizar preferencias de UI del usuario actual
   */
  async updateMyPreferences(preferences: Record<string, unknown>): Promise<User> {
    const response = await api.patch<User>('/auth/me/preferences', { preferences });

    // Refrescar el cache local del usuario
    localStorage.setItem('user', JSON.stringify(response.data));

    return response.data;
  },

  /**
   * Forgot Password - Solicita link de recuperación
   */
  async forgotPassword(email: string): Promise<{ message: string; email: string }> {
    const response = await api.post<{ message: string; email: string }>(
      '/auth/forgot-password',
      { email }
    );
    return response.data;
  },

  /**
   * Reset Password - Resetea contraseña con token
   */
  async resetPassword(token: string, newPassword: string): Promise<{ message: string; success: boolean }> {
    const response = await api.post<{ message: string; success: boolean }>(
      '/auth/reset-password',
      { token, new_password: newPassword }
    );
    return response.data;
  },

  /**
   * Change Password - Cambiar contraseña (usuario logueado)
   */
  async changePassword(oldPassword: string, newPassword: string): Promise<{ message: string }> {
    const response = await api.post<{ message: string }>(
      '/auth/change-password',
      { old_password: oldPassword, new_password: newPassword }
    );
    return response.data;
  },
};

export default authService;
