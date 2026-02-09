/**
 * Application-wide constants
 */

// =============================================================================
// Graph Visualization (ConnectedPapersGraph)
// =============================================================================

export const GRAPH_LAYOUT = {
  /** Ratio of node arrangement radius to container size */
  RADIUS_RATIO: 0.17,
  /** Default container dimensions */
  DEFAULT_WIDTH: 500,
  DEFAULT_HEIGHT: 450,
  /** Retry delays for dimension calculation (ms) */
  DIMENSION_RETRY_DELAYS: [100, 300],
} as const;

export const GRAPH_NODE = {
  /** Center node size */
  CENTER_SIZE: 10,
  /** Peripheral node size range */
  MIN_SIZE: 4,
  MAX_SIZE: 9,
  /** Assumed maximum citations for size scaling */
  MAX_CITATIONS_FOR_SCALE: 5000,
  /** Glow radius offset for center node */
  CENTER_GLOW_OFFSET: 3,
} as const;

export const GRAPH_COLORS = {
  /** Center node color (purple) */
  CENTER: '#a855f7',
  /** Unknown year fallback color */
  UNKNOWN_YEAR: '#94a3b8',
  /** Center node border color (gold) */
  CENTER_BORDER: '#fbbf24',
  /** Center node glow color */
  CENTER_GLOW: 'rgba(168, 85, 247, 0.3)',
  /** Regular node border color */
  NODE_BORDER: 'rgba(255, 255, 255, 0.6)',
  /** Year-based gradient settings */
  YEAR_GRADIENT: {
    /** Minimum year for color scale */
    MIN_YEAR: 2019,
    /** HSL settings: Old papers (cyan) → New papers (purple) */
    HUE_START: 180,      // Cyan
    HUE_END: 270,        // Purple
    SATURATION_START: 45,
    SATURATION_END: 95,
    LIGHTNESS_START: 85, // Light (old)
    LIGHTNESS_END: 15,   // Dark (new)
  },
} as const;

export const GRAPH_LINKS = {
  /** Cross-link (paper-to-paper) settings */
  CROSS: {
    OPACITY_MIN: 0.2,
    OPACITY_MAX: 0.7,
    WIDTH_MIN: 0.8,
    WIDTH_MAX: 2.0,
    COLOR_BASE: 'rgb(120, 140, 170)',
  },
  /** Center-link (center-to-paper) settings */
  CENTER: {
    OPACITY_MIN: 0.3,
    OPACITY_MAX: 0.8,
    WIDTH_MIN: 1.0,
    WIDTH_MAX: 2.5,
    COLOR_BASE: 'rgb(160, 170, 190)',
  },
  /** Similarity thresholds for cross-links */
  SIMILARITY: {
    MAX_CITATION_DIFF: 150,
    MAX_YEAR_DIFF: 2,
    CITATION_NORM_DIVISOR: 150,
    YEAR_NORM_DIVISOR: 5,
  },
} as const;

export const GRAPH_SHADOW = {
  COLOR: 'rgba(0, 0, 0, 0.3)',
  BLUR: 8,
  OFFSET_X: 2,
  OFFSET_Y: 2,
} as const;

// =============================================================================
// Search Page
// =============================================================================

export const SEARCH_CONFIG = {
  /** Index offset for connected paper results (to avoid collision with scholar results) */
  CONNECTED_RESULTS_INDEX_OFFSET: 100,
  /** Default search result limit */
  DEFAULT_LIMIT: 5,
} as const;

// =============================================================================
// UI Settings
// =============================================================================

export const UI_CONFIG = {
  /** Debounce delay for search input (ms) */
  SEARCH_DEBOUNCE_MS: 300,
  /** Default pagination limit */
  DEFAULT_PAGE_LIMIT: 12,
} as const;
