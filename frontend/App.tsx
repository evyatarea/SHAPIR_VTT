/**
 * Main App Component - Shapir Recordings Platform
 * Phase 4: React Frontend
 */
import React, { useState, useEffect } from 'react';
import { AuthContext } from './context/AuthContext';
import { useAuth } from './hooks/useAuth';
import { LoginPage } from './pages/LoginPage';
import { DashboardPage } from './pages/DashboardPage';
import { AdminPage } from './pages/AdminPage';
import { Navigation } from './components/Navigation';

export const App: React.FC = () => {
  const [isInitializing, setIsInitializing] = useState(true);
  const { user, isAuthenticated, login, logout, verifyToken } = useAuth();

  useEffect(() => {
    // Verify token on app load
    const initializeAuth = async () => {
      await verifyToken();
      setIsInitializing(false);
    };

    initializeAuth();
  }, []);

  if (isInitializing) {
    return (
      <div className="flex items-center justify-center min-h-screen bg-gradient-to-br from-blue-50 to-blue-100">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto mb-4"></div>
          <p className="text-gray-600 font-medium">טוען...</p>
        </div>
      </div>
    );
  }

  if (!isAuthenticated || !user) {
    return <LoginPage onLogin={login} />;
  }

  return (
    <AuthContext.Provider value={{ user, isAuthenticated, login, logout }}>
      <div className="min-h-screen bg-gray-50">
        <Navigation user={user} onLogout={logout} />

        <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
          {user.role === 'admin' ? (
            <AdminPage user={user} />
          ) : (
            <DashboardPage user={user} />
          )}
        </main>

        <footer className="bg-white border-t border-gray-200 mt-12">
          <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
            <p className="text-center text-gray-500 text-sm">
              © 2026 Shapir Engineering. Platform לסיכום פגישות עם AI.
            </p>
          </div>
        </footer>
      </div>
    </AuthContext.Provider>
  );
};

export default App;
