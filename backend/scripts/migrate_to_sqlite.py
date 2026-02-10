#!/usr/bin/env python3
"""
Migration script: JSON (papers.json) -> SQLite (papers.db)

Usage:
    cd backend
    python scripts/migrate_to_sqlite.py
"""
import json
import shutil
import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.db.connection import get_db, init_db, DB_PATH

DATA_DIR = Path(__file__).parent.parent / "data"
JSON_FILE = DATA_DIR / "papers.json"
BACKUP_FILE = DATA_DIR / "papers.json.backup"


def load_json_data() -> dict:
    """Load data from JSON file."""
    if not JSON_FILE.exists():
        print(f"Error: {JSON_FILE} not found")
        sys.exit(1)

    with open(JSON_FILE) as f:
        return json.load(f)


def migrate():
    """Run migration from JSON to SQLite."""
    print("=" * 50)
    print("Paper Curation: JSON -> SQLite Migration")
    print("=" * 50)

    # Check if DB already exists
    if DB_PATH.exists():
        response = input(f"\nDatabase {DB_PATH} already exists. Overwrite? [y/N]: ")
        if response.lower() != "y":
            print("Aborted.")
            return
        DB_PATH.unlink()
        print(f"Removed existing database: {DB_PATH}")

    # Load JSON data
    print(f"\nLoading data from {JSON_FILE}...")
    data = load_json_data()
    papers = data.get("papers", [])
    tags = data.get("tags", [])
    print(f"  Found {len(papers)} papers and {len(tags)} tags")

    # Initialize database schema
    print(f"\nInitializing database at {DB_PATH}...")
    init_db()
    print("  Schema created successfully")

    # Migrate tags first
    print("\nMigrating tags...")
    with get_db() as conn:
        for tag in tags:
            conn.execute(
                "INSERT OR IGNORE INTO tags (id, name) VALUES (?, ?)",
                (tag["id"], tag["name"])
            )
    print(f"  Migrated {len(tags)} tags")

    # Migrate papers
    print("\nMigrating papers...")
    migrated = 0
    errors = 0

    with get_db() as conn:
        for paper in papers:
            try:
                # Extract tags from paper
                paper_tags = paper.pop("tags", [])

                # Handle summary object
                summary = paper.pop("summary", None)
                summary_one_line = summary.get("one_line") if summary else None
                summary_contribution = summary.get("contribution") if summary else None
                summary_methodology = summary.get("methodology") if summary else None
                summary_results = summary.get("results") if summary else None

                # Serialize JSON fields
                authors_json = json.dumps(paper.get("authors", []))
                translation_json = json.dumps(paper.get("translation")) if paper.get("translation") else None

                # Insert paper
                conn.execute("""
                    INSERT INTO papers (
                        id, title, authors, abstract, year, arxiv_id, arxiv_url,
                        doi, paper_url, conference, category, published_at, pdf_path,
                        summary_one_line, summary_contribution, summary_methodology, summary_results,
                        full_summary, translation, full_translation, created_at, updated_at
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    paper["id"],
                    paper["title"],
                    authors_json,
                    paper.get("abstract"),
                    paper.get("year"),
                    paper.get("arxiv_id"),
                    paper.get("arxiv_url"),
                    paper.get("doi"),
                    paper.get("paper_url"),
                    paper.get("conference"),
                    paper.get("category", "other"),
                    paper.get("published_at"),
                    paper.get("pdf_path"),
                    summary_one_line,
                    summary_contribution,
                    summary_methodology,
                    summary_results,
                    paper.get("full_summary"),
                    translation_json,
                    paper.get("full_translation"),
                    paper.get("created_at"),
                    paper.get("updated_at"),
                ))

                # Link paper to tags
                for tag in paper_tags:
                    # Ensure tag exists
                    conn.execute(
                        "INSERT OR IGNORE INTO tags (id, name) VALUES (?, ?)",
                        (tag["id"], tag["name"])
                    )
                    conn.execute(
                        "INSERT OR IGNORE INTO paper_tags (paper_id, tag_id) VALUES (?, ?)",
                        (paper["id"], tag["id"])
                    )

                migrated += 1

            except Exception as e:
                print(f"  Error migrating paper '{paper.get('title', 'unknown')}': {e}")
                errors += 1

    print(f"  Migrated {migrated} papers ({errors} errors)")

    # Verify migration
    print("\nVerifying migration...")
    with get_db() as conn:
        cursor = conn.execute("SELECT COUNT(*) as cnt FROM papers")
        db_papers = cursor.fetchone()["cnt"]
        cursor = conn.execute("SELECT COUNT(*) as cnt FROM tags")
        db_tags = cursor.fetchone()["cnt"]
        cursor = conn.execute("SELECT COUNT(*) as cnt FROM paper_tags")
        db_links = cursor.fetchone()["cnt"]

    print(f"  Database contains: {db_papers} papers, {db_tags} tags, {db_links} paper-tag links")

    # Backup JSON file
    if migrated > 0:
        print(f"\nBacking up JSON file to {BACKUP_FILE}...")
        shutil.copy2(JSON_FILE, BACKUP_FILE)
        print("  Backup created")

    print("\n" + "=" * 50)
    print("Migration completed successfully!")
    print("=" * 50)
    print(f"\nDatabase: {DB_PATH}")
    print(f"Backup:   {BACKUP_FILE}")
    print("\nYou can now start the server. The old papers.json is kept as backup.")


if __name__ == "__main__":
    migrate()
