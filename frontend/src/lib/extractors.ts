/**
 * URL parsing utilities for extracting paper identifiers
 */

/**
 * Extract arXiv ID from URL
 * @example extractArxivId('https://arxiv.org/abs/2301.12345') => '2301.12345'
 */
export function extractArxivId(url: string): string | null {
  if (!url) return null;
  const match = url.match(/arxiv\.org\/(?:abs|pdf)\/([\d.]+)/);
  return match ? match[1] : null;
}

/**
 * Extract DOI from URL
 * @example extractDoi('https://doi.org/10.1145/1234567') => '10.1145/1234567'
 */
export function extractDoi(url: string): string | null {
  if (!url) return null;
  const match = url.match(/doi\.org\/(.+)/);
  return match ? match[1] : null;
}

/**
 * Build paper URL from available identifiers
 */
export function buildPaperUrl(params: {
  url?: string | null;
  arxiv_id?: string | null;
  doi?: string | null;
}): string | undefined {
  if (params.url) return params.url;
  if (params.arxiv_id) return `https://arxiv.org/abs/${params.arxiv_id}`;
  if (params.doi) return `https://doi.org/${params.doi}`;
  return undefined;
}
