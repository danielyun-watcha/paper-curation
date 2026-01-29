'use client';

import Link from 'next/link';
import { Paper } from '@/types';
import { CategoryBadge } from '@/components/ui/Badge';
import { Tag } from '@/components/ui/Tag';
import { formatDate } from '@/lib/utils';

interface PaperDetailProps {
  paper: Paper;
  onDelete?: () => void;
}

export function PaperDetail({ paper, onDelete }: PaperDetailProps) {
  return (
    <article className="bg-white dark:bg-gray-800 rounded-lg shadow-md p-8">
      <div className="flex items-start justify-between gap-4 mb-4">
        <h1 className="text-2xl font-bold text-gray-900 dark:text-white">
          {paper.title}
        </h1>
        <CategoryBadge category={paper.category} />
      </div>

      <div className="mb-6">
        <h3 className="text-sm font-medium text-gray-500 dark:text-gray-400 mb-1">
          Authors
        </h3>
        <p className="text-gray-800 dark:text-gray-200">
          {paper.authors.join(', ')}
        </p>
      </div>

      <div className="mb-6">
        <h3 className="text-sm font-medium text-gray-500 dark:text-gray-400 mb-1">
          Abstract
        </h3>
        <p className="text-gray-700 dark:text-gray-300 whitespace-pre-wrap leading-relaxed">
          {paper.abstract}
        </p>
      </div>

      <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-6">
        <div>
          <h3 className="text-sm font-medium text-gray-500 dark:text-gray-400 mb-1">
            Year
          </h3>
          <p className="text-gray-800 dark:text-gray-200">{paper.year}</p>
        </div>

        {paper.arxiv_id && (
          <div>
            <h3 className="text-sm font-medium text-gray-500 dark:text-gray-400 mb-1">
              arXiv ID
            </h3>
            <a
              href={paper.arxiv_url || '#'}
              target="_blank"
              rel="noopener noreferrer"
              className="text-blue-600 hover:underline"
            >
              {paper.arxiv_id}
            </a>
          </div>
        )}

        {paper.doi && (
          <div>
            <h3 className="text-sm font-medium text-gray-500 dark:text-gray-400 mb-1">
              DOI
            </h3>
            <a
              href={paper.paper_url || `https://doi.org/${paper.doi}`}
              target="_blank"
              rel="noopener noreferrer"
              className="text-blue-600 hover:underline"
            >
              {paper.doi}
            </a>
          </div>
        )}

        <div>
          <h3 className="text-sm font-medium text-gray-500 dark:text-gray-400 mb-1">
            Created
          </h3>
          <p className="text-gray-800 dark:text-gray-200">
            {formatDate(paper.created_at)}
          </p>
        </div>

        <div>
          <h3 className="text-sm font-medium text-gray-500 dark:text-gray-400 mb-1">
            Updated
          </h3>
          <p className="text-gray-800 dark:text-gray-200">
            {formatDate(paper.updated_at)}
          </p>
        </div>
      </div>

      {paper.tags.length > 0 && (
        <div className="mb-6">
          <h3 className="text-sm font-medium text-gray-500 dark:text-gray-400 mb-2">
            Tags
          </h3>
          <div className="flex flex-wrap gap-2">
            {paper.tags.map((tag) => (
              <Tag key={tag.id} name={tag.name} />
            ))}
          </div>
        </div>
      )}

      <div className="flex gap-3 pt-4 border-t border-gray-200 dark:border-gray-700">
        <Link
          href={`/papers/${paper.id}/edit`}
          className="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 transition-colors"
        >
          Edit
        </Link>
        {onDelete && (
          <button
            onClick={onDelete}
            className="px-4 py-2 bg-red-600 text-white rounded-md hover:bg-red-700 transition-colors"
          >
            Delete
          </button>
        )}
        <Link
          href="/"
          className="px-4 py-2 bg-gray-200 text-gray-700 dark:bg-gray-700 dark:text-gray-200 rounded-md hover:bg-gray-300 dark:hover:bg-gray-600 transition-colors"
        >
          Back to List
        </Link>
      </div>
    </article>
  );
}
