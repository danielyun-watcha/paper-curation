'use client';

import { useState, useEffect } from 'react';
import { useSearchParams } from 'next/navigation';
import { ScholarSearchResult, RelatedPaperResult } from '@/types';
import { papersApi } from '@/lib/api';

// Extract arxiv ID from URL
function extractArxivId(url: string): string | null {
  const match = url.match(/arxiv\.org\/(?:abs|pdf)\/([\d.]+)/);
  return match ? match[1] : null;
}

// Extract DOI from URL
function extractDoi(url: string): string | null {
  const match = url.match(/doi\.org\/(.+)/);
  return match ? match[1] : null;
}

export default function SearchPage() {
  const searchParams = useSearchParams();

  // Google Scholar search state
  const [query, setQuery] = useState('');
  const [searching, setSearching] = useState(false);
  const [results, setResults] = useState<ScholarSearchResult[]>([]);
  const [error, setError] = useState<string | null>(null);
  const [hasSearched, setHasSearched] = useState(false);

  // Add state
  const [addingIndex, setAddingIndex] = useState<number | null>(null);
  const [addedIndices, setAddedIndices] = useState<Set<number>>(new Set());

  // Connect state (connected papers panel)
  const [connectingIndex, setConnectingIndex] = useState<number | null>(null);
  const [connectedResults, setConnectedResults] = useState<RelatedPaperResult[]>([]);
  const [connectedSourceTitle, setConnectedSourceTitle] = useState('');
  const [hasConnected, setHasConnected] = useState(false);

  // Handle URL query params: ?connect={id} → auto-show connected papers
  const [autoConnectDone, setAutoConnectDone] = useState(false);
  useEffect(() => {
    const connectId = searchParams.get('connect');
    if (connectId && !autoConnectDone) {
      setAutoConnectDone(true);
      papersApi.getRelatedPapers(connectId).then(response => {
        setConnectedResults(response.results);
        setConnectedSourceTitle(response.paper_title);
        setHasConnected(true);
      }).catch(err => {
        console.error('Auto-connect failed:', err);
      });
    }
  }, [searchParams, autoConnectDone]);

  // Google Scholar search
  const handleSearch = async () => {
    if (!query.trim()) return;
    setSearching(true);
    setError(null);
    setHasSearched(true);
    setAddedIndices(new Set());
    try {
      const response = await papersApi.searchScholar(query.trim(), 5);
      setResults(response.results);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Search failed');
      setResults([]);
    } finally {
      setSearching(false);
    }
  };

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSearch();
    }
  };

  // Connect: find related papers for a search result or connected result
  const handleConnect = async (index: number, params: { arxiv_id?: string; doi?: string; title?: string }) => {
    setConnectingIndex(index);
    try {
      const response = await papersApi.getRelatedPapersExternal({
        arxiv_id: params.arxiv_id || undefined,
        doi: params.doi || undefined,
        title: !params.arxiv_id && !params.doi ? params.title : undefined,
      });
      setConnectedResults(response.results);
      setConnectedSourceTitle(params.title || '');
      setHasConnected(true);
      setAddedIndices(new Set());
    } catch (err) {
      alert(err instanceof Error ? err.message : 'Failed to find connected papers');
    } finally {
      setConnectingIndex(null);
    }
  };

  // Connect from Scholar result
  const handleConnectScholar = (index: number, result: ScholarSearchResult) => {
    const arxivId = extractArxivId(result.url || '') || extractArxivId(result.pub_url || '');
    const doi = extractDoi(result.url || '') || extractDoi(result.pub_url || '');
    handleConnect(index, { arxiv_id: arxivId || undefined, doi: doi || undefined, title: result.title });
  };

  // Connect from Connected result (chain)
  const handleConnectChain = (index: number, result: RelatedPaperResult) => {
    handleConnect(index, { arxiv_id: result.arxiv_id || undefined, doi: result.doi || undefined, title: result.title });
  };

  // Add paper from Scholar result
  const handleAddScholar = async (index: number, result: ScholarSearchResult) => {
    setAddingIndex(index);
    try {
      await papersApi.addFromScholar({
        title: result.title,
        authors: result.authors,
        abstract: result.abstract || undefined,
        year: result.year || undefined,
        url: result.url || undefined,
        category: 'other',
      });
      setAddedIndices(prev => new Set(prev).add(index));
    } catch (err) {
      alert(err instanceof Error ? err.message : 'Failed to add paper');
    } finally {
      setAddingIndex(null);
    }
  };

  // Add paper from Connected result
  const handleAddConnected = async (index: number, result: RelatedPaperResult) => {
    setAddingIndex(index);
    try {
      const url = result.url
        || (result.arxiv_id ? `https://arxiv.org/abs/${result.arxiv_id}` : undefined)
        || (result.doi ? `https://doi.org/${result.doi}` : undefined);
      await papersApi.addFromScholar({
        title: result.title,
        authors: result.authors,
        abstract: result.abstract || undefined,
        year: result.year || undefined,
        url: url,
        category: 'other',
      });
      setAddedIndices(prev => new Set(prev).add(index));
    } catch (err) {
      alert(err instanceof Error ? err.message : 'Failed to add paper');
    } finally {
      setAddingIndex(null);
    }
  };

  // Shared result card renderer
  const renderResultCard = (
    index: number,
    title: string,
    url: string | null,
    authors: string[],
    year: number | null,
    abstract: string | null,
    citedBy: number,
    sourceUrl: string | null,
    onAdd: () => void,
    onConnect: () => void,
    displayIndex?: number,
  ) => (
    <li key={index} className="p-4 hover:bg-gray-50 dark:hover:bg-gray-700/50 transition-colors">
      <div className="flex justify-between items-start gap-4">
        <div className="flex-1 min-w-0">
          <div className="flex items-start gap-2">
            <span className="text-sm font-medium text-blue-600 dark:text-blue-400 flex-shrink-0">
              #{(displayIndex ?? index) + 1}
            </span>
            <h3 className="font-medium text-gray-900 dark:text-white leading-snug">
              {url ? (
                <a href={url} target="_blank" rel="noopener noreferrer" className="hover:text-blue-600 dark:hover:text-blue-400">
                  {title}
                </a>
              ) : title}
            </h3>
          </div>

          <p className="text-sm text-gray-500 dark:text-gray-400 mt-1 ml-6">
            {authors.slice(0, 4).join(', ')}
            {authors.length > 4 && ` +${authors.length - 4} more`}
            {year && ` · ${year}`}
          </p>

          {abstract && (
            <p className="text-sm text-gray-600 dark:text-gray-300 mt-2 ml-6 line-clamp-2">
              {abstract}
            </p>
          )}

          <div className="mt-3 ml-6 flex items-center gap-2">
            {addedIndices.has(index) ? (
              <span className="inline-flex items-center gap-1 text-sm text-green-600 dark:text-green-400">
                <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
                </svg>
                Added
              </span>
            ) : (
              <button
                onClick={onAdd}
                disabled={addingIndex === index}
                className="inline-flex items-center gap-1 text-xs px-2 py-1 bg-blue-600 text-white rounded hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed"
              >
                {addingIndex === index ? (
                  <>
                    <svg className="animate-spin h-3 w-3" viewBox="0 0 24 24">
                      <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" fill="none" />
                      <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
                    </svg>
                    Adding...
                  </>
                ) : (
                  <>
                    <svg className="w-3 h-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 4v16m8-8H4" />
                    </svg>
                    Add
                  </>
                )}
              </button>
            )}

            <button
              onClick={onConnect}
              disabled={connectingIndex === index}
              className="inline-flex items-center gap-1 text-xs px-2 py-1 bg-purple-600 text-white rounded hover:bg-purple-700 disabled:opacity-50 disabled:cursor-not-allowed"
            >
              {connectingIndex === index ? (
                <>
                  <svg className="animate-spin h-3 w-3" viewBox="0 0 24 24">
                    <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" fill="none" />
                    <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
                  </svg>
                  Connecting...
                </>
              ) : (
                <>
                  <svg className="w-3 h-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13.828 10.172a4 4 0 00-5.656 0l-4 4a4 4 0 105.656 5.656l1.102-1.101m-.758-4.899a4 4 0 005.656 0l4-4a4 4 0 00-5.656-5.656l-1.1 1.1" />
                  </svg>
                  Connect
                </>
              )}
            </button>
          </div>
        </div>

        <div className="flex flex-col items-end gap-2 flex-shrink-0">
          {citedBy > 0 && (
            <div className="flex items-center gap-1 text-sm text-gray-500 dark:text-gray-400">
              <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 7h12m0 0l-4-4m4 4l-4 4m0 6H4m0 0l4 4m-4-4l4-4" />
              </svg>
              <span>{citedBy.toLocaleString()}</span>
            </div>
          )}
          {sourceUrl && (
            <a href={sourceUrl} target="_blank" rel="noopener noreferrer" className="text-xs text-blue-600 hover:underline">
              View Source
            </a>
          )}
        </div>
      </div>
    </li>
  );

  return (
    <div className={`${hasConnected ? 'max-w-7xl' : 'max-w-4xl'} mx-auto space-y-6 transition-all`}>
      <h1 className="text-2xl font-bold text-gray-900 dark:text-white">
        Similar Paper Search
      </h1>

      <div className={hasConnected ? "grid grid-cols-1 lg:grid-cols-2 gap-6 items-start" : ""}>
        {/* Left column: Search + Results */}
        <div className="space-y-6">
          <div className="bg-white dark:bg-gray-800 rounded-lg shadow-md p-6">
            <div className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                  Enter paper title or abstract to find similar papers
                </label>
                <textarea
                  value={query}
                  onChange={(e) => setQuery(e.target.value)}
                  onKeyDown={handleKeyDown}
                  placeholder="Paste a paper title, abstract, or describe the topic you're looking for..."
                  rows={4}
                  className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md
                           bg-white dark:bg-gray-700 text-gray-900 dark:text-white
                           focus:outline-none focus:ring-2 focus:ring-blue-500 resize-none"
                />
              </div>

              <button
                onClick={handleSearch}
                disabled={!query.trim() || searching}
                className="w-full py-2 px-4 bg-blue-600 text-white rounded-md hover:bg-blue-700
                         disabled:bg-gray-400 disabled:cursor-not-allowed transition-colors
                         flex items-center justify-center gap-2"
              >
                {searching ? (
                  <>
                    <svg className="animate-spin h-4 w-4" viewBox="0 0 24 24">
                      <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" fill="none" />
                      <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z" />
                    </svg>
                    Searching Google Scholar...
                  </>
                ) : (
                  <>
                    <svg className="w-4 h-4" viewBox="0 0 24 24" fill="currentColor">
                      <path d="M12 24a7 7 0 1 1 0-14 7 7 0 0 1 0 14zm0-24L0 9.5l4.838 3.94A8 8 0 0 1 12 9a8 8 0 0 1 7.162 4.44L24 9.5 12 0z" />
                    </svg>
                    Find Similar Papers
                  </>
                )}
              </button>
            </div>
          </div>

          {/* Error */}
          {error && (
            <div className="bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded-lg p-4">
              <p className="text-red-700 dark:text-red-300">{error}</p>
            </div>
          )}

          {/* Scholar results */}
          {hasSearched && !searching && !error && (
            <div className="bg-white dark:bg-gray-800 rounded-lg shadow-md overflow-hidden">
              <div className="p-4 border-b border-gray-200 dark:border-gray-700">
                <h2 className="font-semibold text-gray-900 dark:text-white">
                  Google Scholar Results
                  {results.length > 0 && (
                    <span className="ml-2 text-sm font-normal text-gray-500">
                      ({results.length} papers found, sorted by relevance)
                    </span>
                  )}
                </h2>
              </div>

              {results.length === 0 ? (
                <div className="p-8 text-center text-gray-500 dark:text-gray-400">
                  No similar papers found. Try a different query.
                </div>
              ) : (
                <ul className="divide-y divide-gray-200 dark:divide-gray-700">
                  {results.map((result, index) =>
                    renderResultCard(
                      index,
                      result.title,
                      result.url,
                      result.authors,
                      result.year,
                      result.abstract,
                      result.cited_by,
                      result.pub_url,
                      () => handleAddScholar(index, result),
                      () => handleConnectScholar(index, result),
                    )
                  )}
                </ul>
              )}
            </div>
          )}

          {/* Info box */}
          {!hasSearched && !hasConnected && (
            <div className="bg-blue-50 dark:bg-blue-900/20 border border-blue-200 dark:border-blue-800 rounded-lg p-4">
              <p className="text-blue-800 dark:text-blue-200 text-sm">
                <strong>Tip:</strong> Enter a paper title, abstract, or topic description to find related papers from Google Scholar.
                Results are sorted by relevance. You can add papers directly to your collection, or click Connect to find related papers.
              </p>
            </div>
          )}
        </div>

        {/* Right column: Connected Papers */}
        {hasConnected && (
          <div className="lg:sticky lg:top-4">
            <div className="bg-white dark:bg-gray-800 rounded-lg shadow-md overflow-hidden border-2 border-purple-200 dark:border-purple-800">
              <div className="p-4 border-b border-purple-200 dark:border-purple-700 bg-purple-50 dark:bg-purple-900/20">
                <h2 className="font-semibold text-purple-800 dark:text-purple-200 flex items-center gap-2">
                  <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13.828 10.172a4 4 0 00-5.656 0l-4 4a4 4 0 105.656 5.656l1.102-1.101m-.758-4.899a4 4 0 005.656 0l4-4a4 4 0 00-5.656-5.656l-1.1 1.1" />
                  </svg>
                  Connected Papers
                </h2>
                {connectedSourceTitle && (
                  <p className="text-sm text-purple-600 dark:text-purple-400 mt-1 truncate">
                    for &ldquo;{connectedSourceTitle}&rdquo;
                  </p>
                )}
              </div>

              {connectedResults.length === 0 ? (
                <div className="p-8 text-center text-gray-500 dark:text-gray-400">
                  No connected papers found.
                </div>
              ) : (
                <ul className="divide-y divide-gray-200 dark:divide-gray-700">
                  {connectedResults.map((result, index) => {
                    const paperUrl = result.url
                      || (result.arxiv_id ? `https://arxiv.org/abs/${result.arxiv_id}` : null)
                      || (result.doi ? `https://doi.org/${result.doi}` : null);
                    const offsetIndex = index + 100;
                    return renderResultCard(
                      offsetIndex,
                      result.title,
                      paperUrl,
                      result.authors,
                      result.year,
                      result.abstract,
                      result.cited_by,
                      paperUrl,
                      () => handleAddConnected(offsetIndex, result),
                      () => handleConnectChain(offsetIndex, result),
                      index,
                    );
                  })}
                </ul>
              )}
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
