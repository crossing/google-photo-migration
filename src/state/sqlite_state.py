import sqlite3
from src.core.interfaces import StateStore
from typing import List, Any

class MigrationStateDB(StateStore):
    def __init__(self, db_path='migration_state.db'):
        self.db_path = db_path
        self._init_db()

    def _init_db(self):
        with sqlite3.connect(self.db_path) as conn:
            conn.execute('''
                CREATE TABLE IF NOT EXISTS indexed_zips (
                    zip_id TEXT PRIMARY KEY,
                    zip_filename TEXT,
                    indexed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            conn.execute('''
                CREATE TABLE IF NOT EXISTS media_items (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    zip_id TEXT,
                    zip_filename TEXT,
                    file_path TEXT,
                    status TEXT DEFAULT 'pending',
                    upload_token TEXT,
                    UNIQUE(zip_id, file_path)
                )
            ''')
            conn.commit()

    def is_indexed(self, container_id: str) -> bool:
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute('SELECT 1 FROM indexed_zips WHERE zip_id = ?', (container_id,))
            return cursor.fetchone() is not None

    def mark_indexed(self, container_id: str, container_name: str):
        with sqlite3.connect(self.db_path) as conn:
            conn.execute('''
                INSERT OR REPLACE INTO indexed_zips (zip_id, zip_filename)
                VALUES (?, ?)
            ''', (container_id, container_name))
            conn.commit()

    def add_items(self, items: List[tuple]):
        """Bulk insert items - list of (zip_id, zip_filename, file_path) tuples."""
        if not items:
            return
        with sqlite3.connect(self.db_path) as conn:
            conn.executemany('''
                INSERT OR IGNORE INTO media_items (zip_id, zip_filename, file_path, status)
                VALUES (?, ?, ?, 'pending')
            ''', items)
            conn.commit()

    def get_pending_items(self, container_id: str) -> List[tuple]:
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute('''
                SELECT id, file_path FROM media_items 
                WHERE zip_id = ? AND status = 'pending'
            ''', (container_id,))
            return cursor.fetchall()

    def mark_uploaded(self, item_id: Any, upload_token: str):
        with sqlite3.connect(self.db_path) as conn:
            conn.execute('''
                UPDATE media_items SET status = 'uploaded', upload_token = ? WHERE id = ?
            ''', (upload_token, item_id))

    def mark_completed(self, upload_token: str):
        with sqlite3.connect(self.db_path) as conn:
            conn.execute('''
                UPDATE media_items SET status = 'created' WHERE upload_token = ?
            ''', (upload_token,))

    def get_uploaded_tokens(self) -> List[str]:
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute('''
                SELECT upload_token FROM media_items WHERE status = 'uploaded'
            ''')
            return [row[0] for row in cursor.fetchall()]

    # Compatibility aliases
    def is_zip_indexed(self, zip_id):
        return self.is_indexed(zip_id)

    def mark_zip_indexed(self, zip_id, zip_filename):
        return self.mark_indexed(zip_id, zip_filename)

    def add_media_items_batch(self, items):
        return self.add_items(items)

    def mark_created(self, upload_token):
        return self.mark_completed(upload_token)

    def get_stats(self, zip_id):
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute('''
                SELECT status, COUNT(*) FROM media_items WHERE zip_id = ? GROUP BY status
            ''', (zip_id,))
            return dict(cursor.fetchall())
