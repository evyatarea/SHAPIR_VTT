/**
 * Admin Page Component
 * Template management and statistics
 */
import React, { useState, useEffect } from 'react';
import { apiService } from '../services/apiClient';
import { TemplateManager } from '../components/TemplateManager';
import type { User } from '../context/AuthContext';

interface AdminPageProps {
  user: User;
}

export const AdminPage: React.FC<AdminPageProps> = ({ user }) => {
  const [currentTab, setCurrentTab] = useState<'templates' | 'stats'>('templates');
  const [stats, setStats] = useState<any>(null);
  const [isLoadingStats, setIsLoadingStats] = useState(false);

  useEffect(() => {
    if (currentTab === 'stats') {
      loadStats();
    }
  }, [currentTab]);

  const loadStats = async () => {
    setIsLoadingStats(true);
    try {
      // For now, just load templates to show admin capabilities
      // In Phase 4 Part 2, we'll add actual statistics endpoints
      const response = await apiService.templates.list();
      setStats({
        totalTemplates: response.data.total,
        templates: response.data.templates,
      });
    } catch (err) {
      console.error('Error loading stats:', err);
    } finally {
      setIsLoadingStats(false);
    }
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="bg-gradient-to-r from-purple-600 to-purple-800 rounded-lg shadow-lg p-8 text-white">
        <h1 className="text-3xl font-bold mb-2">⚙️ ממשק ניהול</h1>
        <p className="text-purple-100">
          ניהול תבניות, סטטיסטיקות ותכונות מערכת
        </p>
      </div>

      {/* Navigation Tabs */}
      <div className="flex space-x-2 border-b border-gray-200">
        <button
          onClick={() => setCurrentTab('templates')}
          className={`px-4 py-2 border-b-2 transition ${
            currentTab === 'templates'
              ? 'border-purple-600 text-purple-600 font-medium'
              : 'border-transparent text-gray-600 hover:text-gray-900'
          }`}
        >
          📝 ניהול תבניות
        </button>
        <button
          onClick={() => setCurrentTab('stats')}
          className={`px-4 py-2 border-b-2 transition ${
            currentTab === 'stats'
              ? 'border-purple-600 text-purple-600 font-medium'
              : 'border-transparent text-gray-600 hover:text-gray-900'
          }`}
        >
          📊 סטטיסטיקות
        </button>
      </div>

      {/* Content */}
      <div className="bg-white rounded-lg shadow">
        {currentTab === 'templates' && <TemplateManager />}

        {currentTab === 'stats' && (
          <div className="p-8">
            <h2 className="text-2xl font-bold mb-6">סטטיסטיקות מערכת</h2>

            {isLoadingStats ? (
              <div className="text-center py-12">
                <svg className="animate-spin h-8 w-8 text-purple-600 mx-auto mb-4" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                  <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                  <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                </svg>
                <p className="text-gray-500">טוען סטטיסטיקות...</p>
              </div>
            ) : (
              <div className="space-y-6">
                {/* Stats Cards */}
                <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                  <div className="bg-gradient-to-br from-blue-50 to-blue-100 rounded-lg p-6 border border-blue-200">
                    <p className="text-blue-600 text-sm font-medium">סה"כ תבניות</p>
                    <p className="text-3xl font-bold text-blue-900 mt-2">
                      {stats?.totalTemplates || 0}
                    </p>
                  </div>

                  <div className="bg-gradient-to-br from-green-50 to-green-100 rounded-lg p-6 border border-green-200">
                    <p className="text-green-600 text-sm font-medium">תבניות פעילות</p>
                    <p className="text-3xl font-bold text-green-900 mt-2">
                      {stats?.templates?.filter((t: any) => t.is_active).length || 0}
                    </p>
                  </div>

                  <div className="bg-gradient-to-br from-purple-50 to-purple-100 rounded-lg p-6 border border-purple-200">
                    <p className="text-purple-600 text-sm font-medium">מחסניות</p>
                    <p className="text-3xl font-bold text-purple-900 mt-2">
                      {stats?.templates?.length || 0}
                    </p>
                  </div>
                </div>

                {/* Templates List */}
                <div>
                  <h3 className="text-lg font-bold text-gray-900 mb-4">תבניות במערכת</h3>
                  <div className="overflow-x-auto">
                    <table className="w-full text-sm">
                      <thead className="bg-gray-50 border-b border-gray-200">
                        <tr>
                          <th className="px-6 py-3 text-right text-gray-700 font-medium">שם</th>
                          <th className="px-6 py-3 text-right text-gray-700 font-medium">תיאור</th>
                          <th className="px-6 py-3 text-right text-gray-700 font-medium">פורמט</th>
                          <th className="px-6 py-3 text-right text-gray-700 font-medium">סטטוס</th>
                          <th className="px-6 py-3 text-right text-gray-700 font-medium">תאריך יצירה</th>
                        </tr>
                      </thead>
                      <tbody className="divide-y divide-gray-200">
                        {stats?.templates?.map((template: any) => (
                          <tr key={template.id} className="hover:bg-gray-50">
                            <td className="px-6 py-4 font-medium text-gray-900">{template.name}</td>
                            <td className="px-6 py-4 text-gray-600 text-xs">{template.description.substring(0, 30)}...</td>
                            <td className="px-6 py-4 text-gray-600">
                              <span className="inline-flex items-center px-2 py-1 rounded-full text-xs font-medium bg-gray-100 text-gray-800">
                                {template.output_format}
                              </span>
                            </td>
                            <td className="px-6 py-4">
                              {template.is_active ? (
                                <span className="inline-flex items-center px-2 py-1 rounded-full text-xs font-medium bg-green-100 text-green-800">
                                  ✅ פעיל
                                </span>
                              ) : (
                                <span className="inline-flex items-center px-2 py-1 rounded-full text-xs font-medium bg-gray-100 text-gray-800">
                                  ⭕ כבוי
                                </span>
                              )}
                            </td>
                            <td className="px-6 py-4 text-gray-600">
                              {new Date(template.created_at).toLocaleDateString('he-IL')}
                            </td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                </div>
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  );
};
