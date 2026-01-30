'use client';

import { useState, useEffect } from 'react';
import { Paper, TranslationResponse } from '@/types';
import { papersApi } from '@/lib/api';

export default function TranslatePage() {
  const [papers, setPapers] = useState<Paper[]>([]);
  const [selectedPaperId, setSelectedPaperId] = useState<string>('');
  const [translation, setTranslation] = useState<TranslationResponse | null>(null);
  const [loading, setLoading] = useState(false);
  const [loadingPapers, setLoadingPapers] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const fetchPapers = async () => {
      try {
        const response = await papersApi.list({ limit: 100 });
        setPapers(response.items);
      } catch (err) {
        console.error('Failed to fetch papers:', err);
      } finally {
        setLoadingPapers(false);
      }
    };
    fetchPapers();
  }, []);

  const handleTranslate = async () => {
    if (!selectedPaperId) return;

    setLoading(true);
    setError(null);
    setTranslation(null);

    try {
      const result = await papersApi.translate(selectedPaperId);
      setTranslation(result);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Translation failed');
    } finally {
      setLoading(false);
    }
  };

  const selectedPaper = papers.find(p => p.id === selectedPaperId);

  return (
    <div className="max-w-4xl mx-auto space-y-6">
      <h1 className="text-2xl font-bold text-gray-900 dark:text-white">
        Translate Paper
      </h1>

      <div className="bg-white dark:bg-gray-800 rounded-lg shadow-md p-6">
        <div className="space-y-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
              Select Paper
            </label>
            {loadingPapers ? (
              <p className="text-gray-500">Loading papers...</p>
            ) : (
              <select
                value={selectedPaperId}
                onChange={(e) => {
                  const paperId = e.target.value;
                  setSelectedPaperId(paperId);
                  // Load saved translation if exists
                  const paper = papers.find(p => p.id === paperId);
                  if (paper?.translation) {
                    setTranslation({
                      paper_id: paper.id,
                      original_title: paper.title,
                      original_abstract: paper.abstract,
                      translated_title: paper.translation.title,
                      translated_abstract: paper.translation.abstract,
                    });
                  } else {
                    setTranslation(null);
                  }
                }}
                className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md
                         bg-white dark:bg-gray-700 text-gray-900 dark:text-white
                         focus:outline-none focus:ring-2 focus:ring-blue-500"
              >
                <option value="">-- Select a paper --</option>
                {papers.map((paper) => (
                  <option key={paper.id} value={paper.id}>
                    {paper.title.length > 80 ? paper.title.substring(0, 80) + '...' : paper.title}
                  </option>
                ))}
              </select>
            )}
          </div>

          {selectedPaper && (
            <div className="p-4 bg-gray-50 dark:bg-gray-700/50 rounded-md">
              <h3 className="font-medium text-gray-900 dark:text-white mb-2">
                {selectedPaper.title}
              </h3>
              <p className="text-sm text-gray-600 dark:text-gray-400 line-clamp-3">
                {selectedPaper.abstract}
              </p>
            </div>
          )}

          <button
            onClick={handleTranslate}
            disabled={!selectedPaperId || loading}
            className="w-full py-2 px-4 bg-green-600 text-white rounded-md hover:bg-green-700
                     disabled:bg-gray-400 disabled:cursor-not-allowed transition-colors
                     flex items-center justify-center gap-2"
          >
            {loading ? (
              <>
                <svg className="animate-spin h-4 w-4" viewBox="0 0 24 24">
                  <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" fill="none" />
                  <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z" />
                </svg>
                Translating...
              </>
            ) : translation ? (
              'Retranslate'
            ) : (
              'Translate to Korean'
            )}
          </button>

          {error && (
            <div className="p-4 bg-red-100 dark:bg-red-900/30 text-red-700 dark:text-red-300 rounded-md">
              {error}
            </div>
          )}
        </div>
      </div>

      {translation && (
        <div className="bg-white dark:bg-gray-800 rounded-lg shadow-md p-6 space-y-6">
          <h2 className="text-xl font-bold text-gray-900 dark:text-white flex items-center gap-2">
            <span className="text-2xl">🇰🇷</span>
            Korean Translation
          </h2>

          <div className="space-y-4">
            <div>
              <h3 className="text-sm font-medium text-gray-500 dark:text-gray-400 mb-1">
                Title (Original)
              </h3>
              <p className="text-gray-800 dark:text-gray-200">
                {translation.original_title}
              </p>
            </div>

            {translation.translated_title && (
              <div className="p-4 bg-green-50 dark:bg-green-900/20 rounded-md border border-green-200 dark:border-green-800">
                <h3 className="text-sm font-medium text-green-700 dark:text-green-400 mb-1">
                  Title (Korean)
                </h3>
                <p className="text-gray-800 dark:text-gray-200 font-medium">
                  {translation.translated_title}
                </p>
              </div>
            )}

            <div>
              <h3 className="text-sm font-medium text-gray-500 dark:text-gray-400 mb-1">
                Abstract (Original)
              </h3>
              <p className="text-gray-700 dark:text-gray-300 text-sm leading-relaxed">
                {translation.original_abstract}
              </p>
            </div>

            <div className="p-4 bg-green-50 dark:bg-green-900/20 rounded-md border border-green-200 dark:border-green-800">
              <h3 className="text-sm font-medium text-green-700 dark:text-green-400 mb-1">
                Abstract (Korean)
              </h3>
              <p className="text-gray-800 dark:text-gray-200 leading-relaxed whitespace-pre-wrap">
                {translation.translated_abstract}
              </p>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
