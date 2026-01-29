export type Category = 'recsys' | 'ml' | 'nlp' | 'cv' | 'rl' | 'other';

export interface Tag {
  id: string;
  name: string;
}

export interface TagWithCount extends Tag {
  paper_count: number;
}

export interface Paper {
  id: string;
  title: string;
  authors: string[];
  abstract: string;
  year: number;
  arxiv_id: string | null;
  arxiv_url: string | null;
  doi: string | null;
  paper_url: string | null;
  category: Category;
  tags: Tag[];
  published_at: string | null;
  created_at: string;
  updated_at: string;
}

export interface PaperListResponse {
  items: Paper[];
  total: number;
  page: number;
  limit: number;
  pages: number;
}

export interface PaperCreate {
  title: string;
  authors: string[];
  abstract: string;
  year: number;
  category: Category;
  tags: string[];
}

export interface ArxivImportRequest {
  arxiv_url: string;
  category: Category;
  tags: string[];
}

export interface DoiImportRequest {
  url: string;
  category: Category;
  tags: string[];
  title?: string;
  abstract?: string;
}

export interface PaperUpdate {
  title?: string;
  authors?: string[];
  abstract?: string;
  year?: number;
  category?: Category;
  tags?: string[];
}

export interface PaperFilters {
  search?: string;
  category?: Category;
  tags?: string;
  year?: number;
  page?: number;
  limit?: number;
}

export const CATEGORIES: { value: Category; label: string }[] = [
  { value: 'recsys', label: 'RecSys' },
  { value: 'ml', label: 'ML' },
  { value: 'nlp', label: 'NLP' },
  { value: 'cv', label: 'CV' },
  { value: 'rl', label: 'RL' },
  { value: 'other', label: 'Other' },
];
