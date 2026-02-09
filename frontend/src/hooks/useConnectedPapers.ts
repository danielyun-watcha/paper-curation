'use client';

import { useState, useCallback, useEffect } from 'react';
import { RelatedPaperResult, ScholarSearchResult } from '@/types';
import { papersApi } from '@/lib/api';
import { extractArxivId, extractDoi } from '@/lib/extractors';

interface ConnectParams {
  arxiv_id?: string;
  doi?: string;
  title?: string;
  year?: number;
  citations?: number;
}

interface UseConnectedPapersReturn {
  connectedResults: RelatedPaperResult[];
  sourceTitle: string;
  sourceYear: number | undefined;
  sourceCitations: number;
  hasConnected: boolean;
  connectingIndex: number | null;
  handleConnect: (index: number, params: ConnectParams) => Promise<void>;
  handleConnectFromScholar: (index: number, result: ScholarSearchResult) => void;
  handleConnectFromRelated: (index: number, result: RelatedPaperResult) => void;
  handleConnectById: (paperId: string) => Promise<void>;
  clearConnected: () => void;
}

/**
 * Custom hook for Connected Papers functionality
 */
export function useConnectedPapers(
  onConnectStart?: () => void
): UseConnectedPapersReturn {
  const [connectedResults, setConnectedResults] = useState<RelatedPaperResult[]>([]);
  const [sourceTitle, setSourceTitle] = useState('');
  const [sourceYear, setSourceYear] = useState<number | undefined>(undefined);
  const [sourceCitations, setSourceCitations] = useState(0);
  const [hasConnected, setHasConnected] = useState(false);
  const [connectingIndex, setConnectingIndex] = useState<number | null>(null);

  const handleConnect = useCallback(
    async (index: number, params: ConnectParams) => {
      setConnectingIndex(index);
      onConnectStart?.();

      try {
        const response = await papersApi.getRelatedPapersExternal({
          arxiv_id: params.arxiv_id || undefined,
          doi: params.doi || undefined,
          title: !params.arxiv_id && !params.doi ? params.title : undefined,
        });

        setConnectedResults(response.results);
        setSourceTitle(params.title || '');
        setSourceYear(params.year);
        setSourceCitations(params.citations || 0);
        setHasConnected(true);
      } catch (err) {
        alert(err instanceof Error ? err.message : 'Failed to find connected papers');
      } finally {
        setConnectingIndex(null);
      }
    },
    [onConnectStart]
  );

  const handleConnectFromScholar = useCallback(
    (index: number, result: ScholarSearchResult) => {
      const arxivId = extractArxivId(result.url || '') || extractArxivId(result.pub_url || '');
      const doi = extractDoi(result.url || '') || extractDoi(result.pub_url || '');

      handleConnect(index, {
        arxiv_id: arxivId || undefined,
        doi: doi || undefined,
        title: result.title,
        year: result.year || undefined,
        citations: result.cited_by,
      });
    },
    [handleConnect]
  );

  const handleConnectFromRelated = useCallback(
    (index: number, result: RelatedPaperResult) => {
      handleConnect(index, {
        arxiv_id: result.arxiv_id || undefined,
        doi: result.doi || undefined,
        title: result.title,
        year: result.year || undefined,
        citations: result.cited_by,
      });
    },
    [handleConnect]
  );

  const clearConnected = useCallback(() => {
    setConnectedResults([]);
    setSourceTitle('');
    setSourceYear(undefined);
    setSourceCitations(0);
    setHasConnected(false);
  }, []);

  const handleConnectById = useCallback(
    async (paperId: string) => {
      try {
        const response = await papersApi.getRelatedPapers(paperId);
        setConnectedResults(response.results);
        setSourceTitle(response.paper_title);
        setHasConnected(true);
      } catch (err) {
        console.error('Auto-connect failed:', err);
      }
    },
    []
  );

  return {
    connectedResults,
    sourceTitle,
    sourceYear,
    sourceCitations,
    hasConnected,
    connectingIndex,
    handleConnect,
    handleConnectFromScholar,
    handleConnectFromRelated,
    handleConnectById,
    clearConnected,
  };
}

/**
 * Hook for auto-connecting from URL params
 */
export function useAutoConnect(
  connectId: string | null,
  setConnectedResults: (results: RelatedPaperResult[]) => void,
  setSourceTitle: (title: string) => void,
  setHasConnected: (connected: boolean) => void
) {
  const [autoConnectDone, setAutoConnectDone] = useState(false);

  useEffect(() => {
    if (connectId && !autoConnectDone) {
      setAutoConnectDone(true);
      papersApi
        .getRelatedPapers(connectId)
        .then((response) => {
          setConnectedResults(response.results);
          setSourceTitle(response.paper_title);
          setHasConnected(true);
        })
        .catch((err) => {
          console.error('Auto-connect failed:', err);
        });
    }
  }, [connectId, autoConnectDone, setConnectedResults, setSourceTitle, setHasConnected]);
}
