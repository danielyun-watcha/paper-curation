'use client';

import { useState, useEffect, useCallback } from 'react';

export type ReadingStatus = 'none' | 'favorite' | 'to_read' | 'read';

export const READING_STATUS_LABELS: Record<ReadingStatus, string> = {
  none: '-',
  favorite: '즐겨찾기',
  to_read: '읽을 예정',
  read: '읽음',
};

export const READING_STATUS_ICONS: Record<ReadingStatus, string> = {
  none: '',
  favorite: '⭐',
  to_read: '📋',
  read: '✅',
};

const READING_STATUS_KEY = 'paper-reading-status';

interface ReadingStatusMap {
  [paperId: string]: ReadingStatus;
}

export function useReadingStatus() {
  const [statusMap, setStatusMap] = useState<ReadingStatusMap>({});
  const [isLoaded, setIsLoaded] = useState(false);

  // Load from localStorage on mount
  useEffect(() => {
    const stored = localStorage.getItem(READING_STATUS_KEY);
    if (stored) {
      try {
        const parsed = JSON.parse(stored);
        setStatusMap(parsed);
      } catch {
        setStatusMap({});
      }
    }
    setIsLoaded(true);
  }, []);

  // Save to localStorage whenever statusMap changes
  useEffect(() => {
    if (isLoaded) {
      localStorage.setItem(READING_STATUS_KEY, JSON.stringify(statusMap));
    }
  }, [statusMap, isLoaded]);

  const getStatus = useCallback(
    (paperId: string): ReadingStatus => statusMap[paperId] || 'none',
    [statusMap]
  );

  const setStatus = useCallback((paperId: string, status: ReadingStatus) => {
    setStatusMap((prev) => {
      const next = { ...prev };
      if (status === 'none') {
        delete next[paperId];
      } else {
        next[paperId] = status;
      }
      return next;
    });
  }, []);

  const cycleStatus = useCallback((paperId: string) => {
    const currentStatus = statusMap[paperId] || 'none';
    const order: ReadingStatus[] = ['none', 'favorite', 'to_read', 'read'];
    const currentIndex = order.indexOf(currentStatus);
    const nextStatus = order[(currentIndex + 1) % order.length];
    setStatus(paperId, nextStatus);
  }, [statusMap, setStatus]);

  // For backwards compatibility with useFavorites
  const isFavorite = useCallback(
    (paperId: string) => statusMap[paperId] === 'favorite',
    [statusMap]
  );

  const toggleFavorite = useCallback((paperId: string) => {
    const currentStatus = statusMap[paperId];
    if (currentStatus === 'favorite') {
      setStatus(paperId, 'none');
    } else {
      setStatus(paperId, 'favorite');
    }
  }, [statusMap, setStatus]);

  const getPaperIdsByStatus = useCallback(
    (status: ReadingStatus) =>
      Object.entries(statusMap)
        .filter(([, s]) => s === status)
        .map(([id]) => id),
    [statusMap]
  );

  return {
    getStatus,
    setStatus,
    cycleStatus,
    isFavorite,
    toggleFavorite,
    getPaperIdsByStatus,
    isLoaded,
  };
}
