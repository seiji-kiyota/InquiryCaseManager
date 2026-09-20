"""案件のID採番、案件化、一覧、更新。"""

from datetime import date, datetime

from common.db import get_connection
from common.inquiry_service import get_inquiry_by_id, is_overdue
from common.models import CASE_COMPLETED_STATUS, UNASSIGNED_ASSIGNEE
from common.validators import parse_date, parse_progress, validate_case

CASE_FREEWORD_COLUMNS = (
    "case_id",
    "inquiry_id",
    "case_name",
    "customer_name",
    "summary",
)


def _text(value):
    if value is None:
        return ""
    return str(value).strip()


def _date_text(value):
    parsed = parse_date(value)
    return parsed.isoformat() if parsed is not None else ""


def _year_month(base_date):
    parsed = parse_date(base_date)
    if parsed is None:
        raise ValueError("案件作成日が指定されていません。")
    return parsed.strftime("%Y%m")


def generate_case_id(base_date, db_path=None, conn=None):
    """作成年月単位で次の案件ID（CASE-YYYYMM-0001）を返す。"""
    prefix = f"CASE-{_year_month(base_date)}-"
    should_close = conn is None
    if conn is None:
        conn = get_connection(db_path)
    try:
        rows = conn.execute(
            "SELECT case_id FROM cases WHERE case_id LIKE ?",
            (f"{prefix}%",),
        ).fetchall()
        max_number = 0
        for row in rows:
            suffix = row["case_id"][len(prefix) :]
            if suffix.isdigit():
                max_number = max(max_number, int(suffix))
        return f"{prefix}{max_number + 1:04d}"
    finally:
        if should_close:
            conn.close()


def get_case_by_id(case_id, db_path=None, today=None):
    """案件IDで1件取得する。存在しない場合は None。"""
    current_id = _text(case_id)
    if not current_id:
        return None

    conn = get_connection(db_path)
    try:
        row = conn.execute(
            "SELECT * FROM cases WHERE case_id = ?",
            (current_id,),
        ).fetchone()
    finally:
        conn.close()

    if row is None:
        return None
    item = dict(row)
    item["overdue"] = is_overdue(item.get("due_date"), item.get("status"), today=today)
    return item


def get_case_by_inquiry_id(inquiry_id, db_path=None, today=None, conn=None):
    """問い合わせIDに紐づく案件を1件取得する。"""
    current_id = _text(inquiry_id)
    if not current_id:
        return None

    should_close = conn is None
    if conn is None:
        conn = get_connection(db_path)
    try:
        row = conn.execute(
            "SELECT * FROM cases WHERE inquiry_id = ?",
            (current_id,),
        ).fetchone()
    finally:
        if should_close:
            conn.close()

    if row is None:
        return None
    item = dict(row)
    item["overdue"] = is_overdue(item.get("due_date"), item.get("status"), today=today)
    return item


def is_inquiry_converted(inquiry_id, db_path=None, conn=None):
    """問い合わせが案件化済みなら True。"""
    return get_case_by_inquiry_id(inquiry_id, db_path=db_path, conn=conn) is not None


def count_cases(db_path=None):
    """登録済み案件の総件数を返す。"""
    conn = get_connection(db_path)
    try:
        return conn.execute("SELECT COUNT(*) AS n FROM cases").fetchone()["n"]
    finally:
        conn.close()


def search_cases(filters=None, db_path=None, today=None):
    """条件で案件を検索し、overdue フラグを付与して返す。"""
    filters = filters or {}
    current_day = today if today is not None else date.today()
    conditions = []
    params = []

    keyword = _text(filters.get("keyword"))
    if keyword:
        like = f"%{keyword}%"
        placeholders = " OR ".join(f"{column} LIKE ?" for column in CASE_FREEWORD_COLUMNS)
        conditions.append(f"({placeholders})")
        params.extend([like] * len(CASE_FREEWORD_COLUMNS))

    for column, key in (
        ("assignee", "assignees"),
        ("priority", "priorities"),
        ("status", "statuses"),
    ):
        values = [_text(value) for value in (filters.get(key) or []) if _text(value)]
        if values:
            placeholders = ", ".join("?" for _ in values)
            conditions.append(f"{column} IN ({placeholders})")
            params.extend(values)

    where_sql = f"WHERE {' AND '.join(conditions)}" if conditions else ""
    sql = f"""
        SELECT *
        FROM cases
        {where_sql}
        ORDER BY start_date DESC, created_at DESC, case_id DESC
    """

    conn = get_connection(db_path)
    try:
        rows = [dict(row) for row in conn.execute(sql, params).fetchall()]
    finally:
        conn.close()

    results = []
    for row in rows:
        row["overdue"] = is_overdue(row.get("due_date"), row.get("status"), today=current_day)
        results.append(row)

    if filters.get("overdue_only"):
        results = [row for row in results if row["overdue"]]
    return results


def get_cases(db_path=None, today=None):
    """全件を開始日降順で返す。"""
    return search_cases(db_path=db_path, today=today)


def create_case_from_inquiry(inquiry_id, db_path=None, today=None, now=None):
    """問い合わせから案件を作成し、案件IDを返す。"""
    inquiry = get_inquiry_by_id(inquiry_id, db_path=db_path)
    if inquiry is None:
        return None

    start_date = today if today is not None else date.today()
    timestamp_dt = now or datetime.now()
    timestamp = timestamp_dt.strftime("%Y-%m-%d %H:%M:%S")
    payload = {
        "case_name": inquiry["subject"],
        "customer_name": inquiry["customer_name"],
        "assignee": inquiry["assignee"] or UNASSIGNED_ASSIGNEE,
        "sub_assignee": "",
        "priority": inquiry["priority"],
        "status": "未着手",
        "progress": 0,
        "start_date": start_date,
        "due_date": inquiry.get("due_date") or "",
        "completed_date": "",
        "summary": inquiry["description"],
        "action_plan": "",
        "notes": "",
    }
    errors = validate_case(payload, strict_dates=False)
    if errors:
        raise ValueError("\n".join(errors))

    conn = get_connection(db_path)
    try:
        if get_case_by_inquiry_id(inquiry["inquiry_id"], conn=conn) is not None:
            raise ValueError("この問い合わせは案件化済みです。")

        case_id = generate_case_id(start_date, conn=conn)
        conn.execute(
            """
            INSERT INTO cases (
                case_id,
                inquiry_id,
                case_name,
                customer_name,
                assignee,
                sub_assignee,
                priority,
                status,
                progress,
                start_date,
                due_date,
                completed_date,
                summary,
                action_plan,
                notes,
                created_at,
                updated_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                case_id,
                inquiry["inquiry_id"],
                _text(payload["case_name"]),
                _text(payload["customer_name"]),
                _text(payload["assignee"]) or UNASSIGNED_ASSIGNEE,
                "",
                _text(payload["priority"]),
                "未着手",
                0,
                _date_text(start_date),
                _date_text(payload.get("due_date")),
                "",
                _text(payload["summary"]),
                "",
                "",
                timestamp,
                timestamp,
            ),
        )
        conn.commit()
        return case_id
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def _apply_completion_rules(payload, today):
    """完了ステータスに応じて進捗率と完了日を補正する。"""
    adjusted = dict(payload)
    status = _text(adjusted.get("status"))
    current_day = today if today is not None else date.today()
    if status == CASE_COMPLETED_STATUS:
        adjusted["progress"] = 100
        if parse_date(adjusted.get("completed_date")) is None:
            adjusted["completed_date"] = current_day
    else:
        adjusted["completed_date"] = ""
    return adjusted


def update_case(case_id, data, db_path=None, today=None, now=None):
    """案件を更新し、案件IDを返す。存在しない場合は None。"""
    existing = get_case_by_id(case_id, db_path=db_path)
    if existing is None:
        return None

    payload = _apply_completion_rules(dict(data or {}), today)
    errors = validate_case(payload)
    if errors:
        raise ValueError("\n".join(errors))

    timestamp = (now or datetime.now()).strftime("%Y-%m-%d %H:%M:%S")
    progress = parse_progress(payload.get("progress"))
    assignee = _text(payload.get("assignee")) or UNASSIGNED_ASSIGNEE

    conn = get_connection(db_path)
    try:
        conn.execute(
            """
            UPDATE cases
            SET
                case_name = ?,
                customer_name = ?,
                assignee = ?,
                sub_assignee = ?,
                priority = ?,
                status = ?,
                progress = ?,
                start_date = ?,
                due_date = ?,
                completed_date = ?,
                summary = ?,
                action_plan = ?,
                notes = ?,
                updated_at = ?
            WHERE case_id = ?
            """,
            (
                _text(payload.get("case_name")),
                _text(payload.get("customer_name")),
                assignee,
                _text(payload.get("sub_assignee")),
                _text(payload.get("priority")),
                _text(payload.get("status")),
                progress,
                _date_text(payload.get("start_date")),
                _date_text(payload.get("due_date")),
                _date_text(payload.get("completed_date")),
                _text(payload.get("summary")),
                _text(payload.get("action_plan")),
                _text(payload.get("notes")),
                timestamp,
                existing["case_id"],
            ),
        )
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()

    return existing["case_id"]
