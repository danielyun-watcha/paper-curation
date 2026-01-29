'use client';

import { useState, useEffect, useCallback } from 'react';

const FAVORITES_KEY = 'paper-favorites';

export function useFavorites() {
  const [favorites, setFavorites] = useState<Set<string>>(new Set());
  const [isLoaded, setIsLoaded] = useState(false);

  // Load favorites from localStorage on mount
  useEffect(() => {
    const stored = localStorage.getItem(FAVORITES_KEY);
    if (stored) {
      try {
        const parsed = JSON.parse(stored);
        setFavorites(new Set(parsed));
      } catch {
        setFavorites(new Set());
      }
    }
    setIsLoaded(true);
  }, []);

  // Save to localStorage whenever favorites change
  useEffect(() => {
    if (isLoaded) {
      localStorage.setItem(FAVORITES_KEY, JSON.stringify([...favorites]));
    }
  }, [favorites, isLoaded]);

  const isFavorite = useCallback(
    (paperId: string) => favorites.has(paperId),
    [favorites]
  );

  const toggleFavorite = useCallback((paperId: string) => {
    setFavorites((prev) => {
      const next = new Set(prev);
      if (next.has(paperId)) {
        next.delete(paperId);
      } else {
        next.add(paperId);
      }
      return next;
    });
  }, []);

  const getFavoriteIds = useCallback(() => [...favorites], [favorites]);

  return {
    isFavorite,
    toggleFavorite,
    getFavoriteIds,
    isLoaded,
  };
}
