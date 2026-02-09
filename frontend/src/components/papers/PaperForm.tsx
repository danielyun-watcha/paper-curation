'use client';

import { useState } from 'react';
import { useRouter } from 'next/navigation';
import { Paper, PaperCreate, PaperUpdate, Category, CATEGORIES } from '@/types';
import { papersApi } from '@/lib/api';
import { TagManager } from '@/components/ui/TagManager';
import { LoadingButton } from '@/components/ui/LoadingButton';

interface PaperFormProps {
  paper?: Paper;
  mode: 'create' | 'edit';
}

export function PaperForm({ paper, mode }: PaperFormProps) {
  const router = useRouter();
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const [title, setTitle] = useState(paper?.title || '');
  const [authors, setAuthors] = useState(paper?.authors.join(', ') || '');
  const [abstract, setAbstract] = useState(paper?.abstract || '');
  const [year, setYear] = useState(paper?.year || new Date().getFullYear());
  const [category, setCategory] = useState<Category>(paper?.category || 'other');
  const [tags, setTags] = useState<string[]>(paper?.tags.map((t) => t.name) || []);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setError(null);

    const authorList = authors
      .split(',')
      .map((a) => a.trim())
      .filter(Boolean);

    try {
      if (mode === 'create') {
        const data: PaperCreate = {
          title,
          authors: authorList,
          abstract,
          year,
          category,
          tags,
        };
        await papersApi.create(data);
      } else if (paper) {
        const data: PaperUpdate = {
          title,
          authors: authorList,
          abstract,
          year,
          category,
          tags,
        };
        await papersApi.update(paper.id, data);
      }
      router.push('/');
      router.refresh();
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to save paper');
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
          Title *
        </label>
        <input
          type="text"
          value={title}
          onChange={(e) => setTitle(e.target.value)}
          required
          className="w-full px-4 py-2 border border-gray-300 dark:border-gray-600 rounded-md bg-white dark:bg-gray-800 text-gray-900 dark:text-white focus:ring-2 focus:ring-blue-500"
        />
      </div>

      <div>
        <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
          Authors (comma-separated) *
        </label>
        <input
          type="text"
          value={authors}
          onChange={(e) => setAuthors(e.target.value)}
          required
          placeholder="John Doe, Jane Smith"
          className="w-full px-4 py-2 border border-gray-300 dark:border-gray-600 rounded-md bg-white dark:bg-gray-800 text-gray-900 dark:text-white focus:ring-2 focus:ring-blue-500"
        />
      </div>

      <div>
        <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
          Abstract *
        </label>
        <textarea
          value={abstract}
          onChange={(e) => setAbstract(e.target.value)}
          required
          rows={6}
          className="w-full px-4 py-2 border border-gray-300 dark:border-gray-600 rounded-md bg-white dark:bg-gray-800 text-gray-900 dark:text-white focus:ring-2 focus:ring-blue-500"
        />
      </div>

      <div className="grid grid-cols-2 gap-4">
        <div>
          <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
            Year *
          </label>
          <input
            type="number"
            value={year}
            onChange={(e) => setYear(parseInt(e.target.value))}
            required
            min={1900}
            max={2100}
            className="w-full px-4 py-2 border border-gray-300 dark:border-gray-600 rounded-md bg-white dark:bg-gray-800 text-gray-900 dark:text-white focus:ring-2 focus:ring-blue-500"
          />
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
      </div>

      <TagManager tags={tags} onTagsChange={setTags} />

      <div className="flex gap-3">
        <LoadingButton
          type="submit"
          isLoading={loading}
          loadingText="Saving..."
          size="lg"
        >
          {mode === 'create' ? 'Create Paper' : 'Update Paper'}
        </LoadingButton>
        <LoadingButton
          type="button"
          variant="secondary"
          size="lg"
          onClick={() => router.back()}
        >
          Cancel
        </LoadingButton>
      </div>
    </form>
  );
}
