import {
  Paper,
  PaperListResponse,
  PaperCreate,
  PaperUpdate,
  ArxivImportRequest,
  DoiImportRequest,
  PaperFilters,
  TagWithCount,
  BulkImportRequest,
  BulkImportResponse,
  PaperSummary,
  TranslationResponse,
  PreviewImportRequest,
  PreviewImportResponse,
  BulkImportWithCategoriesRequest,
  ScholarSearchResponse,
  ScholarAddRequest,
  RelatedPapersResponse,
} from '@/types';

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

class ApiError extends Error {
  constructor(public status: number, message: string) {
    super(message);
    this.name = 'ApiError';
  }
}

async function fetchApi<T>(
  endpoint: string,
  options: RequestInit = {}
): Promise<T> {
  const url = `${API_BASE_URL}${endpoint}`;

  const response = await fetch(url, {
    ...options,
    headers: {
      'Content-Type': 'application/json',
      ...options.headers,
    },
  });

  if (!response.ok) {
    const error = await response.json().catch(() => ({ detail: 'Unknown error' }));
    throw new ApiError(response.status, error.detail || 'Request failed');
  }

  return response.json();
}

// Papers API
export const papersApi = {
  list: async (filters: PaperFilters = {}): Promise<PaperListResponse> => {
    const params = new URLSearchParams();

    if (filters.search) params.set('search', filters.search);
    if (filters.category) params.set('category', filters.category);
    if (filters.tags) params.set('tags', filters.tags);
    if (filters.year) params.set('year', String(filters.year));
    if (filters.page) params.set('page', String(filters.page));
    if (filters.limit) params.set('limit', String(filters.limit));

    const query = params.toString();
    return fetchApi<PaperListResponse>(`/api/papers${query ? `?${query}` : ''}`);
  },

  get: async (id: string): Promise<Paper> => {
    return fetchApi<Paper>(`/api/papers/${id}`);
  },

  create: async (data: PaperCreate): Promise<Paper> => {
    return fetchApi<Paper>('/api/papers', {
      method: 'POST',
      body: JSON.stringify(data),
    });
  },

  importFromArxiv: async (data: ArxivImportRequest): Promise<Paper> => {
    return fetchApi<Paper>('/api/papers/arxiv', {
      method: 'POST',
      body: JSON.stringify(data),
    });
  },

  importFromDoi: async (data: DoiImportRequest): Promise<Paper> => {
    return fetchApi<Paper>('/api/papers/doi', {
      method: 'POST',
      body: JSON.stringify(data),
    });
  },

  update: async (id: string, data: PaperUpdate): Promise<Paper> => {
    return fetchApi<Paper>(`/api/papers/${id}`, {
      method: 'PUT',
      body: JSON.stringify(data),
    });
  },

  delete: async (id: string): Promise<void> => {
    await fetchApi(`/api/papers/${id}`, {
      method: 'DELETE',
    });
  },

  getYears: async (): Promise<number[]> => {
    return fetchApi<number[]>('/api/papers/years');
  },

  bulkImport: async (data: BulkImportRequest): Promise<BulkImportResponse> => {
    return fetchApi<BulkImportResponse>('/api/papers/bulk', {
      method: 'POST',
      body: JSON.stringify(data),
    });
  },

  previewImport: async (data: PreviewImportRequest): Promise<PreviewImportResponse> => {
    return fetchApi<PreviewImportResponse>('/api/papers/preview', {
      method: 'POST',
      body: JSON.stringify(data),
    });
  },

  bulkImportWithCategories: async (data: BulkImportWithCategoriesRequest): Promise<BulkImportResponse> => {
    return fetchApi<BulkImportResponse>('/api/papers/bulk-with-categories', {
      method: 'POST',
      body: JSON.stringify(data),
    });
  },

  generateSummary: async (id: string): Promise<PaperSummary> => {
    return fetchApi<PaperSummary>(`/api/papers/${id}/summary`, {
      method: 'POST',
    });
  },

  translate: async (id: string): Promise<TranslationResponse> => {
    return fetchApi<TranslationResponse>(`/api/papers/${id}/translate`, {
      method: 'POST',
    });
  },

  uploadPdf: async (
    pdf: File,
    data: {
      title: string;
      authors: string;
      abstract: string;
      year: number;
      category: string;
      tags: string;
    }
  ): Promise<Paper> => {
    const formData = new FormData();
    formData.append('pdf', pdf);
    formData.append('title', data.title);
    formData.append('authors', data.authors);
    formData.append('abstract', data.abstract);
    formData.append('year', String(data.year));
    formData.append('category', data.category);
    formData.append('tags', data.tags);

    const url = `${API_BASE_URL}/api/papers/upload-pdf`;
    const response = await fetch(url, {
      method: 'POST',
      body: formData,
    });

    if (!response.ok) {
      const error = await response.json().catch(() => ({ detail: 'Unknown error' }));
      throw new ApiError(response.status, error.detail || 'Upload failed');
    }

    return response.json();
  },

  searchScholar: async (query: string, limit: number = 5): Promise<ScholarSearchResponse> => {
    const params = new URLSearchParams();
    params.set('query', query);
    params.set('limit', String(limit));

    return fetchApi<ScholarSearchResponse>(`/api/papers/search-scholar?${params.toString()}`);
  },

  addFromScholar: async (data: ScholarAddRequest): Promise<Paper> => {
    return fetchApi<Paper>('/api/papers/add-from-scholar', {
      method: 'POST',
      body: JSON.stringify(data),
    });
  },

  getRelatedPapers: async (paperId: string): Promise<RelatedPapersResponse> => {
    return fetchApi<RelatedPapersResponse>(`/api/papers/related/${paperId}`);
  },

  getRelatedPapersExternal: async (params: { arxiv_id?: string; doi?: string; title?: string }): Promise<RelatedPapersResponse> => {
    const searchParams = new URLSearchParams();
    if (params.arxiv_id) searchParams.set('arxiv_id', params.arxiv_id);
    if (params.doi) searchParams.set('doi', params.doi);
    if (params.title) searchParams.set('title', params.title);
    return fetchApi<RelatedPapersResponse>(`/api/papers/related-external?${searchParams.toString()}`);
  },
};

// Tags API
export const tagsApi = {
  list: async (): Promise<TagWithCount[]> => {
    return fetchApi<TagWithCount[]>('/api/tags');
  },

  create: async (name: string): Promise<{ id: string; name: string }> => {
    return fetchApi('/api/tags', {
      method: 'POST',
      body: JSON.stringify({ name }),
    });
  },

  delete: async (id: string): Promise<void> => {
    await fetchApi(`/api/tags/${id}`, {
      method: 'DELETE',
    });
  },
};

export { ApiError };
