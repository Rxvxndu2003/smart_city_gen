import { useEffect } from 'react';
import { useAuthStore } from '../store/authStore';
import { authService } from '../services/authService';

export const useAuth = () => {
  const { user, isAuthenticated, isLoading, setUser, setLoading, logout } = useAuthStore();

  useEffect(() => {
    const initAuth = async () => {
      if (authService.isAuthenticated()) {
        try {
          const userData = await authService.getCurrentUser();
          setUser(userData);
        } catch (error) {
          console.error('Failed to get current user:', error);
          logout();
        }
      } else {
        setLoading(false);
      }
    };

    initAuth();
  }, [setUser, setLoading, logout]);

  return {
    user,
    isAuthenticated,
    isLoading,
    logout: async () => {
      await authService.logout();
      logout();
    },
  };
};
