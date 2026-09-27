/**
 * Template Manager Component
 * CRUD operations for summarization templates
 */
import React, { useState, useEffect } from 'react';
import { apiService } from '../services/apiClient';

interface Template {
  id: string;
  name: string;
  description: string;
  output_format: string;
  is_active: boolean;
  created_at: string;
  updated_at: string | null;
}

export const TemplateManager: React.FC = () => {
  const [templates, setTemplates] = useState<Template[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [showForm, setShowForm] = useState(false);
  const [editingId, setEditingId] = useState<string | null>(null);
  const [message, setMessage] = useState<{ type: 'success' | 'error'; text: string } | null>(null);
  const [formData, setFormData] = useState({
    name: '',
    description: '',
    system_prompt: '',
    user_prompt_template: '',
    output_format: 'txt',
  });

  useEffect(() => {
    loadTemplates();
  }, []);

  const loadTemplates = async () => {
    try {
      setIsLoading(true);
      const response = await apiService.templates.list();
      setTemplates(response.data.templates);
    } catch (err) {
      showMessage('error', 'שגיאה בטעינת התבניות');
    } finally {
      setIsLoading(false);
    }
  };

  const showMessage = (type: 'success' | 'error', text: string) => {
    setMessage({ type, text });
    setTimeout(() => setMessage(null), 3000);
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();

    // Validate
    if (!formData.name || !formData.system_prompt || !formData.user_prompt_template) {
      showMessage('error', 'יש למלא את כל השדות הנדרשים');
      return;
    }

    if (!formData.user_prompt_template.includes('{transcript}')) {
      showMessage('error', 'התבנית חייבת להכיל {transcript}');
      return;
    }

    try {
      if (editingId) {
        await apiService.templates.update(editingId, formData);
        showMessage('success', 'התבנית עודכנה בהצלחה');
      } else {
        await apiService.templates.create(formData);
        showMessage('success', 'התבנית נוצרה בהצלחה');
      }
      resetForm();
      loadTemplates();
    } catch (err: any) {
      showMessage('error', err.response?.data?.detail || 'שגיאה בשמירת התבנית');
    }
  };

  const handleDelete = async (id: string) => {
    if (!window.confirm('אתה בטוח שברצונך למחוק את התבנית?')) return;

    try {
      await apiService.templates.delete(id);
      showMessage('success', 'התבנית נמחקה בהצלחה');
      loadTemplates();
    } catch (err: any) {
      showMessage('error', 'שגיאה במחיקת התבנית');
    }
  };

  const handleEdit = (template: Template) => {
    const fullTemplate = { ...template, system_prompt: '', user_prompt_template: '' };
    apiService.templates.get(template.id).then((response) => {
      setFormData({
        name: response.data.name,
        description: response.data.description,
        system_prompt: response.data.system_prompt,
        user_prompt_template: response.data.user_prompt_template,
        output_format: response.data.output_format,
      });
      setEditingId(template.id);
      setShowForm(true);
    });
  };

  const resetForm = () => {
    setFormData({
      name: '',
      description: '',
      system_prompt: '',
      user_prompt_template: '',
      output_format: 'txt',
    });
    setEditingId(null);
    setShowForm(false);
  };

  return (
    <div className="p-8">
      <div className="flex justify-between items-center mb-6">
        <h2 className="text-2xl font-bold text-gray-900">📝 ניהול תבניות סיכום</h2>
        <button
          onClick={() => {
            resetForm();
            setShowForm(!showForm);
          }}
          className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition"
        >
          {showForm ? '❌ ביטול' : '➕ תבנית חדשה'}
        </button>
      </div>

      {/* Messages */}
      {message && (
        <div
          className={`mb-4 p-4 rounded-lg ${
            message.type === 'success'
              ? 'bg-green-50 text-green-700 border border-green-200'
              : 'bg-red-50 text-red-700 border border-red-200'
          }`}
        >
          {message.text}
        </div>
      )}

      {/* Form */}
      {showForm && (
        <form onSubmit={handleSubmit} className="bg-gray-50 rounded-lg p-6 mb-6 border border-gray-200 space-y-4">
          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">שם התבנית *</label>
              <input
                type="text"
                value={formData.name}
                onChange={(e) => setFormData({ ...formData, name: e.target.value })}
                placeholder="סיכום קצר"
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 outline-none"
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">פורמט פלט</label>
              <select
                value={formData.output_format}
                onChange={(e) => setFormData({ ...formData, output_format: e.target.value })}
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 outline-none"
              >
                <option value="txt">טקסט</option>
                <option value="pdf">PDF</option>
                <option value="docx">Word</option>
                <option value="xlsx">Excel</option>
              </select>
            </div>
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">תיאור</label>
            <input
              type="text"
              value={formData.description}
              onChange={(e) => setFormData({ ...formData, description: e.target.value })}
              placeholder="תיאור קצר של התבנית"
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 outline-none"
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">System Prompt *</label>
            <textarea
              value={formData.system_prompt}
              onChange={(e) => setFormData({ ...formData, system_prompt: e.target.value })}
              placeholder="הנחיות ל-GPT על כיצד להתנהג..."
              rows={3}
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 outline-none font-mono text-sm"
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">User Prompt Template * (חייב להכיל {'{transcript}'})</label>
            <textarea
              value={formData.user_prompt_template}
              onChange={(e) => setFormData({ ...formData, user_prompt_template: e.target.value })}
              placeholder="סכם את השיחה הבאה:{'\n'}{'{transcript}'}{'\n\n'}סיכום:"
              rows={4}
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 outline-none font-mono text-sm"
            />
          </div>

          <div className="flex justify-end space-x-2">
            <button
              type="button"
              onClick={resetForm}
              className="px-4 py-2 border border-gray-300 rounded-lg text-gray-700 hover:bg-gray-100 transition"
            >
              ביטול
            </button>
            <button
              type="submit"
              className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition"
            >
              {editingId ? '💾 עדכן' : '➕ הוסף'}
            </button>
          </div>
        </form>
      )}

      {/* Templates List */}
      {isLoading ? (
        <div className="text-center py-12">
          <svg className="animate-spin h-8 w-8 text-blue-600 mx-auto mb-4" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
            <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
            <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
          </svg>
          <p className="text-gray-500">טוען תבניות...</p>
        </div>
      ) : (
        <div className="grid grid-cols-1 gap-4">
          {templates.map((template) => (
            <div key={template.id} className="bg-white border border-gray-200 rounded-lg p-4 hover:shadow-md transition">
              <div className="flex justify-between items-start">
                <div className="flex-1">
                  <div className="flex items-center space-x-2">
                    <h3 className="font-bold text-gray-900">{template.name}</h3>
                    {template.is_active ? (
                      <span className="text-xs bg-green-100 text-green-800 px-2 py-1 rounded">✅ פעיל</span>
                    ) : (
                      <span className="text-xs bg-gray-100 text-gray-800 px-2 py-1 rounded">⭕ כבוי</span>
                    )}
                  </div>
                  <p className="text-sm text-gray-600 mt-1">{template.description}</p>
                  <p className="text-xs text-gray-400 mt-2">פורמט: {template.output_format} • נוצר: {new Date(template.created_at).toLocaleDateString('he-IL')}</p>
                </div>
                <div className="flex space-x-2 ml-4">
                  <button
                    onClick={() => handleEdit(template)}
                    className="px-3 py-1 text-sm bg-blue-100 text-blue-700 rounded hover:bg-blue-200 transition"
                  >
                    ✏️ עריכה
                  </button>
                  <button
                    onClick={() => handleDelete(template.id)}
                    className="px-3 py-1 text-sm bg-red-100 text-red-700 rounded hover:bg-red-200 transition"
                  >
                    🗑️ מחיקה
                  </button>
                </div>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
};
