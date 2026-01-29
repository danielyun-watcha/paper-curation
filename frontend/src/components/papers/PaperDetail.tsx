'use client';

import Link from 'next/link';
import { Paper } from '@/types';
import { CategoryBadge } from '@/components/ui/Badge';
import { Tag } from '@/components/ui/Tag';
import { formatDate } from '@/lib/utils';

interface PaperDetailProps {
  paper: Paper;
  onDelete?: () => void;
  isFavorite?: boolean;
  onToggleFavorite?: (paperId: string) => void;
}

export function PaperDetail({ paper, onDelete, isFavorite, onToggleFavorite }: PaperDetailProps) {
  return (
    <article className="bg-white dark:bg-gray-800 rounded-lg shadow-md p-8">
      <div className="flex items-start justify-between gap-4 mb-4">
        <h1 className="text-2xl font-bold text-gray-900 dark:text-white">
          {paper.title}
        </h1>
        <div className="flex items-center gap-2 flex-shrink-0">
          {onToggleFavorite && (
            <button
              onClick={() => onToggleFavorite(paper.id)}
              className="p-2 hover:bg-gray-100 dark:hover:bg-gray-700 rounded transition-colors"
              title={isFavorite ? 'Remove from favorites' : 'Add to favorites'}
            >
              {isFavorite ? (
                <svg className="w-6 h-6 text-yellow-500" fill="currentColor" viewBox="0 0 20 20">
                  <path d="M9.049 2.927c.3-.921 1.603-.921 1.902 0l1.07 3.292a1 1 0 00.95.69h3.462c.969 0 1.371 1.24.588 1.81l-2.8 2.034a1 1 0 00-.364 1.118l1.07 3.292c.3.921-.755 1.688-1.54 1.118l-2.8-2.034a1 1 0 00-1.175 0l-2.8 2.034c-.784.57-1.838-.197-1.539-1.118l1.07-3.292a1 1 0 00-.364-1.118L2.98 8.72c-.783-.57-.38-1.81.588-1.81h3.461a1 1 0 00.951-.69l1.07-3.292z" />
                </svg>
              ) : (
                <svg className="w-6 h-6 text-gray-400 hover:text-yellow-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M11.049 2.927c.3-.921 1.603-.921 1.902 0l1.519 4.674a1 1 0 00.95.69h4.915c.969 0 1.371 1.24.588 1.81l-3.976 2.888a1 1 0 00-.363 1.118l1.518 4.674c.3.922-.755 1.688-1.538 1.118l-3.976-2.888a1 1 0 00-1.176 0l-3.976 2.888c-.783.57-1.838-.197-1.538-1.118l1.518-4.674a1 1 0 00-.363-1.118l-3.976-2.888c-.784-.57-.38-1.81.588-1.81h4.914a1 1 0 00.951-.69l1.519-4.674z" />
                </svg>
              )}
            </button>
          )}
          <CategoryBadge category={paper.category} />
        </div>
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
        {paper.published_at && (
          <div>
            <h3 className="text-sm font-medium text-gray-500 dark:text-gray-400 mb-1">
              Published
            </h3>
            <p className="text-gray-800 dark:text-gray-200">
              {paper.published_at}
            </p>
          </div>
        )}

        {paper.doi ? (
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
        ) : paper.arxiv_id && (
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

        <div>
          <h3 className="text-sm font-medium text-gray-500 dark:text-gray-400 mb-1">
            Conference
          </h3>
          <p className="text-gray-800 dark:text-gray-200">
            {paper.conference || (paper.arxiv_id ? 'arXiv' : '-')}
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
