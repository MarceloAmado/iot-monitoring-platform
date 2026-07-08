/**
 * Custom hook para manejo de autenticación.
 */

import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { useNavigate } from 'react-router-dom';
import authService from '@/services/authService';
import type { LoginRequest, User } from '@/types';

export const useAuth = () => {
  const queryClient = useQueryClient();
  const navigate = useNavigate();

  // Query para obtener usuario actual
  const { data: user, isLoading } = useQuery<User | null>({
    queryKey: ['current-user'],
    queryFn: async () => {
      if (!authService.isAuthenticated()) {
        return null;
      }
      try {
        return await authService.getCurrentUser();
      } catch {
        return null;
      }
    },
    staleTime: 5 * 60 * 1000, // 5 minutos
  });

  // Mutation para login
  const loginMutation = useMutation({
    mutationFn: (credentials: LoginRequest) => authService.login(credentials),
    onSuccess: async () => {
      // Refetch user data
      await queryClient.invalidateQueries({ queryKey: ['current-user'] });
      navigate('/dashboard');
    },
  });

  // Logout
  const logout = () => {
    authService.logout();
    queryClient.setQueryData(['current-user'], null);
    navigate('/login');
  };

  return {
    user,
    isLoading,
    isAuthenticated: !!user,
    login: loginMutation.mutate,
    loginLoading: loginMutation.isPending,
    loginError: loginMutation.error,
    logout,
  };
};

export default useAuth;
