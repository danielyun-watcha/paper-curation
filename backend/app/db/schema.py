"""SQLite schema definition"""

SCHEMA_SQL = """
-- Tags table
CREATE TABLE IF NOT EXISTS tags (
    id TEXT PRIMARY KEY,
    name TEXT NOT NULL UNIQUE COLLATE NOCASE
);

-- Papers table
CREATE TABLE IF NOT EXISTS papers (
    id TEXT PRIMARY KEY,
    title TEXT NOT NULL,
    authors TEXT NOT NULL,          -- JSON array
    abstract TEXT,
    year INTEGER,
    arxiv_id TEXT UNIQUE,
    arxiv_url TEXT,
    doi TEXT UNIQUE,
    paper_url TEXT,
    conference TEXT,
    category TEXT NOT NULL DEFAULT 'other',
    published_at TEXT,
    pdf_path TEXT,

    -- Summary fields (server storage)
    summary_one_line TEXT,
    summary_contribution TEXT,
    summary_methodology TEXT,
    summary_results TEXT,
    full_summary TEXT,

    -- Translation fields (JSON)
    translation TEXT,
    full_translation TEXT,

    -- Timestamps
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL
);

-- Paper-Tag relationship (many-to-many)
CREATE TABLE IF NOT EXISTS paper_tags (
    paper_id TEXT REFERENCES papers(id) ON DELETE CASCADE,
    tag_id TEXT REFERENCES tags(id) ON DELETE CASCADE,
    PRIMARY KEY (paper_id, tag_id)
);

-- Indexes for common queries
CREATE INDEX IF NOT EXISTS idx_papers_arxiv_id ON papers(arxiv_id);
CREATE INDEX IF NOT EXISTS idx_papers_doi ON papers(doi);
CREATE INDEX IF NOT EXISTS idx_papers_year ON papers(year);
CREATE INDEX IF NOT EXISTS idx_papers_category ON papers(category);
CREATE INDEX IF NOT EXISTS idx_papers_updated_at ON papers(updated_at DESC);
CREATE INDEX IF NOT EXISTS idx_paper_tags_paper_id ON paper_tags(paper_id);
CREATE INDEX IF NOT EXISTS idx_paper_tags_tag_id ON paper_tags(tag_id);

-- Metadata table for tracking updates
CREATE TABLE IF NOT EXISTS metadata (
    key TEXT PRIMARY KEY,
    value TEXT,
    updated_at TEXT DEFAULT CURRENT_TIMESTAMP
);
"""
