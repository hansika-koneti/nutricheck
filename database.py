import sqlite3
import os
from config import DATABASE_PATH


def get_db():
    """Get a database connection with row factory."""
    conn = sqlite3.connect(DATABASE_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    return conn


def init_db():
    """Initialize database tables."""
    os.makedirs(os.path.dirname(DATABASE_PATH), exist_ok=True)
    conn = get_db()
    conn.executescript('''
        CREATE TABLE IF NOT EXISTS analyses (
            id              INTEGER PRIMARY KEY AUTOINCREMENT,
            product_name    TEXT DEFAULT 'Unknown Product',
            image_path      TEXT NOT NULL,
            calories        REAL,
            sugar           REAL,
            fat             REAL,
            sodium          REAL,
            protein         REAL,
            fiber           REAL,
            health_score    INTEGER,
            verdict         TEXT,
            explanation     TEXT,
            recommendation  TEXT,
            raw_ocr_text    TEXT,
            created_at      DATETIME DEFAULT CURRENT_TIMESTAMP
        );
    ''')
    conn.commit()
    conn.close()


def save_analysis(data):
    """Save an analysis result and return the inserted row ID."""
    conn = get_db()
    cursor = conn.execute('''
        INSERT INTO analyses 
        (product_name, image_path, calories, sugar, fat, sodium, protein, fiber,
         health_score, verdict, explanation, recommendation, raw_ocr_text)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    ''', (
        data.get('product_name', 'Unknown Product'),
        data['image_path'],
        data.get('calories'),
        data.get('sugar'),
        data.get('fat'),
        data.get('sodium'),
        data.get('protein'),
        data.get('fiber'),
        data.get('health_score'),
        data.get('verdict'),
        data.get('explanation'),
        data.get('recommendation'),
        data.get('raw_ocr_text')
    ))
    conn.commit()
    row_id = cursor.lastrowid
    conn.close()
    return row_id


def get_all_analyses():
    """Return all analyses ordered by most recent."""
    conn = get_db()
    rows = conn.execute(
        'SELECT * FROM analyses ORDER BY created_at DESC'
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def get_analysis_by_id(analysis_id):
    """Return a single analysis by ID."""
    conn = get_db()
    row = conn.execute(
        'SELECT * FROM analyses WHERE id = ?', (analysis_id,)
    ).fetchone()
    conn.close()
    return dict(row) if row else None


def delete_analysis(analysis_id):
    """Delete an analysis by ID. Returns True if a row was deleted."""
    conn = get_db()
    cursor = conn.execute('DELETE FROM analyses WHERE id = ?', (analysis_id,))
    conn.commit()
    deleted = cursor.rowcount > 0
    conn.close()
    return deleted


def get_analyses_by_ids(ids):
    """Return analyses matching the given list of IDs."""
    if not ids:
        return []
    placeholders = ','.join('?' for _ in ids)
    conn = get_db()
    rows = conn.execute(
        f'SELECT * FROM analyses WHERE id IN ({placeholders})', ids
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]
