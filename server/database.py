import sqlite3
from datetime import datetime


class Database:
    def __init__(self, db_path="records.db"):
        self.db_path = db_path
        self._init_db()

    def _init_db(self):
        conn = sqlite3.connect(self.db_path)
        conn.execute('''
            CREATE TABLE IF NOT EXISTS records (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                plate_number TEXT NOT NULL,
                color TEXT,
                confidence REAL,
                image_path TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        conn.commit()
        conn.close()

    def add_record(self, plate_number, color, confidence, image_path=None):
        conn = sqlite3.connect(self.db_path)
        conn.execute(
            "INSERT INTO records (plate_number, color, confidence, image_path) VALUES (?, ?, ?, ?)",
            (plate_number, color, confidence, image_path)
        )
        conn.commit()
        conn.close()

    def get_records(self, page=1, per_page=20):
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        offset = (page - 1) * per_page
        cursor = conn.execute(
            "SELECT * FROM records ORDER BY created_at DESC LIMIT ? OFFSET ?",
            (per_page, offset)
        )
        rows = cursor.fetchall()
        conn.close()
        return [dict(row) for row in rows]

    def get_total_count(self):
        conn = sqlite3.connect(self.db_path)
        cursor = conn.execute("SELECT COUNT(*) FROM records")
        count = cursor.fetchone()[0]
        conn.close()
        return count

    def clear_records(self):
        conn = sqlite3.connect(self.db_path)
        conn.execute("DELETE FROM records")
        conn.execute("DELETE FROM sqlite_sequence WHERE name='records'")
        conn.commit()
        conn.close()
