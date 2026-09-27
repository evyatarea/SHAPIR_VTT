/**
 * Authentication Context
 * Global state management for user authentication
 */
import React from 'react';

export interface User {
  id: string;
  email: string;
  name: string;
  role: 'viewer' | 'editor' | 'admin';
  is_active: boolean;
  created_at: string;
  last_login: string | null;
}

export interface AuthContextType {
  user: User | null;
  isAuthenticated: boolean;
  login: (username: string, password: string) => Promise<void>;
  logout: () => void;
  verifyToken: () => Promise<boolean>;
}

export const AuthContext = React.createContext<AuthContextType | undefined>(undefined);

export const AuthProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  return <>{children}</>;
};
