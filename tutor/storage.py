import json
import sqlite3
from datetime import UTC, datetime
from pathlib import Path


def utc_now() -> str:
    return datetime.now(UTC).isoformat()


class Store:
    """Small single-user SQLite repository; transactions never span network awaits."""

    def __init__(self, path: str):
        if path != ":memory:":
            Path(path).parent.mkdir(parents=True, exist_ok=True)
        self.db = sqlite3.connect(path)
        self.db.row_factory = sqlite3.Row
        self.db.execute("PRAGMA journal_mode=WAL")
        self.db.executescript("""
            CREATE TABLE IF NOT EXISTS settings (id INTEGER PRIMARY KEY CHECK(id=1), body TEXT NOT NULL);
            CREATE TABLE IF NOT EXISTS session (id INTEGER PRIMARY KEY CHECK(id=1), body TEXT NOT NULL);
            CREATE TABLE IF NOT EXISTS progress (
                lesson_id TEXT PRIMARY KEY, status TEXT NOT NULL, updated_at TEXT NOT NULL);
            CREATE TABLE IF NOT EXISTS attempts (
                id TEXT PRIMARY KEY, lesson_id TEXT NOT NULL, body TEXT NOT NULL, created_at TEXT NOT NULL);
            CREATE TABLE IF NOT EXISTS deferred (lesson_id TEXT PRIMARY KEY, until_at TEXT NOT NULL);
            CREATE TABLE IF NOT EXISTS deliveries (slot TEXT PRIMARY KEY, created_at TEXT NOT NULL);
            CREATE TABLE IF NOT EXISTS service_messages (
                chat_id INTEGER NOT NULL, message_id INTEGER NOT NULL,
                PRIMARY KEY (chat_id, message_id));
        """)

    def close(self):
        self.db.close()

    def service_messages(self, chat_id: int) -> list[int]:
        return [
            row[0]
            for row in self.db.execute(
                "SELECT message_id FROM service_messages WHERE chat_id=? ORDER BY message_id", (chat_id,)
            )
        ]

    def track_service_message(self, chat_id: int, message_id: int):
        with self.db:
            self.db.execute("INSERT OR IGNORE INTO service_messages VALUES (?, ?)", (chat_id, message_id))

    def forget_service_message(self, chat_id: int, message_id: int):
        with self.db:
            self.db.execute(
                "DELETE FROM service_messages WHERE chat_id=? AND message_id=?", (chat_id, message_id)
            )

    def settings(self) -> dict | None:
        row = self.db.execute("SELECT body FROM settings WHERE id=1").fetchone()
        return json.loads(row[0]) if row else None

    def save_settings(self, value: dict):
        with self.db:
            self.db.execute(
                "INSERT OR REPLACE INTO settings VALUES (1, ?)", (json.dumps(value, ensure_ascii=False),)
            )

    def session(self) -> dict | None:
        row = self.db.execute("SELECT body FROM session WHERE id=1").fetchone()
        return json.loads(row[0]) if row else None

    def save_session(self, value: dict | None):
        with self.db:
            if value is None:
                self.db.execute("DELETE FROM session")
            else:
                self.db.execute(
                    "INSERT OR REPLACE INTO session VALUES (1, ?)", (json.dumps(value, ensure_ascii=False),)
                )

    def progress(self) -> dict[str, str]:
        return dict(self.db.execute("SELECT lesson_id, status FROM progress").fetchall())

    def deferred(self) -> dict[str, str]:
        return dict(self.db.execute("SELECT lesson_id, until_at FROM deferred").fetchall())

    def postpone(self, lesson_id: str, until: str):
        with self.db:
            self.db.execute("INSERT OR REPLACE INTO deferred VALUES (?, ?)", (lesson_id, until))
            self.db.execute("DELETE FROM session")

    def finish(self, session: dict, passed: bool):
        """One atomic commit for verdict, attempt history and resumable result screen."""
        with self.db:
            self.db.execute(
                "INSERT OR IGNORE INTO attempts VALUES (?, ?, ?, ?)",
                (session["id"], session["lesson_id"], json.dumps(session, ensure_ascii=False), utc_now()),
            )
            self.db.execute(
                "INSERT OR REPLACE INTO progress VALUES (?, ?, ?)",
                (session["lesson_id"], "passed" if passed else "failed", utc_now()),
            )
            self.db.execute("DELETE FROM deferred WHERE lesson_id=?", (session["lesson_id"],))
            self.db.execute(
                "INSERT OR REPLACE INTO session VALUES (1, ?)", (json.dumps(session, ensure_ascii=False),)
            )

    def claim_slot(self, slot: str) -> bool:
        with self.db:
            return (
                self.db.execute("INSERT OR IGNORE INTO deliveries VALUES (?, ?)", (slot, utc_now())).rowcount
                == 1
            )

    def release_slot(self, slot: str):
        with self.db:
            self.db.execute("DELETE FROM deliveries WHERE slot=?", (slot,))
