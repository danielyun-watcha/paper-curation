import {
  Paper,
  PaperListResponse,
  PaperCreate,
  PaperUpdate,
  ArxivImportRequest,
  DoiImportRequest,
  PaperFilters,
  TagWithCount,
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
