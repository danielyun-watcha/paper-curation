'use client';

import { useState } from 'react';
import { useRouter } from 'next/navigation';
import { BulkImportResultItem, Category, CATEGORIES } from '@/types';
import { papersApi, ApiError } from '@/lib/api';

interface PreviewItem {
  url: string;
  title: string | null;
  category: Category;
  error: string | null;
}

export function ArxivImporter() {
  const router = useRouter();
  const [urls, setUrls] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [results, setResults] = useState<BulkImportResultItem[] | null>(null);
  const [previews, setPreviews] = useState<PreviewItem[] | null>(null);

  const handlePreview = async () => {
    const urlList = urls
      .split('\n')
      .map((u) => u.trim())
      .filter((u) => u.length > 0);

    if (urlList.length === 0) {
      setError('Please enter at least one URL');
      return;
    }

    setLoading(true);
    setError(null);

    try {
      const response = await papersApi.previewImport({ urls: urlList });
      setPreviews(response.previews);
    } catch (err) {
      if (err instanceof ApiError) {
        setError(err.message);
      } else {
        setError('Failed to fetch paper info');
      }
    } finally {
      setLoading(false);
    }
  };

  const handleCategoryChange = (index: number, category: Category) => {
    if (!previews) return;
    const updated = [...previews];
    updated[index].category = category;
    setPreviews(updated);
  };

  const handleImport = async () => {
    if (!previews) return;

    const validPreviews = previews.filter((p) => !p.error);
    if (validPreviews.length === 0) {
      setError('No valid papers to import');
      return;
    }

    setLoading(true);
    setError(null);

    try {
      const response = await papersApi.bulkImportWithCategories({
        items: validPreviews.map((p) => ({
          url: p.url,
          category: p.category,
        })),
      });

      if (response.failed > 0) {
        setResults(response.results);
      } else {
        router.push('/');
        router.refresh();
      }
    } catch (err) {
      if (err instanceof ApiError) {
        setError(err.message);
      } else {
        setError('Failed to import papers');
      }
    } finally {
      setLoading(false);
    }
  };

  const urlCount = urls.split('\n').filter((u) => u.trim()).length;

  // Step 3: Show results
  if (results) {
    return (
      <div className="space-y-4">
        <div className="p-4 bg-gray-50 dark:bg-gray-900 rounded-md space-y-2">
          <p className="font-medium text-gray-700 dark:text-gray-300">
            Import Results: {results.filter((r) => r.success).length} success, {results.filter((r) => !r.success).length} failed
          </p>
          <div className="max-h-60 overflow-y-auto space-y-1">
            {results.map((result, idx) => (
              <div
                key={idx}
                className={`text-sm p-2 rounded ${
                  result.success
                    ? 'bg-green-100 dark:bg-green-900/30 text-green-700 dark:text-green-400'
                    : 'bg-red-100 dark:bg-red-900/30 text-red-700 dark:text-red-400'
                }`}
              >
                {result.success ? (
                  <span>{result.title}</span>
                ) : (
                  <span>{result.url}: {result.error}</span>
                )}
              </div>
            ))}
          </div>
        </div>
        <button
          type="button"
          onClick={() => {
            router.push('/');
            router.refresh();
          }}
          className="px-6 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700"
        >
          Go to Paper List
        </button>
      </div>
    );
  }

  // Step 2: Preview with category selection
  if (previews) {
    const validCount = previews.filter((p) => !p.error).length;
    return (
      <div className="space-y-4">
        <div className="flex items-center justify-between">
          <h3 className="font-medium text-gray-700 dark:text-gray-300">
            Preview ({validCount} valid, {previews.length - validCount} failed)
          </h3>
          <button
            type="button"
            onClick={() => setPreviews(null)}
            className="text-sm text-gray-500 hover:text-gray-700"
          >
            Back to URLs
          </button>
        </div>

        <div className="space-y-2 max-h-80 overflow-y-auto">
          {previews.map((preview, idx) => (
            <div
              key={idx}
              className={`p-3 rounded-md border ${
                preview.error
                  ? 'border-red-300 bg-red-50 dark:bg-red-900/20 dark:border-red-800'
                  : 'border-gray-200 dark:border-gray-700'
              }`}
            >
              {preview.error ? (
                <div className="text-sm text-red-600 dark:text-red-400">
                  <span className="font-mono text-xs">{preview.url}</span>
                  <br />
                  {preview.error}
                </div>
              ) : (
                <div className="flex items-center gap-3">
                  <div className="flex-1 min-w-0">
                    <p className="text-sm font-medium text-gray-900 dark:text-white truncate">
                      {preview.title}
                    </p>
                  </div>
                  <select
                    value={preview.category}
                    onChange={(e) => handleCategoryChange(idx, e.target.value as Category)}
                    className="px-2 py-1 text-sm border border-gray-300 dark:border-gray-600 rounded bg-white dark:bg-gray-800 text-gray-900 dark:text-white"
                  >
                    {CATEGORIES.map((cat) => (
                      <option key={cat.value} value={cat.value}>
                        {cat.label}
                      </option>
                    ))}
                  </select>
                </div>
              )}
            </div>
          ))}
        </div>

        {error && (
          <div className="p-3 bg-red-100 text-red-700 rounded-md text-sm">{error}</div>
        )}

        <div className="flex gap-3">
          <button
            type="button"
            onClick={handleImport}
            disabled={loading || validCount === 0}
            className="px-6 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 disabled:opacity-50 transition-colors"
          >
            {loading ? 'Importing...' : `Import ${validCount} Paper${validCount > 1 ? 's' : ''}`}
          </button>
          <button
            type="button"
            onClick={() => router.back()}
            className="px-6 py-2 bg-gray-200 dark:bg-gray-700 text-gray-700 dark:text-gray-200 rounded-md hover:bg-gray-300 dark:hover:bg-gray-600"
          >
            Cancel
          </button>
        </div>
      </div>
    );
  }

  // Step 1: Enter URLs
  return (
    <div className="space-y-6">
      {error && (
        <div className="p-4 bg-red-100 text-red-700 rounded-md">{error}</div>
      )}

      <div>
        <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
          Paper URLs (one per line)
        </label>
        <textarea
          value={urls}
          onChange={(e) => setUrls(e.target.value)}
          rows={6}
          placeholder="https://arxiv.org/abs/2402.17152"
          className="w-full px-4 py-2 border border-gray-300 dark:border-gray-600 rounded-md bg-white dark:bg-gray-800 text-gray-900 dark:text-white focus:ring-2 focus:ring-blue-500 font-mono text-sm"
        />
        <p className="mt-1 text-sm text-gray-500">
          Supports: arXiv, ACM, IEEE, DOI URLs
          {urlCount > 0 && <span className="ml-2 text-blue-600">({urlCount} URL{urlCount > 1 ? 's' : ''})</span>}
        </p>
      </div>

      <div className="flex gap-3">
        <button
          type="button"
          onClick={handlePreview}
          disabled={loading || urlCount === 0}
          className="px-6 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 disabled:opacity-50 transition-colors"
        >
          {loading ? 'Loading...' : 'Preview'}
        </button>
        <button
          type="button"
          onClick={() => router.back()}
          className="px-6 py-2 bg-gray-200 dark:bg-gray-700 text-gray-700 dark:text-gray-200 rounded-md hover:bg-gray-300 dark:hover:bg-gray-600"
        >
          Cancel
        </button>
      </div>
    </div>
  );
}
