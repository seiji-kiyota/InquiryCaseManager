"""対応履歴のID採番、登録、一覧取得。"""

from datetime import datetime

from common.db import get_connection
from common.models import INQUIRY_TARGET_TYPE, STATUS_CHANGE_ACTION_TYPE
from common.validators import parse_date, parse_datetime, validate_history

HISTORY_ID_PREFIX = "HIS-"


def _text(value):
    if value is None:
        return ""
    return str(value).strip()


def _date_text(value):
    parsed = parse_date(value)
    return parsed.isoformat() if parsed is not None else ""


def _datetime_text(value):
    parsed = parse_datetime(value)
    return parsed.strftime("%Y-%m-%d %H:%M:%S") if parsed is not None else ""


def generate_history_id(db_path=None, conn=None):
    """次の対応履歴ID（HIS-000001）を返す。"""
    should_close = conn is None
    if conn is None:
        conn = get_connection(db_path)
    try:
        rows = conn.execute(
            "SELECT history_id FROM histories WHERE history_id LIKE ?",
            (f"{HISTORY_ID_PREFIX}%",),
        ).fetchall()
        max_number = 0
        for row in rows:
            suffix = row["history_id"][len(HISTORY_ID_PREFIX) :]
            if suffix.isdigit():
                max_number = max(max_number, int(suffix))
        return f"{HISTORY_ID_PREFIX}{max_number + 1:06d}"
    finally:
        if should_close:
            conn.close()


def get_histories_by_target(target_type, target_id, db_path=None):
    """対象の対応履歴を新しい順で返す。"""
    conn = get_connection(db_path)
    try:
        rows = conn.execute(
            """
            SELECT *
            FROM histories
            WHERE target_type = ? AND target_id = ?
            ORDER BY action_datetime DESC, created_at DESC, history_id DESC
            """,
            (_text(target_type), _text(target_id)),
        ).fetchall()
        return [dict(row) for row in rows]
    finally:
        conn.close()


def create_history(data, db_path=None, conn=None, now=None):
    """対応履歴を登録し、履歴IDを返す。対象が無い場合は None。"""
    errors = validate_history(data)
    if errors:
        raise ValueError("\n".join(errors))

    payload = data or {}
    target_type = _text(payload.get("target_type")) or INQUIRY_TARGET_TYPE
    target_id = _text(payload.get("target_id"))
    timestamp = (now or datetime.now()).strftime("%Y-%m-%d %H:%M:%S")

    should_close = conn is None
    if conn is None:
        conn = get_connection(db_path)
    try:
        if target_type == INQUIRY_TARGET_TYPE:
            existing = conn.execute(
                "SELECT inquiry_id FROM inquiries WHERE inquiry_id = ?",
                (target_id,),
            ).fetchone()
            if existing is None:
                return None

        history_id = generate_history_id(conn=conn)
        conn.execute(
            """
            INSERT INTO histories (
                history_id,
                target_type,
                target_id,
                action_datetime,
                operator,
                action_type,
                action_detail,
                next_action_date,
                old_status,
                new_status,
                created_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                history_id,
                target_type,
                target_id,
                _datetime_text(payload.get("action_datetime")) or timestamp,
                _text(payload.get("operator")),
                _text(payload.get("action_type")),
                _text(payload.get("action_detail")),
                _date_text(payload.get("next_action_date")),
                _text(payload.get("old_status")),
                _text(payload.get("new_status")),
                timestamp,
            ),
        )
        if should_close:
            conn.commit()
        return history_id
    except Exception:
        if should_close:
            conn.rollback()
        raise
    finally:
        if should_close:
            conn.close()


def create_status_change_history(
    inquiry_id,
    old_status,
    new_status,
    operator,
    action_datetime=None,
    db_path=None,
    conn=None,
    now=None,
):
    """ステータス変更時の対応履歴を登録する。変更がなければ None。"""
    previous = _text(old_status)
    current = _text(new_status)
    if previous == current:
        return None

    timestamp = now or datetime.now()
    return create_history(
        {
            "target_type": INQUIRY_TARGET_TYPE,
            "target_id": inquiry_id,
            "action_datetime": action_datetime or timestamp,
            "operator": operator,
            "action_type": STATUS_CHANGE_ACTION_TYPE,
            "action_detail": f"ステータスを「{previous}」から「{current}」に変更しました。",
            "old_status": previous,
            "new_status": current,
        },
        db_path=db_path,
        conn=conn,
        now=timestamp if isinstance(timestamp, datetime) else now,
    )
