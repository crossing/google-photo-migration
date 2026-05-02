import sqlite3

from src.core.interfaces import StateStore


class MigrationStateDB(StateStore):
    def __init__(self, db_path: str):
        self.db_path = db_path
        self._init_db()

    def _init_db(self) -> None:
        with sqlite3.connect(self.db_path) as conn:
            conn.execute('''
                CREATE TABLE IF NOT EXISTS media_items (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    zip_id TEXT,
                    zip_filename TEXT,
                    file_path TEXT,
                    status TEXT DEFAULT 'pending',
                    upload_token TEXT,
                    error_message TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            conn.execute('''
                CREATE INDEX IF NOT EXISTS idx_zip_status
                ON media_items(zip_id, status)
            ''')

    def add_items(self, items: list[tuple[str, str, str]]) -> None:
        """Bulk insert items - list of (zip_id, zip_filename, file_path) tuples."""
        if not items:
            return
        with sqlite3.connect(self.db_path) as conn:
            conn.executemany('''
                INSERT INTO media_items (zip_id, zip_filename, file_path)
                VALUES (?, ?, ?)
            ''', items)
            conn.commit()

    def get_pending_items(self, container_id: str) -> list[tuple[int, str]]:
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute('''
                SELECT id, file_path FROM media_items
                WHERE zip_id = ? AND status = 'pending'
            ''', (container_id,))
            return [(row[0], row[1]) for row in cursor.fetchall()]

    def mark_completed(self, item_id: int, upload_token: str) -> None:
        with sqlite3.connect(self.db_path) as conn:
            conn.execute('''
                UPDATE media_items
                SET status = 'completed', upload_token = ?, updated_at = CURRENT_TIMESTAMP
                WHERE id = ?
            ''', (upload_token, item_id))
            conn.commit()

    def mark_failed(self, item_id: int, error_message: str) -> None:
        with sqlite3.connect(self.db_path) as conn:
            conn.execute('''
                UPDATE media_items
                SET status = 'failed', error_message = ?, updated_at = CURRENT_TIMESTAMP
                WHERE id = ?
            ''', (error_message, item_id))
            conn.commit()

    def get_uploaded_tokens(self) -> list[str]:
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute('''
                SELECT upload_token FROM media_items
                WHERE status = 'uploaded'
            ''')
            return [row[0] for row in cursor.fetchall()]

    def get_total_count(self, zip_id: str) -> int:
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute('SELECT COUNT(*) FROM media_items WHERE zip_id = ?', (zip_id,))
            return int(cursor.fetchone()[0])

    def get_completed_count(self, zip_id: str) -> int:
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute(
                "SELECT COUNT(*) FROM media_items WHERE zip_id = ? AND status = 'completed'",
                (zip_id,)
            )
            return int(cursor.fetchone()[0])

    def get_failed_count(self, zip_id: str) -> int:
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute(
                "SELECT COUNT(*) FROM media_items WHERE zip_id = ? AND status = 'failed'",
                (zip_id,)
            )
            return int(cursor.fetchone()[0])

    def is_zip_processed(self, zip_id: str) -> bool:
        total = self.get_total_count(zip_id)
        if total == 0:
            return False
        pending = len(self.get_pending_items(zip_id))
        return pending == 0

    def clear_state(self) -> None:
        with sqlite3.connect(self.db_path) as conn:
            conn.execute('DELETE FROM media_items')
            conn.commit()
