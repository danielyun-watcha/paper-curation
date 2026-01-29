'use client';

import { useState } from 'react';
import { ArxivImporter } from '@/components/papers/ArxivImporter';
import { PaperForm } from '@/components/papers/PaperForm';

type Mode = 'arxiv' | 'manual';

export default function NewPaperPage() {
  const [mode, setMode] = useState<Mode>('arxiv');

  return (
    <div className="max-w-2xl mx-auto">
      <h1 className="text-2xl font-bold text-gray-900 dark:text-white mb-6">
        Add New Paper
      </h1>

      <div className="mb-6">
        <div className="flex gap-2">
          <button
            onClick={() => setMode('arxiv')}
            className={`px-4 py-2 rounded-md transition-colors ${
              mode === 'arxiv'
                ? 'bg-blue-600 text-white'
                : 'bg-gray-200 dark:bg-gray-700 text-gray-700 dark:text-gray-200 hover:bg-gray-300 dark:hover:bg-gray-600'
            }`}
          >
            Import from arXiv
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
        {mode === 'arxiv' ? (
          <ArxivImporter />
        ) : (
          <PaperForm mode="create" />
        )}
      </div>
    </div>
  );
}
