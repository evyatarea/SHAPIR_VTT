/**
 * Recording List Component
 * Display user's recordings with summarization options
 */
import React, { useState, useEffect } from 'react';
import { apiService } from '../services/apiClient';

interface Recording {
  id: string;
  file_name: string;
  file_size_mb: number;
  file_format: string;
  language: string | null;
  transcription_status: 'pending' | 'processing' | 'completed' | 'failed';
  duration_seconds: number | null;
  created_at: string;
  transcribed_at: string | null;
}

interface RecordingListProps {
  selectedRecordingId?: string | null;
  onViewSummary: (summaryId: string) => void;
  onError: (error: string) => void;
}

export const RecordingList: React.FC<RecordingListProps> = ({
  selectedRecordingId,
  onViewSummary,
  onError,
}) => {
  const [recordings, setRecordings] = useState<Recording[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [page, setPage] = useState(0);
  const [total, setTotal] = useState(0);
  const [expandedId, setExpandedId] = useState<string | null>(selectedRecordingId || null);
  const [showTemplateSelector, setShowTemplateSelector] = useState<string | null>(null);
  const [templates, setTemplates] = useState<any[]>([]);
  const [isSummarizing, setIsSummarizing] = useState<string | null>(null);

  const limit = 20;

  useEffect(() => {
    loadRecordings();
    loadTemplates();
  }, [page]);

  const loadRecordings = async () => {
    try {
      setIsLoading(true);
      const response = await apiService.recordings.list(limit, page * limit);
      setRecordings(response.data.recordings);
      setTotal(response.data.total);
    } catch (err: any) {
      onError('שגיאה בטעינת הקלטות');
      console.error(err);
    } finally {
      setIsLoading(false);
    }
  };

  const loadTemplates = async () => {
    try {
      const response = await apiService.templates.list(true);
      setTemplates(response.data.templates);
    } catch (err) {
      console.error('Error loading templates:', err);
    }
  };

  const formatDuration = (seconds: number | null): string => {
    if (!seconds) return 'לא ידוע';
    const hours = Math.floor(seconds / 3600);
    const minutes = Math.floor((seconds % 3600) / 60);
    if (hours > 0) {
      return `${hours}h ${minutes}m`;
    }
    return `${minutes}m`;
  };

  const getStatusBadge = (status: string) => {
    const statusConfig: Record<string, { bg: string; text: string; icon: string }> = {
      pending: { bg: 'bg-yellow-50', text: 'text-yellow-700', icon: '⏳' },
      processing: { bg: 'bg-blue-50', text: 'text-blue-700', icon: '⚙️' },
      completed: { bg: 'bg-green-50', text: 'text-green-700', icon: '✅' },
      failed: { bg: 'bg-red-50', text: 'text-red-700', icon: '❌' },
    };

    const config = statusConfig[status] || statusConfig.pending;

    return (
      <span className={`inline-flex items-center space-x-1 px-3 py-1 rounded-full text-sm ${config.bg} ${config.text}`}>
        <span>{config.icon}</span>
        <span>
          {status === 'pending' && 'ממתין'}
          {status === 'processing' && 'מעבד'}
          {status === 'completed' && 'הושלם'}
          {status === 'failed' && 'נכשל'}
        </span>
      </span>
    );
  };

  const handleCreateSummary = async (recordingId: string, templateId: string) => {
    setIsSummarizing(recordingId);
    try {
      const response = await apiService.summaries.create(recordingId, templateId);
      onViewSummary(response.data.id);
      setShowTemplateSelector(null);
    } catch (err: any) {
      onError(err.response?.data?.detail || 'שגיאה ביצירת סיכום');
    } finally {
      setIsSummarizing(null);
    }
  };

  if (isLoading && recordings.length === 0) {
    return (
      <div className="text-center py-12">
        <svg className="animate-spin h-8 w-8 text-blue-600 mx-auto mb-4" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
          <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
          <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
        </svg>
        <p className="text-gray-500">טוען הקלטות...</p>
      </div>
    );
  }

  if (recordings.length === 0) {
    return (
      <div className="text-center py-12">
        <svg className="w-12 h-12 text-gray-400 mx-auto mb-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 19V6l12-3v13M9 19c0 1.105-1.343 2-3 2s-3-.895-3-2 1.343-2 3-2 3 .895 3 2zm12-3c0 1.105-1.343 2-3 2s-3-.895-3-2 1.343-2 3-2 3 .895 3 2zM9 10l12-3" />
        </svg>
        <p className="text-gray-500 text-lg">עדיין לא העלית הקלטות</p>
        <p className="text-gray-400 text-sm mt-2">התחל בהעלאת הקלטת פגישה ראשונה</p>
      </div>
    );
  }

  return (
    <div className="space-y-4">
      {/* Recordings List */}
      {recordings.map((recording) => (
        <div key={recording.id} className="border border-gray-200 rounded-lg overflow-hidden">
          {/* Recording Header */}
          <button
            onClick={() => setExpandedId(expandedId === recording.id ? null : recording.id)}
            className="w-full px-6 py-4 hover:bg-gray-50 transition flex items-center justify-between"
          >
            <div className="flex items-center space-x-4 flex-1 text-left">
              <div className="flex-1">
                <h3 className="font-medium text-gray-900">{recording.file_name}</h3>
                <div className="flex items-center space-x-4 mt-2 text-sm text-gray-500">
                  <span>{recording.file_size_mb.toFixed(1)} MB</span>
                  <span>•</span>
                  <span>{formatDuration(recording.duration_seconds)}</span>
                  <span>•</span>
                  {getStatusBadge(recording.transcription_status)}
                </div>
              </div>
            </div>
            <svg
              className={`w-5 h-5 text-gray-400 transition ${expandedId === recording.id ? 'rotate-180' : ''}`}
              fill="none"
              stroke="currentColor"
              viewBox="0 0 24 24"
            >
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 14l-7 7m0 0l-7-7m7 7V3" />
            </svg>
          </button>

          {/* Expanded Content */}
          {expandedId === recording.id && (
            <div className="border-t border-gray-200 px-6 py-4 bg-gray-50">
              {recording.transcription_status === 'completed' ? (
                <div className="space-y-4">
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-3">
                      בחר תבנית לסיכום:
                    </label>
                    <div className="grid grid-cols-2 gap-2">
                      {templates.map((template) => (
                        <button
                          key={template.id}
                          onClick={() => handleCreateSummary(recording.id, template.id)}
                          disabled={isSummarizing === recording.id}
                          className="p-3 border border-gray-300 rounded-lg hover:border-blue-500 hover:bg-blue-50 transition text-left text-sm disabled:opacity-50"
                        >
                          <p className="font-medium text-gray-900">{template.name}</p>
                          <p className="text-gray-500 text-xs mt-1">{template.description}</p>
                        </button>
                      ))}
                    </div>
                  </div>
                </div>
              ) : (
                <div className="text-center py-4">
                  <svg className="animate-spin h-6 w-6 text-blue-600 mx-auto mb-2" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                    <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                    <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                  </svg>
                  <p className="text-gray-600 text-sm">
                    {recording.transcription_status === 'pending' && 'ממתין לעיבוד...'}
                    {recording.transcription_status === 'processing' && 'מעבד את השיחה...'}
                    {recording.transcription_status === 'failed' && 'שגיאה בעיבוד'}
                  </p>
                </div>
              )}
            </div>
          )}
        </div>
      ))}

      {/* Pagination */}
      {total > limit && (
        <div className="flex justify-center items-center space-x-2 mt-6">
          <button
            onClick={() => setPage(Math.max(0, page - 1))}
            disabled={page === 0}
            className="px-4 py-2 border border-gray-300 rounded-lg text-sm font-medium text-gray-700 hover:bg-gray-50 disabled:opacity-50"
          >
            הקודם
          </button>
          <span className="text-sm text-gray-600">
            עמוד {page + 1} מתוך {Math.ceil(total / limit)}
          </span>
          <button
            onClick={() => setPage(page + 1)}
            disabled={(page + 1) * limit >= total}
            className="px-4 py-2 border border-gray-300 rounded-lg text-sm font-medium text-gray-700 hover:bg-gray-50 disabled:opacity-50"
          >
            הבא
          </button>
        </div>
      )}
    </div>
  );
};
