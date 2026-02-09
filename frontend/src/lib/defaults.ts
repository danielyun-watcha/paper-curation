/**
 * Application-wide default values
 */

// =============================================================================
// Paper Form Defaults
// =============================================================================

export const PAPER_FORM_DEFAULTS = {
  /** Default year for new papers */
  year: () => new Date().getFullYear(),
  /** Default category for new papers */
  category: 'other' as const,
  /** Default reading status for new papers */
  readingStatus: 'unread' as const,
  /** Default tags for new papers */
  tags: [] as string[],
} as const;

// =============================================================================
// Pagination Defaults
// =============================================================================

export const PAGINATION_DEFAULTS = {
  /** Default page number */
  page: 1,
  /** Default items per page for paper list */
  paperListLimit: 12,
  /** Limit for dropdown/selector lists */
  selectorLimit: 100,
} as const;

// =============================================================================
// Search Defaults
// =============================================================================

export const SEARCH_DEFAULTS = {
  /** Default Scholar search result limit */
  scholarLimit: 5,
  /** Default Connected Papers result limit */
  connectedPapersLimit: 10,
} as const;

// =============================================================================
// Highlight Defaults
// =============================================================================

export const HIGHLIGHT_DEFAULTS = {
  /** Default highlight color */
  color: 'yellow',
} as const;

// =============================================================================
// Placeholder Text
// =============================================================================

export const PLACEHOLDERS = {
  /** Search bar placeholder */
  search: 'Search papers...',
  /** Filter search placeholder */
  filterSearch: 'Search by title or abstract...',
  /** Tag input placeholder */
  tagInput: 'Add tag and press Enter',
  /** Authors input placeholder */
  authors: 'John Doe, Jane Smith',
  /** Abstract input placeholder */
  abstract: 'Paper abstract (optional)',
  /** Comment input placeholder */
  comment: 'Add a comment (optional)...',
  /** Scholar search placeholder */
  scholarSearch: "Paste a paper title, abstract, or describe the topic you're looking for...",
  /** PDF title placeholder */
  pdfTitle: 'Leave empty to auto-extract from PDF',
  /** arXiv URL example */
  arxivUrl: 'https://arxiv.org/abs/2402.17152',
} as const;
