'use client';

import { useState } from 'react';
import Link from 'next/link';
import { Paper, PaperSummary, PaperTranslation, TranslationResponse } from '@/types';
import { CategoryBadge } from '@/components/ui/Badge';
import { Tag } from '@/components/ui/Tag';
import { formatDate } from '@/lib/utils';
import { papersApi } from '@/lib/api';
import { ReadingStatus, READING_STATUS_LABELS, READING_STATUS_ICONS } from '@/hooks/useReadingStatus';

interface PaperDetailProps {
  paper: Paper;
  onDelete?: () => void;
  readingStatus?: ReadingStatus;
  onStatusChange?: (status: ReadingStatus) => void;
}

export function PaperDetail({ paper, onDelete, readingStatus = 'none', onStatusChange }: PaperDetailProps) {
  const [summary, setSummary] = useState<PaperSummary | null>(paper.summary);
  const [generating, setGenerating] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [translation, setTranslation] = useState<PaperTranslation | null>(paper.translation);
  const [translating, setTranslating] = useState(false);
  const [translationError, setTranslationError] = useState<string | null>(null);
  const [showSummary, setShowSummary] = useState(true);
  const [showTranslation, setShowTranslation] = useState(true);

  const handleGenerateSummary = async () => {
    setGenerating(true);
    setError(null);
    try {
      const newSummary = await papersApi.generateSummary(paper.id);
      setSummary(newSummary);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to generate summary');
    } finally {
      setGenerating(false);
    }
  };

  const handleTranslate = async () => {
    setTranslating(true);
    setTranslationError(null);
    try {
      const result = await papersApi.translate(paper.id);
      setTranslation({
        title: result.translated_title,
        abstract: result.translated_abstract,
      });
    } catch (err) {
      setTranslationError(err instanceof Error ? err.message : 'Translation failed');
    } finally {
      setTranslating(false);
    }
  };

  return (
    <article className="bg-white dark:bg-gray-800 rounded-lg shadow-md p-8">
      <div className="flex items-start justify-between gap-4 mb-4">
        <h1 className="text-2xl font-bold text-gray-900 dark:text-white">
          {paper.title}
        </h1>
        <div className="flex items-center gap-2 flex-shrink-0">
          {onStatusChange && (
            <select
              value={readingStatus}
              onChange={(e) => onStatusChange(e.target.value as ReadingStatus)}
              className="px-3 py-1.5 text-sm border border-gray-300 dark:border-gray-600 rounded-md bg-white dark:bg-gray-700 text-gray-700 dark:text-gray-300 cursor-pointer focus:outline-none focus:ring-2 focus:ring-blue-500"
            >
              <option value="none">Status: -</option>
              <option value="favorite">{READING_STATUS_ICONS.favorite} {READING_STATUS_LABELS.favorite}</option>
              <option value="to_read">{READING_STATUS_ICONS.to_read} {READING_STATUS_LABELS.to_read}</option>
              <option value="read">{READING_STATUS_ICONS.read} {READING_STATUS_LABELS.read}</option>
            </select>
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

      {/* AI Summary Section */}
      <div className="mb-6 p-4 bg-gradient-to-r from-purple-50 to-blue-50 dark:from-purple-900/20 dark:to-blue-900/20 rounded-lg border border-purple-200 dark:border-purple-800">
        <div className="flex items-center justify-between mb-3">
          <h3 className="text-sm font-medium text-purple-700 dark:text-purple-300 flex items-center gap-2">
            <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 10V3L4 14h7v7l9-11h-7z" />
            </svg>
            TL;DR
          </h3>
          <div className="flex items-center gap-2">
            <button
              onClick={handleGenerateSummary}
              disabled={generating}
              className="px-3 py-1 text-xs bg-purple-600 text-white rounded-md hover:bg-purple-700 disabled:bg-gray-400 disabled:cursor-not-allowed transition-colors flex items-center gap-1"
            >
              {generating ? (
                <>
                  <svg className="animate-spin h-3 w-3" viewBox="0 0 24 24">
                    <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" fill="none" />
                    <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z" />
                  </svg>
                  Generating...
                </>
              ) : summary ? (
                'Regenerate'
              ) : (
                'Generate'
              )}
            </button>
            <button
              onClick={handleTranslate}
              disabled={translating}
              className="px-3 py-1 text-xs bg-green-600 text-white rounded-md hover:bg-green-700 disabled:bg-gray-400 disabled:cursor-not-allowed transition-colors flex items-center gap-1"
            >
              {translating ? (
                <>
                  <svg className="animate-spin h-3 w-3" viewBox="0 0 24 24">
                    <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" fill="none" />
                    <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z" />
                  </svg>
                  Translating...
                </>
              ) : translation ? (
                'Retranslate'
              ) : (
                'Translate'
              )}
            </button>
          </div>
        </div>

        {error && (
          <div className="text-red-600 dark:text-red-400 text-sm mb-3">
            {error}
          </div>
        )}

        {translationError && (
          <div className="text-red-600 dark:text-red-400 text-sm mb-3">
            {translationError}
          </div>
        )}

        {summary?.one_line ? (
          <div>
            <div className="flex items-center justify-between">
              <button
                onClick={() => setShowSummary(!showSummary)}
                className="flex items-center gap-1 text-xs text-purple-600 dark:text-purple-400 hover:underline"
              >
                <svg
                  className={`w-3 h-3 transition-transform ${showSummary ? 'rotate-90' : ''}`}
                  fill="currentColor"
                  viewBox="0 0 20 20"
                >
                  <path fillRule="evenodd" d="M7.293 14.707a1 1 0 010-1.414L10.586 10 7.293 6.707a1 1 0 011.414-1.414l4 4a1 1 0 010 1.414l-4 4a1 1 0 01-1.414 0z" clipRule="evenodd" />
                </svg>
                {showSummary ? 'Hide' : 'Show'} Summary
              </button>
            </div>
            {showSummary && (
              <p className="text-gray-800 dark:text-gray-200 mt-2">
                {summary.one_line}
              </p>
            )}
          </div>
        ) : (
          <p className="text-gray-500 dark:text-gray-400 text-sm">
            Click &quot;Generate&quot; to create a TL;DR summary.
          </p>
        )}

        {translation && (
          <div className="mt-4 pt-4 border-t border-purple-200 dark:border-purple-700">
            <button
              onClick={() => setShowTranslation(!showTranslation)}
              className="flex items-center gap-1 text-xs text-green-600 dark:text-green-400 hover:underline"
            >
              <svg
                className={`w-3 h-3 transition-transform ${showTranslation ? 'rotate-90' : ''}`}
                fill="currentColor"
                viewBox="0 0 20 20"
              >
                <path fillRule="evenodd" d="M7.293 14.707a1 1 0 010-1.414L10.586 10 7.293 6.707a1 1 0 011.414-1.414l4 4a1 1 0 010 1.414l-4 4a1 1 0 01-1.414 0z" clipRule="evenodd" />
              </svg>
              {showTranslation ? 'Hide' : 'Show'} Korean Translation
            </button>
            {showTranslation && (
              <div className="mt-2">
                {translation.title && (
                  <p className="text-gray-800 dark:text-gray-200 font-medium mb-2">
                    {translation.title}
                  </p>
                )}
                <p className="text-gray-700 dark:text-gray-300 text-sm leading-relaxed whitespace-pre-wrap">
                  {translation.abstract}
                </p>
              </div>
            )}
          </div>
        )}
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
        <Link
          href={`/study?paper=${paper.id}`}
          className="px-4 py-2 bg-green-600 text-white rounded-md hover:bg-green-700 transition-colors flex items-center gap-1"
        >
          <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 6.253v13m0-13C10.832 5.477 9.246 5 7.5 5S4.168 5.477 3 6.253v13C4.168 18.477 5.754 18 7.5 18s3.332.477 4.5 1.253m0-13C13.168 5.477 14.754 5 16.5 5c1.747 0 3.332.477 4.5 1.253v13C19.832 18.477 18.247 18 16.5 18c-1.746 0-3.332.477-4.5 1.253" />
          </svg>
          Study
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
