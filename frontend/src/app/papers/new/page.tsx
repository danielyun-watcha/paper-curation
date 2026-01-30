'use client';

import { useState } from 'react';
import { ArxivImporter } from '@/components/papers/ArxivImporter';
import { PaperForm } from '@/components/papers/PaperForm';
import { PdfUploader } from '@/components/papers/PdfUploader';

type Mode = 'url' | 'pdf' | 'manual';

export default function NewPaperPage() {
  const [mode, setMode] = useState<Mode>('url');

  return (
    <div className="max-w-2xl mx-auto">
      <h1 className="text-2xl font-bold text-gray-900 dark:text-white mb-6">
        Add New Paper
      </h1>

      <div className="mb-6">
        <div className="flex flex-wrap gap-2">
          <button
            onClick={() => setMode('url')}
            className={`px-4 py-2 rounded-md transition-colors ${
              mode === 'url'
                ? 'bg-blue-600 text-white'
                : 'bg-gray-200 dark:bg-gray-700 text-gray-700 dark:text-gray-200 hover:bg-gray-300 dark:hover:bg-gray-600'
            }`}
          >
            URL Import
          </button>
          <button
            onClick={() => setMode('pdf')}
            className={`px-4 py-2 rounded-md transition-colors ${
              mode === 'pdf'
                ? 'bg-blue-600 text-white'
                : 'bg-gray-200 dark:bg-gray-700 text-gray-700 dark:text-gray-200 hover:bg-gray-300 dark:hover:bg-gray-600'
            }`}
          >
            PDF Upload
          </button>
          <button
            onClick={() => setMode('manual')}
            className={`px-4 py-2 rounded-md transition-colors ${
              mode === 'manual'
                ? 'bg-blue-600 text-white'
                : 'bg-gray-200 dark:bg-gray-700 text-gray-700 dark:text-gray-200 hover:bg-gray-300 dark:hover:bg-gray-600'
            }`}
          >
            Manual Entry
          </button>
        </div>
      </div>

      <div className="bg-white dark:bg-gray-800 rounded-lg shadow-md p-6">
        {mode === 'url' ? (
          <ArxivImporter />
        ) : mode === 'pdf' ? (
          <PdfUploader />
        ) : (
          <PaperForm mode="create" />
        )}
      </div>
    </div>
  );
}
