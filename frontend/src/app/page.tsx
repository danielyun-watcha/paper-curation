'use client';

import { useEffect, useState, useCallback, useMemo } from 'react';
import { Paper, PaperFilters, Category, TagWithCount } from '@/types';
import { papersApi, tagsApi } from '@/lib/api';
import { PaperCard } from '@/components/papers/PaperCard';
import { SearchBar } from '@/components/filters/SearchBar';
import { CategoryFilter } from '@/components/filters/CategoryFilter';
import { TagFilter } from '@/components/filters/TagFilter';
import { Pagination } from '@/components/ui/Pagination';
import { useReadingStatus, ReadingStatus, READING_STATUS_LABELS } from '@/hooks/useReadingStatus';

export default function HomePage() {
  const [papers, setPapers] = useState<Paper[]>([]);
  const [tags, setTags] = useState<TagWithCount[]>([]);
  const [years, setYears] = useState<number[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const [filters, setFilters] = useState<PaperFilters>({
    page: 1,
    limit: 12,
  });
  const [totalPages, setTotalPages] = useState(0);
  const [selectedTags, setSelectedTags] = useState<string[]>([]);
  const [statusFilter, setStatusFilter] = useState<ReadingStatus | 'all'>('all');
  const [sortBy, setSortBy] = useState<string>('updated_desc');

  const { getStatus, setStatus, isFavorite, toggleFavorite, isLoaded } = useReadingStatus();

  const fetchPapers = useCallback(async () => {
    try {
      setLoading(true);
      const tagsParam = selectedTags.length > 0 ? selectedTags.join(',') : undefined;
      const response = await papersApi.list({ ...filters, tags: tagsParam });
      setPapers(response.items);
      setTotalPages(response.pages);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to fetch papers');
    } finally {
      setLoading(false);
    }
  }, [filters, selectedTags]);

  const fetchTags = useCallback(async () => {
    try {
      const response = await tagsApi.list();
      setTags(response);
    } catch (err) {
      console.error('Failed to fetch tags:', err);
    }
  }, []);

  const fetchYears = useCallback(async () => {
    try {
      const response = await papersApi.getYears();
      setYears(response);
    } catch (err) {
      console.error('Failed to fetch years:', err);
    }
  }, []);

  useEffect(() => {
    fetchPapers();
  }, [fetchPapers]);

  useEffect(() => {
    fetchTags();
  }, [fetchTags]);

  useEffect(() => {
    fetchYears();
  }, [fetchYears]);

  const handleSearchChange = (search: string) => {
    setFilters((prev) => ({ ...prev, search: search || undefined, page: 1 }));
  };

  const handleCategoryChange = (category: Category | undefined) => {
    setFilters((prev) => ({ ...prev, category, page: 1 }));
  };

  const handleTagsChange = (tags: string[]) => {
    setSelectedTags(tags);
    setFilters((prev) => ({ ...prev, page: 1 }));
  };

  const handleYearChange = (year: number | undefined) => {
    setFilters((prev) => ({ ...prev, year, page: 1 }));
  };

  const handlePageChange = (page: number) => {
    setFilters((prev) => ({ ...prev, page }));
    window.scrollTo({ top: 0, behavior: 'smooth' });
  };

  const handleTagClick = (tagName: string) => {
    if (!selectedTags.includes(tagName)) {
      handleTagsChange([...selectedTags, tagName]);
    }
  };

  const sortedPapers = useMemo(() => {
    const sorted = [...papers];
    switch (sortBy) {
      case 'published_desc':
        return sorted.sort((a, b) =>
          (b.published_at || '').localeCompare(a.published_at || '')
        );
      case 'published_asc':
        return sorted.sort((a, b) =>
          (a.published_at || '').localeCompare(b.published_at || '')
        );
      case 'updated_desc':
        return sorted.sort((a, b) =>
          b.updated_at.localeCompare(a.updated_at)
        );
      case 'updated_asc':
        return sorted.sort((a, b) =>
          a.updated_at.localeCompare(b.updated_at)
        );
      case 'title_asc':
        return sorted.sort((a, b) =>
          a.title.localeCompare(b.title)
        );
      default:
        return sorted;
    }
  }, [papers, sortBy]);

  return (
    <div className="space-y-6">
      <div className="bg-white dark:bg-gray-800 rounded-lg shadow-md p-6">
        <div className="space-y-4">
          <SearchBar
            value={filters.search || ''}
            onChange={handleSearchChange}
            placeholder="Search by title or abstract..."
          />

          <div>
            <h3 className="text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
              Category
            </h3>
            <CategoryFilter
              value={filters.category}
              onChange={handleCategoryChange}
            />
          </div>

          {tags.length > 0 && (
            <div>
              <h3 className="text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                Tags
              </h3>
              <TagFilter
                tags={tags}
                selectedTags={selectedTags}
                onChange={handleTagsChange}
              />
            </div>
          )}

          <div className="flex items-center gap-3 pt-2 border-t border-gray-200 dark:border-gray-700">
            <select
              value={statusFilter}
              onChange={(e) => setStatusFilter(e.target.value as ReadingStatus | 'all')}
              className="px-3 py-1.5 text-sm border border-gray-300 dark:border-gray-600 rounded-md bg-white dark:bg-gray-700 text-gray-700 dark:text-gray-300 focus:outline-none focus:ring-2 focus:ring-blue-500"
            >
              <option value="all">All Status</option>
              <option value="favorite">⭐ {READING_STATUS_LABELS.favorite}</option>
              <option value="to_read">📋 {READING_STATUS_LABELS.to_read}</option>
              <option value="read">✅ {READING_STATUS_LABELS.read}</option>
            </select>

            <select
              value={filters.year || ''}
              onChange={(e) => handleYearChange(e.target.value ? Number(e.target.value) : undefined)}
              className="px-3 py-1.5 text-sm border border-gray-300 dark:border-gray-600 rounded-md bg-white dark:bg-gray-700 text-gray-700 dark:text-gray-300 focus:outline-none focus:ring-2 focus:ring-blue-500"
            >
              <option value="">All Years</option>
              {years.map((year) => (
                <option key={year} value={year}>
                  {year}
                </option>
              ))}
            </select>

            <select
              value={sortBy}
              onChange={(e) => setSortBy(e.target.value)}
              className="px-3 py-1.5 text-sm border border-gray-300 dark:border-gray-600 rounded-md bg-white dark:bg-gray-700 text-gray-700 dark:text-gray-300 focus:outline-none focus:ring-2 focus:ring-blue-500"
            >
              <option value="updated_desc">Updated (Newest)</option>
              <option value="updated_asc">Updated (Oldest)</option>
              <option value="published_desc">Published (Newest)</option>
              <option value="published_asc">Published (Oldest)</option>
              <option value="title_asc">Title (A-Z)</option>
            </select>
          </div>
        </div>
      </div>

      {error && (
        <div className="p-4 bg-red-100 text-red-700 rounded-md">{error}</div>
      )}

      {loading || !isLoaded ? (
        <div className="text-center py-12">
          <p className="text-gray-500 dark:text-gray-400">Loading papers...</p>
        </div>
      ) : papers.length === 0 ? (
        <div className="text-center py-12">
          <p className="text-gray-500 dark:text-gray-400">No papers found</p>
        </div>
      ) : (
        <>
          <div className="grid gap-6 md:grid-cols-2 lg:grid-cols-3">
            {sortedPapers
              .filter((paper) => statusFilter === 'all' || getStatus(paper.id) === statusFilter)
              .map((paper) => (
                <PaperCard
                  key={paper.id}
                  paper={paper}
                  onTagClick={handleTagClick}
                  readingStatus={getStatus(paper.id)}
                  onStatusChange={(status) => setStatus(paper.id, status)}
                />
              ))}
          </div>

          {statusFilter === 'all' && (
            <Pagination
              currentPage={filters.page || 1}
              totalPages={totalPages}
              onPageChange={handlePageChange}
            />
          )}
        </>
      )}
    </div>
  );
}
