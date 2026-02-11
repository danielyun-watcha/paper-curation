"""Migrate papers from JSON to SQLite"""
import json
import sqlite3
from datetime import datetime

# Load JSON data
with open('data/papers.json', 'r') as f:
    data = json.load(f)

papers = data.get('papers', [])
tags = data.get('tags', [])

print(f"Found {len(papers)} papers and {len(tags)} tags in JSON")

# Connect to SQLite
conn = sqlite3.connect('data/papers.db')
cursor = conn.cursor()

# Insert tags
for tag in tags:
    try:
        cursor.execute(
            "INSERT OR IGNORE INTO tags (id, name) VALUES (?, ?)",
            (tag['id'], tag['name'])
        )
    except Exception as e:
        print(f"Error inserting tag {tag}: {e}")

print(f"Inserted tags")

# Insert papers
for paper in papers:
    try:
        cursor.execute("""
            INSERT OR REPLACE INTO papers (
                id, title, authors, abstract, year, arxiv_id, arxiv_url,
                doi, paper_url, conference, category, published_at, pdf_path,
                summary_one_line, summary_contribution, summary_methodology,
                summary_results, full_summary, translation, full_translation,
                created_at, updated_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            paper.get('id'),
            paper.get('title', ''),
            json.dumps(paper.get('authors', [])),
            paper.get('abstract'),
            paper.get('year'),
            paper.get('arxiv_id'),
            paper.get('arxiv_url'),
            paper.get('doi'),
            paper.get('paper_url') or paper.get('url'),
            paper.get('conference'),
            paper.get('category', 'other'),
            paper.get('published_at'),
            paper.get('pdf_path'),
            paper.get('summary', {}).get('one_line') if isinstance(paper.get('summary'), dict) else None,
            paper.get('summary', {}).get('contribution') if isinstance(paper.get('summary'), dict) else None,
            paper.get('summary', {}).get('methodology') if isinstance(paper.get('summary'), dict) else None,
            paper.get('summary', {}).get('results') if isinstance(paper.get('summary'), dict) else None,
            paper.get('full_summary'),
            json.dumps(paper.get('translation')) if paper.get('translation') else None,
            paper.get('full_translation'),
            paper.get('created_at', datetime.now().isoformat()),
            paper.get('updated_at', datetime.now().isoformat())
        ))

        # Insert paper-tag relationships
        for tag_name in paper.get('tags', []):
            # Find tag id by name
            cursor.execute("SELECT id FROM tags WHERE name = ?", (tag_name,))
            row = cursor.fetchone()
            if row:
                tag_id = row[0]
                cursor.execute(
                    "INSERT OR IGNORE INTO paper_tags (paper_id, tag_id) VALUES (?, ?)",
                    (paper['id'], tag_id)
                )
    except Exception as e:
        print(f"Error inserting paper {paper.get('title', 'unknown')}: {e}")

conn.commit()
print(f"Migration complete!")

# Verify
cursor.execute("SELECT COUNT(*) FROM papers")
print(f"Papers in SQLite: {cursor.fetchone()[0]}")
cursor.execute("SELECT COUNT(*) FROM tags")
print(f"Tags in SQLite: {cursor.fetchone()[0]}")

conn.close()
