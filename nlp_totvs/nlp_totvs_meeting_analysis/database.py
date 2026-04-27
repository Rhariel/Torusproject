"""SQLite persistence layer for NLP analysis results."""

from __future__ import annotations

import sqlite3
from pathlib import Path


BASE_DIR = Path(__file__).resolve().parent
DB_PATH = BASE_DIR / "meeting_analysis.db"


def get_connection() -> sqlite3.Connection:
    connection = sqlite3.connect(DB_PATH)
    connection.row_factory = sqlite3.Row
    return connection


def init_db() -> None:
    with get_connection() as connection:
        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS analyses (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                text TEXT NOT NULL,
                intent TEXT NOT NULL,
                sentiment TEXT NOT NULL,
                churn_signal INTEGER NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
            """
        )
        connection.commit()


def insert_data(text: str, intent: str, sentiment: str, churn_signal: bool) -> None:
    with get_connection() as connection:
        connection.execute(
            """
            INSERT INTO analyses (text, intent, sentiment, churn_signal)
            VALUES (?, ?, ?, ?)
            """,
            (text, intent, sentiment, int(churn_signal)),
        )
        connection.commit()
