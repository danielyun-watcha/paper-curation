'use client';

import Link from 'next/link';
import { Paper } from '@/types';
import { CategoryBadge } from '@/components/ui/Badge';
import { Tag } from '@/components/ui/Tag';
import { truncateText } from '@/lib/utils';
import { ReadingStatus, READING_STATUS_ICONS } from '@/hooks/useReadingStatus';

interface PaperCardProps {
  paper: Paper;
  onTagClick?: (tag: string) => void;
  readingStatus?: ReadingStatus;
  onStatusChange?: (status: ReadingStatus) => void;
}

export function PaperCard({ paper, onTagClick, readingStatus = 'none', onStatusChange }: PaperCardProps) {
  return (
    <article className="p-6 bg-white dark:bg-gray-800 rounded-lg shadow-md hover:shadow-lg transition-shadow">
      <div className="flex items-start justify-between gap-4 mb-3">
        <Link href={`/papers/${paper.id}`}>
          <h2 className="text-lg font-semibold text-gray-900 dark:text-white hover:text-blue-600 dark:hover:text-blue-400 line-clamp-2">
            {paper.title}
          </h2>
        </Link>
        <div className="flex items-center gap-2 flex-shrink-0">
          {onStatusChange && (
            <select
              value={readingStatus}
              onChange={(e) => onStatusChange(e.target.value as ReadingStatus)}
              onClick={(e) => e.stopPropagation()}
              className="text-sm px-1.5 py-0.5 border border-gray-300 dark:border-gray-600 rounded bg-white dark:bg-gray-700 text-gray-700 dark:text-gray-300 cursor-pointer focus:outline-none focus:ring-1 focus:ring-blue-500"
            >
              <option value="none">-</option>
              <option value="favorite">{READING_STATUS_ICONS.favorite}</option>
              <option value="to_read">{READING_STATUS_ICONS.to_read}</option>
              <option value="read">{READING_STATUS_ICONS.read}</option>
            </select>
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
