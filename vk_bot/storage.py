from __future__ import annotations

import json
from typing import Any, Dict, Optional

from db import get_conn
from states import States

def get_user_state(user_id: int) -> tuple[str, Dict[str, Any]]:
    with get_conn() as conn:
        row = conn.execute(
            "SELECT state, payload_json FROM user_states WHERE user_id = ?",
            (user_id,),
        ).fetchone()
    if not row:
        return States.IDLE, {}
    payload = json.loads(row["payload_json"]) if row["payload_json"] else {}
    return row["state"], payload

def set_user_state(user_id: int, state: str, payload: Optional[Dict[str, Any]] = None) -> None:
    payload_json = json.dumps(payload or {}, ensure_ascii=False)
    with get_conn() as conn:
        conn.execute(
            '''
            INSERT INTO user_states(user_id, state, payload_json, updated_at)
            VALUES (?, ?, ?, CURRENT_TIMESTAMP)
            ON CONFLICT(user_id) DO UPDATE SET
                state=excluded.state,
                payload_json=excluded.payload_json,
                updated_at=CURRENT_TIMESTAMP
            ''',
            (user_id, state, payload_json),
        )

def clear_user_state(user_id: int) -> None:
    set_user_state(user_id, States.IDLE, {})
