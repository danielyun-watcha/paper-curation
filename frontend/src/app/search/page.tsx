'use client';

import { useEffect, useState, Suspense } from 'react';
import { useSearchParams } from 'next/navigation';
import { buildPaperUrl } from '@/lib/extractors';
import ConnectedPapersGraph from '@/components/ConnectedPapersGraph';
import { useScholarSearch } from '@/hooks/useScholarSearch';
import { useConnectedPapers } from '@/hooks/useConnectedPapers';
import { useAddPaper } from '@/hooks/useAddPaper';

export default function SearchPage() {
  return (
    <Suspense fallback={<SearchPageLoading />}>
      <SearchPageContent />
    </Suspense>
  );
}

function SearchPageLoading() {
  return (
    <div className="flex items-center justify-center h-64">
      <div className="text-gray-500">Loading...</div>
    </div>
  );
}

function SearchPageContent() {
  const searchParams = useSearchParams();

  // Custom hooks for state management
  const {
    handleAddFromScholar,
    handleAddFromRelated,
    resetAddedIndices,
    isAdded,
    isAdding,
  } = useAddPaper();

  const {
    connectedResults,
    sourceTitle: connectedSourceTitle,
    sourceYear: connectedSourceYear,
    sourceCitations: connectedSourceCitations,
    hasConnected,
    connectingIndex,
    handleConnectFromScholar,
    handleConnectFromRelated,
    handleConnectById,
    clearConnected,
  } = useConnectedPapers(resetAddedIndices);

  const {
    query,
    setQuery,
    searching,
    results,
    error,
    hasSearched,
    handleSearch,
    handleKeyDown,
  } = useScholarSearch(() => {
    // Clear connected papers when new search starts
    clearConnected();
    resetAddedIndices();
  });

  // Handle URL query params: ?connect={id} -> auto-show connected papers
  const [autoConnectDone, setAutoConnectDone] = useState(false);
  useEffect(() => {
    const connectId = searchParams.get('connect');
    if (connectId && !autoConnectDone) {
      setAutoConnectDone(true);
      handleConnectById(connectId);
    }
  }, [searchParams, autoConnectDone, handleConnectById]);

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
            {isAdded(index) ? (
              <span className="inline-flex items-center gap-1 text-sm text-green-600 dark:text-green-400">
                <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
                </svg>
                Added
              </span>
            ) : (
              <button
                onClick={onAdd}
                disabled={isAdding(index)}
                className="inline-flex items-center gap-1 text-xs px-2 py-1 bg-blue-600 text-white rounded hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed"
              >
                {isAdding(index) ? (
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

      {/* Search Box */}
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

      {/* Info box */}
      {!hasSearched && !hasConnected && (
        <div className="bg-blue-50 dark:bg-blue-900/20 border border-blue-200 dark:border-blue-800 rounded-lg p-4">
          <p className="text-blue-800 dark:text-blue-200 text-sm">
            <strong>Tip:</strong> Enter a paper title, abstract, or topic description to find related papers from Google Scholar.
            Results are sorted by relevance. You can add papers directly to your collection, or click Connect to find related papers.
          </p>
        </div>
      )}

      {/* Two different layouts based on whether graph is shown */}
      {hasConnected ? (
        /* Layout with graph: 3-column grid */
        <div className="grid grid-cols-1 lg:grid-cols-12 gap-4">
          {/* Left column: Scholar results (compact) */}
          {hasSearched && !searching && !error && (
            <div className="lg:col-span-2">
              <div className="bg-white dark:bg-gray-800 rounded-lg shadow-md overflow-hidden h-[600px] flex flex-col">
                <div className="p-3 border-b border-gray-200 dark:border-gray-700 flex-shrink-0">
                  <h2 className="text-sm font-semibold text-gray-900 dark:text-white">
                    Scholar Results
                    {results.length > 0 && (
                      <span className="block text-xs font-normal text-gray-500 mt-0.5">
                        {results.length} papers
                      </span>
                    )}
                  </h2>
                </div>

                {results.length === 0 ? (
                  <div className="p-4 text-center text-sm text-gray-500 dark:text-gray-400">
                    No papers found
                  </div>
                ) : (
                  <ul className="divide-y divide-gray-200 dark:divide-gray-700 flex-1 overflow-y-auto">
                    {results.map((result, index) => (
                      <li key={index} className="p-3 hover:bg-gray-50 dark:hover:bg-gray-700/50 transition-colors">
                        <div className="space-y-2">
                          <div className="flex items-start gap-1.5">
                            <span className="text-xs font-medium text-blue-600 dark:text-blue-400 flex-shrink-0">
                              #{index + 1}
                            </span>
                            <h3 className="text-xs font-medium text-gray-900 dark:text-white leading-tight line-clamp-2">
                              {result.url ? (
                                <a href={result.url} target="_blank" rel="noopener noreferrer" className="hover:text-blue-600 dark:hover:text-blue-400">
                                  {result.title}
                                </a>
                              ) : result.title}
                            </h3>
                          </div>

                          <p className="text-xs text-gray-500 dark:text-gray-400">
                            {result.authors.slice(0, 2).join(', ')}
                            {result.authors.length > 2 && ` +${result.authors.length - 2}`}
                            {result.year && ` · ${result.year}`}
                          </p>

                          <div className="flex gap-1.5">
                            {isAdded(index) ? (
                              <span className="inline-flex items-center gap-0.5 text-xs text-green-600 dark:text-green-400">
                                <svg className="w-3 h-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
                                </svg>
                                Added
                              </span>
                            ) : (
                              <>
                                <button
                                  onClick={() => handleAddFromScholar(index, result)}
                                  disabled={isAdding(index)}
                                  className="text-xs px-1.5 py-0.5 bg-blue-600 text-white rounded hover:bg-blue-700 disabled:opacity-50"
                                >
                                  {isAdding(index) ? 'Adding...' : 'Add'}
                                </button>
                                <button
                                  onClick={() => handleConnectFromScholar(index, result)}
                                  disabled={connectingIndex === index}
                                  className="text-xs px-1.5 py-0.5 bg-purple-600 text-white rounded hover:bg-purple-700 disabled:opacity-50"
                                >
                                  {connectingIndex === index ? 'Connecting...' : 'Connect'}
                                </button>
                              </>
                            )}
                          </div>
                        </div>
                      </li>
                    ))}
                  </ul>
                )}
              </div>
            </div>
          )}

          {/* Middle column: Graph */}
          <div className={`${hasSearched && !searching && !error ? 'lg:col-span-5' : 'lg:col-span-7'}`}>
            {connectedResults.length > 0 && (
              <div className="bg-white dark:bg-gray-800 rounded-lg shadow-md overflow-hidden border-2 border-purple-200 dark:border-purple-800 h-[600px] flex flex-col">
                <div className="p-3 border-b border-purple-200 dark:border-purple-700 bg-gradient-to-r from-purple-50 to-purple-100 dark:from-purple-900/20 dark:to-purple-800/20 flex-shrink-0">
                  <div className="flex items-start gap-2">
                    <svg className="w-4 h-4 text-purple-600 dark:text-purple-400 flex-shrink-0 mt-0.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13.828 10.172a4 4 0 00-5.656 0l-4 4a4 4 0 105.656 5.656l1.102-1.101m-.758-4.899a4 4 0 005.656 0l4-4a4 4 0 00-5.656-5.656l-1.1 1.1" />
                    </svg>
                    <div className="flex-1 min-w-0">
                      <h2 className="font-semibold text-purple-800 dark:text-purple-200 text-xs mb-1">
                        Connected Papers Graph
                      </h2>
                      {connectedSourceTitle && (
                        <p className="text-sm font-semibold text-gray-900 dark:text-white leading-snug line-clamp-2">
                          &ldquo;{connectedSourceTitle}&rdquo;
                        </p>
                      )}
                    </div>
                  </div>
                </div>

                <div className="flex-1 min-h-0">
                  <ConnectedPapersGraph
                    sourceTitle={connectedSourceTitle}
                    sourceYear={connectedSourceYear}
                    sourceCitations={connectedSourceCitations}
                    connectedPapers={connectedResults}
                  />
                </div>
              </div>
            )}
          </div>

          {/* Right column: Paper Details */}
          <div className={`${hasSearched && !searching && !error ? 'lg:col-span-5' : 'lg:col-span-5'}`}>
            <div className="bg-white dark:bg-gray-800 rounded-lg shadow-md overflow-hidden border-2 border-purple-200 dark:border-purple-800 h-[600px] flex flex-col">
              <div className="p-3 border-b border-purple-200 dark:border-purple-700 bg-purple-50 dark:bg-purple-900/20 flex-shrink-0">
                <h2 className="text-sm font-semibold text-purple-800 dark:text-purple-200 flex items-center gap-2">
                  <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 6h16M4 10h16M4 14h16M4 18h16" />
                  </svg>
                  Paper Details
                </h2>
              </div>

              {connectedResults.length === 0 ? (
                <div className="p-8 text-center text-gray-500 dark:text-gray-400">
                  No connected papers found.
                </div>
              ) : (
                <ul className="divide-y divide-gray-200 dark:divide-gray-700 overflow-y-auto flex-1">
                  {connectedResults.map((result, index) => {
                    const paperUrl = buildPaperUrl({
                      url: result.url,
                      arxiv_id: result.arxiv_id,
                      doi: result.doi,
                    });
                    const offsetIndex = index + 100;
                    return renderResultCard(
                      offsetIndex,
                      result.title,
                      paperUrl || null,
                      result.authors,
                      result.year,
                      result.abstract,
                      result.cited_by,
                      paperUrl || null,
                      () => handleAddFromRelated(offsetIndex, result),
                      () => handleConnectFromRelated(offsetIndex, result),
                      index,
                    );
                  })}
                </ul>
              )}
            </div>
          </div>
        </div>
      ) : (
        /* Layout without graph: Normal full-width Scholar results */
        hasSearched && !searching && !error && (
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
                    () => handleAddFromScholar(index, result),
                    () => handleConnectFromScholar(index, result),
                  )
                )}
              </ul>
            )}
          </div>
        )
      )}
    </div>
  );
}
