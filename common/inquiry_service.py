"""問い合わせのID採番と登録。"""

from datetime import datetime, time

from common.db import get_connection
from common.models import UNASSIGNED_ASSIGNEE
from common.validators import parse_date, validate_inquiry


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
