/**
 * Navigation Bar Component
 * Top navigation with user menu and logout
 */
import React, { useState } from 'react';
import type { User } from '../context/AuthContext';

interface NavigationProps {
  user: User;
  onLogout: () => Promise<void>;
}

export const Navigation: React.FC<NavigationProps> = ({ user, onLogout }) => {
  const [isMenuOpen, setIsMenuOpen] = useState(false);
  const [isLoggingOut, setIsLoggingOut] = useState(false);

  const handleLogout = async () => {
    setIsLoggingOut(true);
    try {
      await onLogout();
    } catch (err) {
      console.error('Logout error:', err);
    } finally {
      setIsLoggingOut(false);
    }
  };

  return (
    <nav className="bg-white shadow-sm border-b border-gray-200">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex justify-between items-center h-16">
          {/* Logo */}
          <div className="flex items-center space-x-3">
            <div className="flex items-center justify-center w-10 h-10 bg-blue-600 rounded-lg">
              <svg
                className="w-6 h-6 text-white"
                fill="none"
                stroke="currentColor"
                viewBox="0 0 24 24"
              >
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={2}
                  d="M9 19V6l12-3v13M9 19c0 1.105-1.343 2-3 2s-3-.895-3-2 1.343-2 3-2 3 .895 3 2zm12-3c0 1.105-1.343 2-3 2s-3-.895-3-2 1.343-2 3-2 3 .895 3 2zM9 10l12-3"
                />
              </svg>
            </div>
            <div>
              <h1 className="text-xl font-bold text-gray-900">Shapir</h1>
              <p className="text-xs text-gray-500">Platform סיכום פגישות</p>
            </div>
          </div>

          {/* User Menu */}
          <div className="relative">
            <button
              onClick={() => setIsMenuOpen(!isMenuOpen)}
              className="flex items-center space-x-2 px-4 py-2 rounded-lg hover:bg-gray-100 transition"
            >
              <div className="w-8 h-8 bg-gradient-to-br from-blue-400 to-blue-600 rounded-full flex items-center justify-center text-white text-sm font-medium">
                {user.name.charAt(0).toUpperCase()}
              </div>
              <div className="text-left">
                <p className="text-sm font-medium text-gray-900">{user.name}</p>
                <p className="text-xs text-gray-500">{user.role}</p>
              </div>
              <svg
                className={`w-4 h-4 text-gray-500 transition ${isMenuOpen ? 'rotate-180' : ''}`}
                fill="none"
                stroke="currentColor"
                viewBox="0 0 24 24"
              >
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 14l-7 7m0 0l-7-7m7 7V3" />
              </svg>
            </button>

            {/* Dropdown Menu */}
            {isMenuOpen && (
              <div className="absolute right-0 mt-2 w-48 bg-white rounded-lg shadow-lg border border-gray-200 z-50">
                <div className="p-3 border-b border-gray-100">
                  <p className="text-sm font-medium text-gray-900">{user.email}</p>
                  <p className="text-xs text-gray-500 mt-1">משתמש מאז {new Date(user.created_at).toLocaleDateString('he-IL')}</p>
                </div>

                <div className="p-2">
                  {user.role === 'admin' && (
                    <a
                      href="/#admin"
                      className="block px-3 py-2 text-sm text-gray-700 hover:bg-gray-100 rounded transition"
                      onClick={() => setIsMenuOpen(false)}
                    >
                      📊 ממשק ניהול
                    </a>
                  )}
                  <a
                    href="/#dashboard"
                    className="block px-3 py-2 text-sm text-gray-700 hover:bg-gray-100 rounded transition"
                    onClick={() => setIsMenuOpen(false)}
                  >
                    📋 סיכומים שלי
                  </a>
                  <a
                    href="/#upload"
                    className="block px-3 py-2 text-sm text-gray-700 hover:bg-gray-100 rounded transition"
                    onClick={() => setIsMenuOpen(false)}
                  >
                    📤 העלאה חדשה
                  </a>
                </div>

                <div className="border-t border-gray-100 p-2">
                  <button
                    onClick={handleLogout}
                    disabled={isLoggingOut}
                    className="w-full text-left px-3 py-2 text-sm text-red-600 hover:bg-red-50 rounded transition disabled:opacity-50"
                  >
                    {isLoggingOut ? '...יוצא' : '🚪 התנתקות'}
                  </button>
                </div>
              </div>
            )}
          </div>
        </div>
      </div>
    </nav>
  );
};
