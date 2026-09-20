"""問い合わせのID採番、登録、一覧検索。"""

from datetime import date, datetime, time

from common.db import get_connection
from common.models import UNASSIGNED_ASSIGNEE
from common.validators import parse_date, validate_inquiry

COMPLETED_STATUS = "完了"
FREEWORD_COLUMNS = (
    "inquiry_id",
    "customer_name",
    "company_name",
    "subject",
    "description",
    "phone",
    "email",
)


def _text(value):
    if value is None:
        return ""
    return str(value).strip()


def _date_text(value):
    parsed = parse_date(value)
    return parsed.isoformat() if parsed is not None else ""


def _time_text(value):
    if value is None or value == "":
        return ""
    if isinstance(value, datetime):
        return value.strftime("%H:%M:%S")
    if isinstance(value, time):
        return value.strftime("%H:%M:%S")
    return str(value).strip()


def _year_month(received_date):
    parsed = parse_date(received_date)
    if parsed is None:
        raise ValueError("受付日が指定されていません。")
    return parsed.strftime("%Y%m")


def generate_inquiry_id(received_date, db_path=None, conn=None):
    """受付年月単位で次の問い合わせID（INQ-YYYYMM-0001）を返す。"""
    year_month = _year_month(received_date)
    prefix = f"INQ-{year_month}-"

    should_close = conn is None
    if conn is None:
        conn = get_connection(db_path)
    try:
        rows = conn.execute(
            "SELECT inquiry_id FROM inquiries WHERE inquiry_id LIKE ?",
            (f"{prefix}%",),
        ).fetchall()
        max_number = 0
        for row in rows:
            suffix = row["inquiry_id"][len(prefix) :]
            if suffix.isdigit():
                max_number = max(max_number, int(suffix))
        return f"{prefix}{max_number + 1:04d}"
    finally:
        if should_close:
            conn.close()


def create_inquiry(data, db_path=None):
    """バリデーション後に問い合わせを登録し、問い合わせIDを返す。"""
    errors = validate_inquiry(data)
    if errors:
        raise ValueError("\n".join(errors))

    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    received_date = _date_text(data.get("received_date"))
    assignee = _text(data.get("assignee")) or UNASSIGNED_ASSIGNEE

    conn = get_connection(db_path)
    try:
        inquiry_id = generate_inquiry_id(received_date, conn=conn)
        conn.execute(
            """
            INSERT INTO inquiries (
                inquiry_id,
                received_date,
                received_time,
                customer_name,
                company_name,
                phone,
                email,
                channel,
                category,
                subject,
                description,
                priority,
                assignee,
                due_date,
                status,
                notes,
                created_at,
                updated_at
            ) VALUES (
                ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?
            )
            """,
            (
                inquiry_id,
                received_date,
                _time_text(data.get("received_time")),
                _text(data.get("customer_name")),
                _text(data.get("company_name")),
                _text(data.get("phone")),
                _text(data.get("email")),
                _text(data.get("channel")),
                _text(data.get("category")),
                _text(data.get("subject")),
                _text(data.get("description")),
                _text(data.get("priority")),
                assignee,
                _date_text(data.get("due_date")),
                _text(data.get("status")),
                _text(data.get("notes")),
                now,
                now,
            ),
        )
        conn.commit()
        return inquiry_id
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def is_overdue(due_date, status, today=None):
    """対応期限切れかつ未完了なら True。期限未設定は False。"""
    parsed_due = parse_date(due_date)
    if parsed_due is None:
        return False
    if _text(status) == COMPLETED_STATUS:
        return False
    current_day = today if today is not None else date.today()
    return parsed_due < current_day


def count_inquiries(db_path=None):
    """登録済み問い合わせの総件数を返す。"""
    conn = get_connection(db_path)
    try:
        return conn.execute("SELECT COUNT(*) AS n FROM inquiries").fetchone()["n"]
    finally:
        conn.close()


def get_inquiries(db_path=None, today=None):
    """全件を受付日降順で返す。"""
    return search_inquiries(db_path=db_path, today=today)


def search_inquiries(filters=None, db_path=None, today=None):
    """条件で問い合わせを検索し、overdue フラグを付与して返す。"""
    filters = filters or {}
    current_day = today if today is not None else date.today()
    conditions = []
    params = []

    keyword = _text(filters.get("keyword"))
    if keyword:
        like = f"%{keyword}%"
        placeholders = " OR ".join(f"{column} LIKE ?" for column in FREEWORD_COLUMNS)
        conditions.append(f"({placeholders})")
        params.extend([like] * len(FREEWORD_COLUMNS))

    customer_name = _text(filters.get("customer_name"))
    if customer_name:
        conditions.append("customer_name LIKE ?")
        params.append(f"%{customer_name}%")

    date_from = _date_text(filters.get("received_date_from"))
    if date_from:
        conditions.append("received_date >= ?")
        params.append(date_from)

    date_to = _date_text(filters.get("received_date_to"))
    if date_to:
        conditions.append("received_date <= ?")
        params.append(date_to)

    for column, key in (
        ("category", "categories"),
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
        FROM inquiries
        {where_sql}
        ORDER BY received_date DESC, received_time DESC, inquiry_id DESC
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


def get_inquiry_by_id(inquiry_id, db_path=None, today=None):
    """問い合わせIDで1件取得する。存在しない場合は None。"""
    current_id = _text(inquiry_id)
    if not current_id:
        return None

    conn = get_connection(db_path)
    try:
        row = conn.execute(
            "SELECT * FROM inquiries WHERE inquiry_id = ?",
            (current_id,),
        ).fetchone()
    finally:
        conn.close()

    if row is None:
        return None

    item = dict(row)
    item["overdue"] = is_overdue(item.get("due_date"), item.get("status"), today=today)
    return item


def update_inquiry(inquiry_id, data, db_path=None, now=None):
    """問い合わせを更新し、問い合わせIDを返す。存在しない場合は None。"""
    existing = get_inquiry_by_id(inquiry_id, db_path=db_path)
    if existing is None:
        return None

    payload = dict(data or {})
    payload["received_date"] = existing["received_date"]
    errors = validate_inquiry(payload)
    if errors:
        raise ValueError("\n".join(errors))

    timestamp = (now or datetime.now()).strftime("%Y-%m-%d %H:%M:%S")
    assignee = _text(payload.get("assignee")) or UNASSIGNED_ASSIGNEE

    conn = get_connection(db_path)
    try:
        conn.execute(
            """
            UPDATE inquiries
            SET
                customer_name = ?,
                company_name = ?,
                phone = ?,
                email = ?,
                channel = ?,
                category = ?,
                subject = ?,
                description = ?,
                priority = ?,
                assignee = ?,
                due_date = ?,
                status = ?,
                notes = ?,
                updated_at = ?
            WHERE inquiry_id = ?
            """,
            (
                _text(payload.get("customer_name")),
                _text(payload.get("company_name")),
                _text(payload.get("phone")),
                _text(payload.get("email")),
                _text(payload.get("channel")),
                _text(payload.get("category")),
                _text(payload.get("subject")),
                _text(payload.get("description")),
                _text(payload.get("priority")),
                assignee,
                _date_text(payload.get("due_date")),
                _text(payload.get("status")),
                _text(payload.get("notes")),
                timestamp,
                existing["inquiry_id"],
            ),
        )
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()

    return existing["inquiry_id"]
