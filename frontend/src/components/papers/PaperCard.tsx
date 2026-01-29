'use client';

import Link from 'next/link';
import { Paper } from '@/types';
import { CategoryBadge } from '@/components/ui/Badge';
import { Tag } from '@/components/ui/Tag';
import { truncateText } from '@/lib/utils';

interface PaperCardProps {
  paper: Paper;
  onTagClick?: (tag: string) => void;
  isFavorite?: boolean;
  onToggleFavorite?: (paperId: string) => void;
}

export function PaperCard({ paper, onTagClick, isFavorite, onToggleFavorite }: PaperCardProps) {
  return (
    <article className="p-6 bg-white dark:bg-gray-800 rounded-lg shadow-md hover:shadow-lg transition-shadow">
      <div className="flex items-start justify-between gap-4 mb-3">
        <Link href={`/papers/${paper.id}`}>
          <h2 className="text-lg font-semibold text-gray-900 dark:text-white hover:text-blue-600 dark:hover:text-blue-400 line-clamp-2">
            {paper.title}
          </h2>
        </Link>
        <div className="flex items-center gap-2 flex-shrink-0">
          {onToggleFavorite && (
            <button
              onClick={() => onToggleFavorite(paper.id)}
              className="p-1 hover:bg-gray-100 dark:hover:bg-gray-700 rounded transition-colors"
              title={isFavorite ? 'Remove from favorites' : 'Add to favorites'}
            >
              {isFavorite ? (
                <svg className="w-5 h-5 text-yellow-500" fill="currentColor" viewBox="0 0 20 20">
                  <path d="M9.049 2.927c.3-.921 1.603-.921 1.902 0l1.07 3.292a1 1 0 00.95.69h3.462c.969 0 1.371 1.24.588 1.81l-2.8 2.034a1 1 0 00-.364 1.118l1.07 3.292c.3.921-.755 1.688-1.54 1.118l-2.8-2.034a1 1 0 00-1.175 0l-2.8 2.034c-.784.57-1.838-.197-1.539-1.118l1.07-3.292a1 1 0 00-.364-1.118L2.98 8.72c-.783-.57-.38-1.81.588-1.81h3.461a1 1 0 00.951-.69l1.07-3.292z" />
                </svg>
              ) : (
                <svg className="w-5 h-5 text-gray-400 hover:text-yellow-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M11.049 2.927c.3-.921 1.603-.921 1.902 0l1.519 4.674a1 1 0 00.95.69h4.915c.969 0 1.371 1.24.588 1.81l-3.976 2.888a1 1 0 00-.363 1.118l1.518 4.674c.3.922-.755 1.688-1.538 1.118l-3.976-2.888a1 1 0 00-1.176 0l-3.976 2.888c-.783.57-1.838-.197-1.538-1.118l1.518-4.674a1 1 0 00-.363-1.118l-3.976-2.888c-.784-.57-.38-1.81.588-1.81h4.914a1 1 0 00.951-.69l1.519-4.674z" />
                </svg>
              )}
            </button>
          )}
          <CategoryBadge category={paper.category} />
        </div>
      </div>

      <p className="text-sm text-gray-600 dark:text-gray-400 mb-2">
        {paper.authors.slice(0, 3).join(', ')}
        {paper.authors.length > 3 && ` +${paper.authors.length - 3} more`}
      </p>

      <p className="text-sm text-gray-700 dark:text-gray-300 mb-4 line-clamp-3">
        {truncateText(paper.abstract, 250)}
      </p>

      <div className="flex items-center justify-between">
        <div className="flex flex-wrap gap-1">
          {paper.tags.map((tag) => (
            <Tag
              key={tag.id}
              name={tag.name}
              onClick={onTagClick ? () => onTagClick(tag.name) : undefined}
            />
          ))}
        </div>

        <div className="flex items-center gap-3 text-sm text-gray-500 dark:text-gray-400">
          <span>{paper.year}</span>
          {paper.arxiv_url && (
            <a
              href={paper.arxiv_url}
              target="_blank"
              rel="noopener noreferrer"
              className="text-blue-600 hover:underline"
            >
              arXiv
            </a>
          )}
          {paper.paper_url && (
            <a
              href={paper.paper_url}
              target="_blank"
              rel="noopener noreferrer"
              className="text-blue-600 hover:underline"
            >
              {paper.paper_url.includes('acm.org') ? 'ACM' :
               paper.paper_url.includes('ieee') ? 'IEEE' : 'Paper'}
            </a>
          )}
        </div>
      </div>
    </article>
  );
}
