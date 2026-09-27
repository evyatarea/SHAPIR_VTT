/**
 * Dashboard Page Component
 * Main page for users - upload, list recordings, create summaries
 */
import React, { useState, useEffect } from 'react';
import { UploadZone } from '../components/UploadZone';
import { RecordingList } from '../components/RecordingList';
import { SummaryView } from '../components/SummaryView';
import type { User } from '../context/AuthContext';

interface DashboardPageProps {
  user: User;
}

type ViewType = 'upload' | 'recordings' | 'summary';

export const DashboardPage: React.FC<DashboardPageProps> = ({ user }) => {
  const [currentView, setCurrentView] = useState<ViewType>('recordings');
  const [selectedRecordingId, setSelectedRecordingId] = useState<string | null>(null);
  const [selectedSummaryId, setSelectedSummaryId] = useState<string | null>(null);
  const [notification, setNotification] = useState<{ type: 'success' | 'error'; message: string } | null>(null);

  const showNotification = (type: 'success' | 'error', message: string) => {
    setNotification({ type, message });
    setTimeout(() => setNotification(null), 4000);
  };

  const handleUploadSuccess = (recordingId: string) => {
    showNotification('success', 'קובץ הועלה בהצלחה! מעבד את השיחה...');
    setSelectedRecordingId(recordingId);
    setCurrentView('recordings');
  };

  const handleUploadError = (error: string) => {
    showNotification('error', error);
  };

  const handleViewSummary = (summaryId: string) => {
    setSelectedSummaryId(summaryId);
    setCurrentView('summary');
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="bg-gradient-to-r from-blue-600 to-blue-800 rounded-lg shadow-lg p-8 text-white">
        <h1 className="text-3xl font-bold mb-2">שלום, {user.name}!</h1>
        <p className="text-blue-100">
          ממשק לניהול הקלטות פגישות וייצור סיכומים עם AI
        </p>
      </div>

      {/* Notifications */}
      {notification && (
        <div
          className={`rounded-lg p-4 flex items-center space-x-2 ${
            notification.type === 'success'
              ? 'bg-green-50 text-green-700 border border-green-200'
              : 'bg-red-50 text-red-700 border border-red-200'
          }`}
        >
          {notification.type === 'success' ? (
            <svg className="w-5 h-5" fill="currentColor" viewBox="0 0 20 20">
              <path
                fillRule="evenodd"
                d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z"
                clipRule="evenodd"
              />
            </svg>
          ) : (
            <svg className="w-5 h-5" fill="currentColor" viewBox="0 0 20 20">
              <path
                fillRule="evenodd"
                d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z"
                clipRule="evenodd"
              />
            </svg>
          )}
          <span>{notification.message}</span>
        </div>
      )}

      {/* Navigation Tabs */}
      <div className="flex space-x-2 border-b border-gray-200">
        <button
          onClick={() => setCurrentView('upload')}
          className={`px-4 py-2 border-b-2 transition ${
            currentView === 'upload'
              ? 'border-blue-600 text-blue-600 font-medium'
              : 'border-transparent text-gray-600 hover:text-gray-900'
          }`}
        >
          📤 העלאה חדשה
        </button>
        <button
          onClick={() => setCurrentView('recordings')}
          className={`px-4 py-2 border-b-2 transition ${
            currentView === 'recordings'
              ? 'border-blue-600 text-blue-600 font-medium'
              : 'border-transparent text-gray-600 hover:text-gray-900'
          }`}
        >
          📋 הקלטות שלי
        </button>
        {selectedSummaryId && (
          <button
            onClick={() => setCurrentView('summary')}
            className={`px-4 py-2 border-b-2 transition ${
              currentView === 'summary'
                ? 'border-blue-600 text-blue-600 font-medium'
                : 'border-transparent text-gray-600 hover:text-gray-900'
            }`}
          >
            📄 סיכום
          </button>
        )}
      </div>

      {/* Content */}
      <div className="bg-white rounded-lg shadow">
        {currentView === 'upload' && (
          <div className="p-8">
            <h2 className="text-2xl font-bold mb-6">העלאת הקלטה חדשה</h2>
            <UploadZone onUploadSuccess={handleUploadSuccess} onError={handleUploadError} />
          </div>
        )}

        {currentView === 'recordings' && (
          <div className="p-8">
            <h2 className="text-2xl font-bold mb-6">ההקלטות שלי</h2>
            <RecordingList
              selectedRecordingId={selectedRecordingId}
              onViewSummary={handleViewSummary}
              onError={handleUploadError}
            />
          </div>
        )}

        {currentView === 'summary' && selectedSummaryId && (
          <div className="p-8">
            <SummaryView summaryId={selectedSummaryId} onError={handleUploadError} />
          </div>
        )}
      </div>
    </div>
  );
};
