export type Category = 'recsys' | 'ml' | 'nlp' | 'cv' | 'rl' | 'other';

export interface Tag {
  id: string;
  name: string;
}

export interface TagWithCount extends Tag {
  paper_count: number;
}

export interface PaperSummary {
  one_line: string | null;
  contribution: string | null;
  methodology: string | null;
  results: string | null;
}

export interface PaperTranslation {
  title: string;
  abstract: string;
}

export interface TranslationSection {
  name: string;
  original: string;
  translated: string;
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
  conference: string | null;
  category: Category;
  tags: Tag[];
  published_at: string | null;
  pdf_path: string | null;
  summary: PaperSummary | null;
  translation: PaperTranslation | null;
  full_translation: TranslationSection[] | null;
  full_summary: string | null;
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

export interface BulkImportRequest {
  urls: string[];
  category?: Category;
}

export interface PreviewImportRequest {
  urls: string[];
}

export interface PreviewItem {
  url: string;
  title: string | null;
  category: Category;
  error: string | null;
}

export interface PreviewImportResponse {
  previews: PreviewItem[];
}

export interface BulkImportWithCategoriesRequest {
  items: { url: string; category: Category }[];
}

export interface BulkImportResultItem {
  url: string;
  success: boolean;
  title?: string;
  error?: string;
}

export interface BulkImportResponse {
  total: number;
  successful: number;
  failed: number;
  results: BulkImportResultItem[];
}

export interface TranslationResponse {
  paper_id: string;
  original_title: string;
  original_abstract: string;
  translated_title: string;
  translated_abstract: string;
}

export const CATEGORIES: { value: Category; label: string }[] = [
  { value: 'recsys', label: 'RecSys' },
  { value: 'ml', label: 'ML' },
  { value: 'nlp', label: 'NLP' },
  { value: 'cv', label: 'CV' },
  { value: 'rl', label: 'RL' },
  { value: 'other', label: 'Other' },
];

export interface ScholarSearchResult {
  title: string;
  authors: string[];
  abstract: string | null;
  year: number | null;
  url: string | null;
  cited_by: number;
  pub_url: string | null;
}

export interface ScholarSearchResponse {
  query: string;
  results: ScholarSearchResult[];
}

export interface ScholarAddRequest {
  title: string;
  authors: string[];
  abstract?: string;
  year?: number;
  url?: string;
  category: Category;
}

export interface RelatedPaperResult {
  title: string;
  authors: string[];
  abstract: string | null;
  year: number | null;
  url: string | null;
  cited_by: number;
  arxiv_id: string | null;
  doi: string | null;
}

export interface RelatedPapersResponse {
  paper_id: string;
  paper_title: string;
  results: RelatedPaperResult[];
}
