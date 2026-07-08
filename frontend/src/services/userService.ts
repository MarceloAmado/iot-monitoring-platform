/**
 * User Service - Cliente API para gestión de usuarios
 *
 * Métodos disponibles:
 * - getUsers: Listar usuarios (con opción de incluir archivados)
 * - getUser: Obtener un usuario específico
 * - createUser: Crear nuevo usuario
 * - updateUser: Actualizar usuario existente
 * - deleteUser: Eliminar usuario (soft delete - desactivar)
 * - activateUser: Reactivar usuario desactivado
 * - deactivateUser: Desactivar usuario (soft delete)
 * - archiveUser: Archivar usuario
 * - unarchiveUser: Desarchivar usuario
 * - resetUserPassword: Resetear password de usuario (admin)
 */

import api from './api';
import { User, UserCreate, UserUpdate } from '../types';

/**
 * Parámetros para filtrar usuarios
 */
export interface GetUsersParams {
  include_archived?: boolean;
  role?: string;
  is_active?: boolean;
  skip?: number;
  limit?: number;
}

/**
 * Response de reset password.
 * La contraseña temporal se envía por email; temp_password solo viene
 * como fallback en desarrollo cuando SMTP está deshabilitado.
 */
export interface ResetPasswordResponse {
  message: string;
  email: string;
  email_sent: boolean;
  temp_password?: string;
}

const userService = {
  /**
   * Listar usuarios
   *
   * @param params - Parámetros de filtrado
   * @returns Array de usuarios
   */
  async getUsers(params?: GetUsersParams): Promise<User[]> {
    const queryParams = new URLSearchParams();

    if (params?.include_archived !== undefined) {
      queryParams.append('include_archived', params.include_archived.toString());
    }
    if (params?.role) {
      queryParams.append('role', params.role);
    }
    if (params?.is_active !== undefined) {
      queryParams.append('is_active', params.is_active.toString());
    }
    if (params?.skip !== undefined) {
      queryParams.append('skip', params.skip.toString());
    }
    if (params?.limit !== undefined) {
      queryParams.append('limit', params.limit.toString());
    }

    const queryString = queryParams.toString();
    const url = queryString ? `/users?${queryString}` : '/users';

    const response = await api.get<User[]>(url);
    return response.data;
  },

  /**
   * Obtener un usuario específico
   *
   * @param userId - ID del usuario
   * @returns Usuario
   */
  async getUser(userId: number): Promise<User> {
    const response = await api.get<User>(`/users/${userId}`);
    return response.data;
  },

  /**
   * Crear nuevo usuario
   *
   * @param userData - Datos del nuevo usuario
   * @returns Usuario creado
   */
  async createUser(userData: UserCreate): Promise<User> {
    const response = await api.post<User>('/users', userData);
    return response.data;
  },

  /**
   * Actualizar usuario existente
   *
   * @param userId - ID del usuario
   * @param userData - Datos a actualizar
   * @returns Usuario actualizado
   */
  async updateUser(userId: number, userData: UserUpdate): Promise<User> {
    const response = await api.patch<User>(`/users/${userId}`, userData);
    return response.data;
  },

  /**
   * Eliminar usuario (no implementado - usar deactivate o archive)
   *
   * @deprecated Usar deactivateUser o archiveUser
   */
  async deleteUser(_userId: number): Promise<void> {
    throw new Error('Delete no implementado. Usar deactivateUser() o archiveUser()');
  },

  /**
   * Activar usuario desactivado
   *
   * @param userId - ID del usuario
   * @returns Usuario activado
   */
  async activateUser(userId: number): Promise<User> {
    const response = await api.patch<User>(`/users/${userId}/activate`);
    return response.data;
  },

  /**
   * Desactivar usuario (soft delete)
   *
   * @param userId - ID del usuario
   * @returns Usuario desactivado
   */
  async deactivateUser(userId: number): Promise<User> {
    const response = await api.patch<User>(`/users/${userId}/deactivate`);
    return response.data;
  },

  /**
   * Archivar usuario
   *
   * @param userId - ID del usuario
   * @returns Usuario archivado
   */
  async archiveUser(userId: number): Promise<User> {
    const response = await api.patch<User>(`/users/${userId}/archive`);
    return response.data;
  },

  /**
   * Desarchivar usuario
   *
   * @param userId - ID del usuario
   * @returns Usuario desarchivado
   */
  async unarchiveUser(userId: number): Promise<User> {
    const response = await api.patch<User>(`/users/${userId}/unarchive`);
    return response.data;
  },

  /**
   * Resetear password de usuario (solo admin)
   *
   * Genera una contraseña temporal que el usuario debe cambiar
   *
   * @param userId - ID del usuario
   * @returns Objeto con mensaje y contraseña temporal
   */
  async resetUserPassword(userId: number): Promise<ResetPasswordResponse> {
    const response = await api.post<ResetPasswordResponse>(`/users/${userId}/reset-password`);
    return response.data;
  },

  /**
   * Obtener estadísticas de usuarios
   *
   * @returns Objeto con estadísticas
   */
  async getUserStats(): Promise<{
    total: number;
    active: number;
    inactive: number;
    archived: number;
    by_role: Record<string, number>;
  }> {
    const users = await this.getUsers({ include_archived: true });

    const stats = {
      total: users.length,
      active: users.filter(u => u.is_active && !u.archived).length,
      inactive: users.filter(u => !u.is_active && !u.archived).length,
      archived: users.filter(u => u.archived).length,
      by_role: users.reduce((acc, user) => {
        acc[user.role] = (acc[user.role] || 0) + 1;
        return acc;
      }, {} as Record<string, number>),
    };

    return stats;
  },
};

export default userService;
