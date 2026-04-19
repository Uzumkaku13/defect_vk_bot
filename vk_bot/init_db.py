from __future__ import annotations

from db import get_conn

SCHEMA = [
    """
    CREATE TABLE IF NOT EXISTS reports (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL,
        report_year INTEGER,
        report_seq INTEGER,
        report_number TEXT,
        client_name TEXT,
        client_phone TEXT,
        object_name TEXT,
        equipment TEXT,
        comment TEXT,
        status TEXT NOT NULL DEFAULT 'draft',
        pdf_path TEXT,
        created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
        updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS defects (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        report_id INTEGER NOT NULL,
        description TEXT NOT NULL,
        photo_url TEXT,
        photo_path TEXT,
        created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY(report_id) REFERENCES reports(id) ON DELETE CASCADE
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS user_states (
        user_id INTEGER PRIMARY KEY,
        state TEXT NOT NULL,
        payload_json TEXT,
        updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
    )
    """,
    """
    CREATE INDEX IF NOT EXISTS idx_reports_user_status
    ON reports(user_id, status)
    """,
    """
    CREATE INDEX IF NOT EXISTS idx_defects_report
    ON defects(report_id)
    """,
]


def _ensure_column(conn, table_name: str, column_name: str, column_type: str) -> None:
    existing = {row[1] for row in conn.execute(f"PRAGMA table_info({table_name})").fetchall()}
    if column_name not in existing:
        conn.execute(f"ALTER TABLE {table_name} ADD COLUMN {column_name} {column_type}")


def _backfill_report_numbers(conn) -> None:
    rows = conn.execute(
        """
        SELECT id, created_at, report_year, report_seq, report_number
        FROM reports
        ORDER BY id ASC
        """
    ).fetchall()
    seq_by_year: dict[int, int] = {}
    for row in rows:
        created_at = row[1] or ""
        year = row[2]
        if year is None:
            try:
                year = int(str(created_at)[:4])
            except Exception:
                year = 2026
        year = int(year)
        seq = row[3]
        if seq is None:
            seq_by_year[year] = seq_by_year.get(year, 0) + 1
            seq = seq_by_year[year]
        else:
            seq = int(seq)
            seq_by_year[year] = max(seq_by_year.get(year, 0), seq)
        report_number = row[4] or f"№ {year}-{seq:07d}"
        conn.execute(
            "UPDATE reports SET report_year = ?, report_seq = ?, report_number = ? WHERE id = ?",
            (year, seq, report_number, row[0]),
        )


def init_db() -> None:
    with get_conn() as conn:
        for stmt in SCHEMA:
            conn.execute(stmt)
        _ensure_column(conn, "reports", "report_year", "INTEGER")
        _ensure_column(conn, "reports", "report_seq", "INTEGER")
        _ensure_column(conn, "reports", "report_number", "TEXT")
        _ensure_column(conn, "reports", "pdf_path", "TEXT")
        _ensure_column(conn, "defects", "photo_url", "TEXT")
        _ensure_column(conn, "defects", "photo_path", "TEXT")
        _backfill_report_numbers(conn)


if __name__ == "__main__":
    init_db()
    print("База данных инициализирована.")
