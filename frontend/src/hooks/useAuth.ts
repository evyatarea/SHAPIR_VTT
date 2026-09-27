/**
 * useAuth Hook - Authentication Management
 * Handles login, logout, and token verification
 */
import { useState, useCallback } from 'react';
import { apiClient } from '../services/apiClient';
import type { User } from '../context/AuthContext';

export const useAuth = () => {
  const [user, setUser] = useState<User | null>(null);
  const [isAuthenticated, setIsAuthenticated] = useState(false);
  const [token, setToken] = useState<string | null>(
    localStorage.getItem('auth_token')
  );
  const [error, setError] = useState<string | null>(null);

  /**
   * Login with AD credentials
   */
  const login = useCallback(async (username: string, password: string) => {
    try {
      setError(null);

      const response = await apiClient.post('/api/auth/login', {
        username,
        password,
      });

      const { access_token, user: userData } = response.data;

      // Store token
      localStorage.setItem('auth_token', access_token);
      setToken(access_token);
      setUser(userData);
      setIsAuthenticated(true);

      // Set token in API client headers
      apiClient.defaults.headers.common['Authorization'] = `Bearer ${access_token}`;
    } catch (err: any) {
      const errorMessage = err.response?.data?.detail || 'فشل تسجيل الدخول';
      setError(errorMessage);
      setIsAuthenticated(false);
      throw new Error(errorMessage);
    }
  }, []);

  /**
   * Logout user
   */
  const logout = useCallback(async () => {
    try {
      if (token) {
        await apiClient.post('/api/auth/logout');
      }
    } catch (err) {
      console.error('Logout error:', err);
    } finally {
      // Clear local state
      localStorage.removeItem('auth_token');
      setToken(null);
      setUser(null);
      setIsAuthenticated(false);

      // Clear API headers
      delete apiClient.defaults.headers.common['Authorization'];
    }
  }, [token]);

  /**
   * Verify token validity
   */
  const verifyToken = useCallback(async (): Promise<boolean> => {
    const storedToken = localStorage.getItem('auth_token');

    if (!storedToken) {
      setIsAuthenticated(false);
      return false;
    }

    try {
      // Set token in headers
      apiClient.defaults.headers.common['Authorization'] = `Bearer ${storedToken}`;

      const response = await apiClient.get('/api/auth/verify-token');

      if (response.status === 200) {
        setToken(storedToken);
        setIsAuthenticated(true);

        // Fetch user details
        const userResponse = await apiClient.get('/api/auth/user');
        setUser(userResponse.data);

        return true;
      }
    } catch (err: any) {
      console.error('Token verification failed:', err);
      localStorage.removeItem('auth_token');
      setToken(null);
      setUser(null);
      setIsAuthenticated(false);
    }

    return false;
  }, []);

  return {
    user,
    token,
    isAuthenticated,
    error,
    login,
    logout,
    verifyToken,
  };
};
