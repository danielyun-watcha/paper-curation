'use client';

import { useState, useCallback } from 'react';
import { ScholarSearchResult, RelatedPaperResult } from '@/types';
import { papersApi } from '@/lib/api';
import { buildPaperUrl } from '@/lib/extractors';

interface UseAddPaperReturn {
  addingIndex: number | null;
  addedIndices: Set<number>;
  handleAddFromScholar: (index: number, result: ScholarSearchResult) => Promise<void>;
  handleAddFromRelated: (index: number, result: RelatedPaperResult) => Promise<void>;
  resetAddedIndices: () => void;
  isAdded: (index: number) => boolean;
  isAdding: (index: number) => boolean;
}

/**
 * Custom hook for adding papers from search/connected results
 */
export function useAddPaper(): UseAddPaperReturn {
  const [addingIndex, setAddingIndex] = useState<number | null>(null);
  const [addedIndices, setAddedIndices] = useState<Set<number>>(new Set());

  const handleAddFromScholar = useCallback(
    async (index: number, result: ScholarSearchResult) => {
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
        setAddedIndices((prev) => new Set(prev).add(index));
      } catch (err) {
        alert(err instanceof Error ? err.message : 'Failed to add paper');
      } finally {
        setAddingIndex(null);
      }
    },
    []
  );

  const handleAddFromRelated = useCallback(
    async (index: number, result: RelatedPaperResult) => {
      setAddingIndex(index);
      try {
        const url = buildPaperUrl({
          url: result.url,
          arxiv_id: result.arxiv_id,
          doi: result.doi,
        });

        await papersApi.addFromScholar({
          title: result.title,
          authors: result.authors,
          abstract: result.abstract || undefined,
          year: result.year || undefined,
          url: url,
          category: 'other',
        });
        setAddedIndices((prev) => new Set(prev).add(index));
      } catch (err) {
        alert(err instanceof Error ? err.message : 'Failed to add paper');
      } finally {
        setAddingIndex(null);
      }
    },
    []
  );

  const resetAddedIndices = useCallback(() => {
    setAddedIndices(new Set());
  }, []);

  const isAdded = useCallback(
    (index: number) => addedIndices.has(index),
    [addedIndices]
  );

  const isAdding = useCallback(
    (index: number) => addingIndex === index,
    [addingIndex]
  );

  return {
    addingIndex,
    addedIndices,
    handleAddFromScholar,
    handleAddFromRelated,
    resetAddedIndices,
    isAdded,
    isAdding,
  };
}
