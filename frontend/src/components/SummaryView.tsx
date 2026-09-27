/**
 * Summary View Component
 * Display summary and download options
 */
import React, { useState, useEffect } from 'react';
import { apiService } from '../services/apiClient';

interface Summary {
  id: string;
  recording_id: string;
  template_id: string;
  summary_text: string;
  api_cost: number;
  processing_time_seconds: number;
  model_used: string;
  created_at: string;
}

interface SummaryViewProps {
  summaryId: string;
  onError: (error: string) => void;
}

type DownloadFormat = 'pdf' | 'docx' | 'xlsx' | 'txt';

export const SummaryView: React.FC<SummaryViewProps> = ({ summaryId, onError }) => {
  const [summary, setSummary] = useState<Summary | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [isDownloading, setIsDownloading] = useState<DownloadFormat | null>(null);

  useEffect(() => {
    loadSummary();
  }, [summaryId]);

  const loadSummary = async () => {
    try {
      setIsLoading(true);
      const response = await apiService.summaries.get(summaryId);
      setSummary(response.data);
    } catch (err: any) {
      onError('שגיאה בטעינת הסיכום');
      console.error(err);
    } finally {
      setIsLoading(false);
    }
  };

  const handleDownload = async (format: DownloadFormat) => {
    setIsDownloading(format);
    try {
      const response = await apiService.summaries.download(summaryId, format);

      // Create download link
      const url = window.URL.createObjectURL(new Blob([response.data]));
      const link = document.createElement('a');
      link.href = url;
      link.setAttribute('download', `summary_${summaryId.slice(0, 8)}.${format}`);
      document.body.appendChild(link);
      link.click();
      link.parentNode?.removeChild(link);
      window.URL.revokeObjectURL(url);
    } catch (err: any) {
      onError(`שגיאה בהורדת הקובץ (${format})`);
    } finally {
      setIsDownloading(null);
    }
  };

  if (isLoading) {
    return (
      <div className="text-center py-12">
        <svg className="animate-spin h-8 w-8 text-blue-600 mx-auto mb-4" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
          <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
          <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
        </svg>
        <p className="text-gray-500">טוען סיכום...</p>
      </div>
    );
  }

  if (!summary) {
    return <p className="text-center text-gray-500">הסיכום לא נמצא</p>;
  }

  const downloadFormats: { format: DownloadFormat; label: string; icon: string; description: string }[] = [
    { format: 'txt', label: 'טקסט', icon: '📄', description: 'קובץ טקסט פשוט' },
    { format: 'pdf', label: 'PDF', icon: '📕', description: 'מסמך מעוצב' },
    { format: 'docx', label: 'Word', icon: '📗', description: 'ניתן לעריכה' },
    { format: 'xlsx', label: 'Excel', icon: '📊', description: 'גיליון נתונים' },
  ];

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="bg-gradient-to-r from-green-600 to-green-800 rounded-lg shadow-lg p-6 text-white">
        <h2 className="text-2xl font-bold mb-2">✅ סיכום הושלם!</h2>
        <p className="text-green-100">
          נוצר ב {new Date(summary.created_at).toLocaleString('he-IL')} | עלות: ${summary.api_cost.toFixed(4)}
        </p>
      </div>

      {/* Summary Content */}
      <div className="bg-white border border-gray-200 rounded-lg p-6">
        <h3 className="text-lg font-bold text-gray-900 mb-4">תוכן הסיכום</h3>
        <div className="prose prose-sm max-w-none text-gray-700 whitespace-pre-wrap leading-relaxed">
          {summary.summary_text}
        </div>
      </div>

      {/* Download Options */}
      <div>
        <h3 className="text-lg font-bold text-gray-900 mb-4">הורדה</h3>
        <div className="grid grid-cols-2 lg:grid-cols-4 gap-3">
          {downloadFormats.map(({ format, label, icon, description }) => (
            <button
              key={format}
              onClick={() => handleDownload(format)}
              disabled={isDownloading === format}
              className="p-4 border border-gray-300 rounded-lg hover:border-blue-500 hover:bg-blue-50 transition flex flex-col items-center text-center disabled:opacity-50"
            >
              <span className="text-2xl mb-2">{icon}</span>
              <p className="font-medium text-gray-900 text-sm">{label}</p>
              <p className="text-xs text-gray-500 mt-1">{description}</p>
              {isDownloading === format && (
                <svg className="animate-spin h-4 w-4 text-blue-600 mt-2" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                  <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                  <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                </svg>
              )}
            </button>
          ))}
        </div>
      </div>

      {/* Metadata */}
      <div className="bg-gray-50 rounded-lg p-4 border border-gray-200">
        <h4 className="font-medium text-gray-900 mb-3">פרטים</h4>
        <div className="grid grid-cols-2 gap-4 text-sm">
          <div>
            <p className="text-gray-500">מודל</p>
            <p className="font-medium text-gray-900">{summary.model_used}</p>
          </div>
          <div>
            <p className="text-gray-500">זמן עיבוד</p>
            <p className="font-medium text-gray-900">{summary.processing_time_seconds}s</p>
          </div>
          <div>
            <p className="text-gray-500">עלות API</p>
            <p className="font-medium text-gray-900">${summary.api_cost.toFixed(4)}</p>
          </div>
          <div>
            <p className="text-gray-500">תאריך יצירה</p>
            <p className="font-medium text-gray-900">
              {new Date(summary.created_at).toLocaleDateString('he-IL')}
            </p>
          </div>
        </div>
      </div>
    </div>
  );
};
