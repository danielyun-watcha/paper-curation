'use client';

import { useEffect, useState, useCallback } from 'react';
import { Paper, PaperFilters, Category, TagWithCount } from '@/types';
import { papersApi, tagsApi } from '@/lib/api';
import { PaperCard } from '@/components/papers/PaperCard';
import { SearchBar } from '@/components/filters/SearchBar';
import { CategoryFilter } from '@/components/filters/CategoryFilter';
import { TagFilter } from '@/components/filters/TagFilter';
import { Pagination } from '@/components/ui/Pagination';

export default function HomePage() {
  const [papers, setPapers] = useState<Paper[]>([]);
  const [tags, setTags] = useState<TagWithCount[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const [filters, setFilters] = useState<PaperFilters>({
    page: 1,
    limit: 12,
  });
  const [totalPages, setTotalPages] = useState(0);
  const [selectedTags, setSelectedTags] = useState<string[]>([]);

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

  useEffect(() => {
    fetchPapers();
  }, [fetchPapers]);

  useEffect(() => {
    fetchTags();
  }, [fetchTags]);

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

  const handlePageChange = (page: number) => {
    setFilters((prev) => ({ ...prev, page }));
    window.scrollTo({ top: 0, behavior: 'smooth' });
  };

  const handleTagClick = (tagName: string) => {
    if (!selectedTags.includes(tagName)) {
      handleTagsChange([...selectedTags, tagName]);
    }
  };

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
        </div>
      </div>

      {error && (
        <div className="p-4 bg-red-100 text-red-700 rounded-md">{error}</div>
      )}

      {loading ? (
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
            {papers.map((paper) => (
              <PaperCard
                key={paper.id}
                paper={paper}
                onTagClick={handleTagClick}
              />
            ))}
          </div>

          <Pagination
            currentPage={filters.page || 1}
            totalPages={totalPages}
            onPageChange={handlePageChange}
          />
        </>
      )}
    </div>
  );
}
