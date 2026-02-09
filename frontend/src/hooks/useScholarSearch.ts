'use client';

import { useState, useCallback } from 'react';
import { ScholarSearchResult } from '@/types';
import { papersApi } from '@/lib/api';

interface UseScholarSearchReturn {
  query: string;
  setQuery: (query: string) => void;
  searching: boolean;
  results: ScholarSearchResult[];
  error: string | null;
  hasSearched: boolean;
  handleSearch: () => Promise<void>;
  handleKeyDown: (e: React.KeyboardEvent) => void;
  clearResults: () => void;
}

/**
 * Custom hook for Google Scholar search functionality
 */
export function useScholarSearch(
  onSearchStart?: () => void
): UseScholarSearchReturn {
  const [query, setQuery] = useState('');
  const [searching, setSearching] = useState(false);
  const [results, setResults] = useState<ScholarSearchResult[]>([]);
  const [error, setError] = useState<string | null>(null);
  const [hasSearched, setHasSearched] = useState(false);

  const handleSearch = useCallback(async () => {
    if (!query.trim()) return;

    setSearching(true);
    setError(null);
    setHasSearched(true);
    onSearchStart?.();

    try {
      const response = await papersApi.searchScholar(query.trim(), 5);
      setResults(response.results);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Search failed');
      setResults([]);
    } finally {
      setSearching(false);
    }
  }, [query, onSearchStart]);

  const handleKeyDown = useCallback(
    (e: React.KeyboardEvent) => {
      if (e.key === 'Enter' && !e.shiftKey) {
        e.preventDefault();
        handleSearch();
      }
    },
    [handleSearch]
  );

  const clearResults = useCallback(() => {
    setResults([]);
    setHasSearched(false);
    setError(null);
  }, []);

  return {
    query,
    setQuery,
    searching,
    results,
    error,
    hasSearched,
    handleSearch,
    handleKeyDown,
    clearResults,
  };
}
