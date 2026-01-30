'use client';

import { useState } from 'react';
import { useRouter } from 'next/navigation';
import { papersApi } from '@/lib/api';
import { BulkImportResultItem } from '@/types';

export function BulkImporter() {
  const router = useRouter();
  const [urls, setUrls] = useState('');
  const [loading, setLoading] = useState(false);
  const [results, setResults] = useState<BulkImportResultItem[] | null>(null);
  const [summary, setSummary] = useState<{ total: number; successful: number; failed: number } | null>(null);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();

    const urlList = urls
      .split('\n')
      .map(url => url.trim())
      .filter(url => url.length > 0);

    if (urlList.length === 0) {
      return;
    }

    setLoading(true);
    setResults(null);
    setSummary(null);

    try {
      const response = await papersApi.bulkImport({ urls: urlList });
      setResults(response.results);
      setSummary({
        total: response.total,
        successful: response.successful,
        failed: response.failed,
      });
    } catch (err) {
      setResults([{
        url: 'Error',
        success: false,
        error: err instanceof Error ? err.message : 'Failed to import',
      }]);
    } finally {
      setLoading(false);
    }
  };

  const urlCount = urls.split('\n').filter(url => url.trim().length > 0).length;

  return (
    <div className="space-y-6">
      <div className="text-sm text-gray-600 dark:text-gray-400">
        Enter multiple arXiv or DOI URLs (one per line). Category and tags will be auto-predicted.
      </div>

      <form onSubmit={handleSubmit} className="space-y-4">
        <div>
          <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
            URLs ({urlCount} {urlCount === 1 ? 'paper' : 'papers'})
          </label>
          <textarea
            value={urls}
            onChange={(e) => setUrls(e.target.value)}
            placeholder="https://arxiv.org/abs/2402.17152
https://dl.acm.org/doi/10.1145/xxxxx
2402.17152"
            rows={8}
            className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md
                     bg-white dark:bg-gray-700 text-gray-900 dark:text-white
                     focus:outline-none focus:ring-2 focus:ring-blue-500 font-mono text-sm"
            disabled={loading}
          />
        </div>

        <button
          type="submit"
          disabled={loading || urlCount === 0}
          className="w-full py-2 px-4 bg-blue-600 text-white rounded-md hover:bg-blue-700
                   disabled:bg-gray-400 disabled:cursor-not-allowed transition-colors"
        >
          {loading ? (
            <span className="flex items-center justify-center gap-2">
              <svg className="animate-spin h-4 w-4" viewBox="0 0 24 24">
                <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" fill="none" />
                <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z" />
              </svg>
              Importing...
            </span>
          ) : (
            `Import ${urlCount} ${urlCount === 1 ? 'Paper' : 'Papers'}`
          )}
        </button>
      </form>

      {summary && (
        <div className={`p-4 rounded-md ${
          summary.failed === 0
            ? 'bg-green-100 dark:bg-green-900/30 text-green-700 dark:text-green-300'
            : summary.successful === 0
            ? 'bg-red-100 dark:bg-red-900/30 text-red-700 dark:text-red-300'
            : 'bg-yellow-100 dark:bg-yellow-900/30 text-yellow-700 dark:text-yellow-300'
        }`}>
          <div className="font-medium">
            Import Complete: {summary.successful} succeeded, {summary.failed} failed
          </div>
        </div>
      )}

      {results && results.length > 0 && (
        <div className="space-y-2">
          <h3 className="text-sm font-medium text-gray-700 dark:text-gray-300">Results</h3>
          <div className="max-h-64 overflow-y-auto space-y-2">
            {results.map((result, index) => (
              <div
                key={index}
                className={`p-3 rounded-md text-sm ${
                  result.success
                    ? 'bg-green-50 dark:bg-green-900/20 border border-green-200 dark:border-green-800'
                    : 'bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800'
                }`}
              >
                <div className="flex items-start gap-2">
                  {result.success ? (
                    <svg className="w-5 h-5 text-green-500 flex-shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
                    </svg>
                  ) : (
                    <svg className="w-5 h-5 text-red-500 flex-shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                    </svg>
                  )}
                  <div className="flex-1 min-w-0">
                    {result.success ? (
                      <div className="text-green-700 dark:text-green-300 truncate">{result.title}</div>
                    ) : (
                      <>
                        <div className="text-red-700 dark:text-red-300 truncate">{result.url}</div>
                        <div className="text-red-600 dark:text-red-400 text-xs mt-1">{result.error}</div>
                      </>
                    )}
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {summary && summary.successful > 0 && (
        <button
          onClick={() => router.push('/')}
          className="w-full py-2 px-4 bg-gray-200 dark:bg-gray-700 text-gray-700 dark:text-gray-200
                   rounded-md hover:bg-gray-300 dark:hover:bg-gray-600 transition-colors"
        >
          Go to Paper List
        </button>
      )}
    </div>
  );
}
