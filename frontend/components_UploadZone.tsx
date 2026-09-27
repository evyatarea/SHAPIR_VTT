/**
 * Upload Zone Component
 * Drag-and-drop file upload with progress tracking
 */
import React, { useState, useRef } from 'react';
import { apiService } from '../services/apiClient';

interface UploadZoneProps {
  onUploadSuccess: (recordingId: string) => void;
  onError: (error: string) => void;
}

export const UploadZone: React.FC<UploadZoneProps> = ({ onUploadSuccess, onError }) => {
  const [isDragging, setIsDragging] = useState(false);
  const [isUploading, setIsUploading] = useState(false);
  const [progress, setProgress] = useState(0);
  const [fileName, setFileName] = useState<string | null>(null);
  const inputRef = useRef<HTMLInputElement>(null);

  const supportedFormats = [
    { ext: 'mp3', type: 'audio/mpeg' },
    { ext: 'm4a', type: 'audio/mp4' },
    { ext: 'wav', type: 'audio/wav' },
    { ext: 'ogg', type: 'audio/ogg' },
  ];

  const validateFile = (file: File): boolean => {
    const maxSize = 100 * 1024 * 1024; // 100MB

    if (file.size > maxSize) {
      onError(`הקובץ גדול מדי. גודל מרבי: 100MB`);
      return false;
    }

    const ext = file.name.split('.').pop()?.toLowerCase();
    if (!ext || !supportedFormats.some((f) => f.ext === ext)) {
      onError(`פורמט קובץ לא נתמך. פורמטים חוקיים: ${supportedFormats.map((f) => f.ext).join(', ')}`);
      return false;
    }

    return true;
  };

  const handleUpload = async (file: File) => {
    if (!validateFile(file)) return;

    setIsUploading(true);
    setFileName(file.name);
    setProgress(0);

    try {
      // Simulate progress (0% → 30% before upload starts)
      setProgress(30);

      const response = await apiService.recordings.upload(file);

      // Progress to 90%
      setProgress(90);

      const { recording_id } = response.data;

      // Final progress
      setProgress(100);

      // Success
      setTimeout(() => {
        setIsUploading(false);
        setProgress(0);
        setFileName(null);
        onUploadSuccess(recording_id);
      }, 500);
    } catch (err: any) {
      setIsUploading(false);
      setProgress(0);
      setFileName(null);
      onError(err.response?.data?.detail || 'שגיאה בהעלאת הקובץ');
    }
  };

  const handleDragOver = (e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(true);
  };

  const handleDragLeave = () => {
    setIsDragging(false);
  };

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(false);

    const files = e.dataTransfer.files;
    if (files.length > 0) {
      handleUpload(files[0]);
    }
  };

  const handleFileSelect = (e: React.ChangeEvent<HTMLInputElement>) => {
    const files = e.currentTarget.files;
    if (files && files.length > 0) {
      handleUpload(files[0]);
    }
  };

  return (
    <div className="w-full">
      {/* Upload Zone */}
      <div
        onDragOver={handleDragOver}
        onDragLeave={handleDragLeave}
        onDrop={handleDrop}
        onClick={() => !isUploading && inputRef.current?.click()}
        className={`relative border-2 border-dashed rounded-lg p-12 text-center cursor-pointer transition ${
          isDragging
            ? 'border-blue-500 bg-blue-50'
            : isUploading
            ? 'border-gray-300 bg-gray-50'
            : 'border-gray-300 hover:border-blue-400 hover:bg-blue-50'
        }`}
      >
        <input
          ref={inputRef}
          type="file"
          accept={supportedFormats.map((f) => f.type).join(',')}
          onChange={handleFileSelect}
          disabled={isUploading}
          className="hidden"
        />

        {isUploading ? (
          <>
            {/* Loading State */}
            <svg className="animate-spin h-12 w-12 text-blue-600 mx-auto mb-4" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
              <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
              <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
            </svg>
            <p className="text-gray-700 font-medium">{fileName}</p>
            <p className="text-sm text-gray-500 mt-2">מעלה...</p>

            {/* Progress Bar */}
            <div className="mt-4 w-full bg-gray-200 rounded-full h-2">
              <div
                className="bg-blue-600 h-2 rounded-full transition-all duration-300"
                style={{ width: `${progress}%` }}
              ></div>
            </div>
            <p className="text-xs text-gray-500 mt-2">{progress}%</p>
          </>
        ) : (
          <>
            {/* Default State */}
            <svg className="h-12 w-12 text-gray-400 mx-auto mb-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 4v16m8-8H4" />
            </svg>
            <p className="text-gray-700 font-medium">גרור קובץ הקלטה כאן</p>
            <p className="text-sm text-gray-500 mt-1">או לחץ כדי לבחור</p>
            <p className="text-xs text-gray-400 mt-3">
              פורמטים תומכים: MP3, M4A, WAV, OGG (עד 100MB)
            </p>
          </>
        )}
      </div>
    </div>
  );
};
