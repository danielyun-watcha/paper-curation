'use client';

import { useState } from 'react';
import { useRouter } from 'next/navigation';
import { Category, CATEGORIES } from '@/types';
import { papersApi, ApiError } from '@/lib/api';
import { Tag } from '@/components/ui/Tag';

type ImportSource = 'arxiv' | 'doi';

export function ArxivImporter() {
  const router = useRouter();
  const [url, setUrl] = useState('');
  const [source, setSource] = useState<ImportSource>('arxiv');
  const [category, setCategory] = useState<Category>('other');
  const [tags, setTags] = useState<string[]>([]);
  const [tagInput, setTagInput] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // Detect source from URL
  const detectSource = (inputUrl: string) => {
    if (inputUrl.includes('arxiv.org')) {
      setSource('arxiv');
    } else if (
      inputUrl.includes('dl.acm.org') ||
      inputUrl.includes('ieee') ||
      inputUrl.includes('doi.org')
    ) {
      setSource('doi');
    }
  };

  const addTag = () => {
    const tag = tagInput.trim().toLowerCase();
    if (tag && !tags.includes(tag)) {
      setTags([...tags, tag]);
    }
    setTagInput('');
  };

  const removeTag = (tag: string) => {
    setTags(tags.filter((t) => t !== tag));
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setError(null);

    try {
      if (source === 'arxiv') {
        await papersApi.importFromArxiv({
          arxiv_url: url,
          category,
          tags,
        });
      } else {
        await papersApi.importFromDoi({
          url,
          category,
          tags,
        });
      }
      router.push('/');
      router.refresh();
    } catch (err) {
      if (err instanceof ApiError) {
        if (err.status === 409) {
          setError('This paper already exists in the database');
        } else {
          setError(err.message);
        }
      } else {
        setError('Failed to import paper');
      }
    } finally {
      setLoading(false);
    }
  };

  return (
    <form onSubmit={handleSubmit} className="space-y-6">
      {error && (
        <div className="p-4 bg-red-100 text-red-700 rounded-md">{error}</div>
      )}

      <div>
        <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
          Paper URL *
        </label>
        <input
          type="url"
          value={url}
          onChange={(e) => {
            setUrl(e.target.value);
            detectSource(e.target.value);
          }}
          required
          placeholder="https://arxiv.org/abs/... or https://dl.acm.org/doi/..."
          className="w-full px-4 py-2 border border-gray-300 dark:border-gray-600 rounded-md bg-white dark:bg-gray-800 text-gray-900 dark:text-white focus:ring-2 focus:ring-blue-500"
        />
        <p className="mt-1 text-sm text-gray-500">
          Supports: arXiv, ACM, IEEE, and DOI URLs
        </p>
      </div>

      <div>
        <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
          Source
        </label>
        <div className="flex gap-4">
          <label className="flex items-center">
            <input
              type="radio"
              name="source"
              value="arxiv"
              checked={source === 'arxiv'}
              onChange={() => setSource('arxiv')}
              className="mr-2"
            />
            arXiv
          </label>
          <label className="flex items-center">
            <input
              type="radio"
              name="source"
              value="doi"
              checked={source === 'doi'}
              onChange={() => setSource('doi')}
              className="mr-2"
            />
            ACM / IEEE / DOI
          </label>
        </div>
      </div>

      <div>
        <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
          Category *
        </label>
        <select
          value={category}
          onChange={(e) => setCategory(e.target.value as Category)}
          className="w-full px-4 py-2 border border-gray-300 dark:border-gray-600 rounded-md bg-white dark:bg-gray-800 text-gray-900 dark:text-white focus:ring-2 focus:ring-blue-500"
        >
          {CATEGORIES.map((cat) => (
            <option key={cat.value} value={cat.value}>
              {cat.label}
            </option>
          ))}
        </select>
      </div>

      <div>
        <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
          Tags (optional - will auto-predict if empty)
        </label>
        <div className="flex gap-2 mb-2">
          <input
            type="text"
            value={tagInput}
            onChange={(e) => setTagInput(e.target.value)}
            onKeyDown={(e) => {
              if (e.key === 'Enter') {
                e.preventDefault();
                addTag();
              }
            }}
            placeholder="Add tag and press Enter"
            className="flex-1 px-4 py-2 border border-gray-300 dark:border-gray-600 rounded-md bg-white dark:bg-gray-800 text-gray-900 dark:text-white focus:ring-2 focus:ring-blue-500"
          />
          <button
            type="button"
            onClick={addTag}
            className="px-4 py-2 bg-gray-200 dark:bg-gray-700 text-gray-700 dark:text-gray-200 rounded-md hover:bg-gray-300 dark:hover:bg-gray-600"
          >
            Add
          </button>
        </div>
        <div className="flex flex-wrap gap-2">
          {tags.map((tag) => (
            <Tag key={tag} name={tag} onRemove={() => removeTag(tag)} />
          ))}
        </div>
      </div>

      <div className="flex gap-3">
        <button
          type="submit"
          disabled={loading}
          className="px-6 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 disabled:opacity-50 transition-colors"
        >
          {loading ? 'Importing...' : 'Import Paper'}
        </button>
        <button
          type="button"
          onClick={() => router.back()}
          className="px-6 py-2 bg-gray-200 dark:bg-gray-700 text-gray-700 dark:text-gray-200 rounded-md hover:bg-gray-300 dark:hover:bg-gray-600"
        >
          Cancel
        </button>
      </div>
    </form>
  );
}
