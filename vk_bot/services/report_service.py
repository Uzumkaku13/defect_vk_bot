from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, List, Optional

from db import get_conn
from states import States


def _current_year() -> int:
    return datetime.now().year


def _next_report_sequence(conn, year: int) -> int:
    row = conn.execute(
        "SELECT COALESCE(MAX(report_seq), 0) AS max_seq FROM reports WHERE report_year = ?",
        (year,),
    ).fetchone()
    return int(row["max_seq"]) + 1


def _format_report_number(year: int, seq: int) -> str:
    return f"№ {year}-{seq:07d}"


def create_report(user_id: int) -> int:
    year = _current_year()
    with get_conn() as conn:
        seq = _next_report_sequence(conn, year)
        report_number = _format_report_number(year, seq)
        cur = conn.execute(
            """
            INSERT INTO reports(user_id, status, report_year, report_seq, report_number)
            VALUES (?, 'draft', ?, ?, ?)
            """,
            (user_id, year, seq, report_number),
        )
        return int(cur.lastrowid)


def get_active_report(user_id: int) -> Optional[dict]:
    with get_conn() as conn:
        row = conn.execute(
            """
            SELECT * FROM reports
            WHERE user_id = ? AND status = 'draft'
            ORDER BY id DESC
            LIMIT 1
            """,
            (user_id,),
        ).fetchone()
    return dict(row) if row else None


def get_report(report_id: int) -> Optional[dict]:
    with get_conn() as conn:
        row = conn.execute("SELECT * FROM reports WHERE id = ?", (report_id,)).fetchone()
    return dict(row) if row else None


def get_next_state_for_report(report: dict | None) -> str:
    if not report:
        return States.IDLE
    if not (report.get("client_name") or "").strip():
        return States.WAIT_CLIENT_NAME
    if not (report.get("client_phone") or "").strip():
        return States.WAIT_CLIENT_PHONE
    if not (report.get("object_name") or "").strip():
        return States.WAIT_OBJECT_NAME
    if not (report.get("equipment") or "").strip():
        return States.WAIT_EQUIPMENT
    if not (report.get("comment") or "").strip():
        return States.WAIT_COMMENT
    return States.WAIT_DEFECT


def update_report_client(report_id: int, client_name: Optional[str] = None, client_phone: Optional[str] = None) -> None:
    with get_conn() as conn:
        if client_name is not None:
            conn.execute(
                "UPDATE reports SET client_name = ?, updated_at = CURRENT_TIMESTAMP WHERE id = ?",
                (client_name, report_id),
            )
        if client_phone is not None:
            conn.execute(
                "UPDATE reports SET client_phone = ?, updated_at = CURRENT_TIMESTAMP WHERE id = ?",
                (client_phone, report_id),
            )


def update_report_object(report_id: int, object_name: str) -> None:
    with get_conn() as conn:
        conn.execute(
            "UPDATE reports SET object_name = ?, updated_at = CURRENT_TIMESTAMP WHERE id = ?",
            (object_name, report_id),
        )


def update_report_equipment(report_id: int, equipment: str) -> None:
    with get_conn() as conn:
        conn.execute(
            "UPDATE reports SET equipment = ?, updated_at = CURRENT_TIMESTAMP WHERE id = ?",
            (equipment, report_id),
        )


def update_report_comment(report_id: int, comment: str) -> None:
    with get_conn() as conn:
        conn.execute(
            "UPDATE reports SET comment = ?, updated_at = CURRENT_TIMESTAMP WHERE id = ?",
            (comment, report_id),
        )


def add_defect(report_id: int, description: str, photo_url: Optional[str] = None, photo_path: Optional[str] = None) -> int:
    with get_conn() as conn:
        cur = conn.execute(
            "INSERT INTO defects(report_id, description, photo_url, photo_path) VALUES (?, ?, ?, ?)",
            (report_id, description, photo_url, photo_path),
        )
        conn.execute(
            "UPDATE reports SET updated_at = CURRENT_TIMESTAMP WHERE id = ?",
            (report_id,),
        )
        return int(cur.lastrowid)


def get_defects(report_id: int) -> List[dict]:
    with get_conn() as conn:
        rows = conn.execute(
            "SELECT * FROM defects WHERE report_id = ? ORDER BY id ASC",
            (report_id,),
        ).fetchall()
    return [dict(r) for r in rows]


def finalize_report(report_id: int, pdf_path: str) -> None:
    with get_conn() as conn:
        conn.execute(
            "UPDATE reports SET status = 'done', pdf_path = ?, updated_at = CURRENT_TIMESTAMP WHERE id = ?",
            (pdf_path, report_id),
        )


def cancel_active_report(user_id: int) -> bool:
    report = get_active_report(user_id)
    if not report:
        return False
    with get_conn() as conn:
        conn.execute("DELETE FROM reports WHERE id = ?", (report["id"],))
    return True


def list_recent_reports(user_id: int, limit: int = 10) -> List[dict]:
    with get_conn() as conn:
        rows = conn.execute(
            """
            SELECT id, report_number, client_name, object_name, equipment, status, created_at, pdf_path
            FROM reports
            WHERE user_id = ?
            ORDER BY id DESC
            LIMIT ?
            """,
            (user_id, limit),
        ).fetchall()
    return [dict(r) for r in rows]


def get_stats(user_id: int) -> Dict[str, Any]:
    with get_conn() as conn:
        total_reports = conn.execute(
            "SELECT COUNT(*) AS cnt FROM reports WHERE user_id = ?",
            (user_id,),
        ).fetchone()["cnt"]
        done_reports = conn.execute(
            "SELECT COUNT(*) AS cnt FROM reports WHERE user_id = ? AND status = 'done'",
            (user_id,),
        ).fetchone()["cnt"]
        draft_reports = conn.execute(
            "SELECT COUNT(*) AS cnt FROM reports WHERE user_id = ? AND status = 'draft'",
            (user_id,),
        ).fetchone()["cnt"]
        total_defects = conn.execute(
            """
            SELECT COUNT(d.id) AS cnt
            FROM defects d
            JOIN reports r ON r.id = d.report_id
            WHERE r.user_id = ?
            """,
            (user_id,),
        ).fetchone()["cnt"]
    return {
        "total_reports": total_reports,
        "done_reports": done_reports,
        "draft_reports": draft_reports,
        "total_defects": total_defects,
    }
