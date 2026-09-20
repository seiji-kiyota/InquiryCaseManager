"""ダッシュボード用のKPI・集計。"""

from common.case_service import get_cases
from common.db import get_connection
from common.inquiry_service import get_inquiries
from common.models import (
    ASSIGNEES,
    CASE_STATUSES,
    INQUIRY_STATUSES,
    INQUIRY_TARGET_TYPE,
    PRIORITIES,
    UNASSIGNED_ASSIGNEE,
)

COMPLETED_STATUS = "完了"


def _completion_rate(completed, total):
    if total == 0:
        return 0.0
    return round(completed / total * 100, 1)


def _count_by_key(rows, field, ordered_keys):
    counts = {key: 0 for key in ordered_keys}
    for row in rows:
        key = row.get(field)
        if key in counts:
            counts[key] += 1
    return counts


def get_inquiry_kpis(db_path=None, today=None):
    """問い合わせの主要KPIを返す。"""
    inquiries = get_inquiries(db_path=db_path, today=today)
    by_status = _count_by_key(inquiries, "status", INQUIRY_STATUSES)
    total = len(inquiries)
    completed = by_status["完了"]
    return {
        "total": total,
        "未対応": by_status["未対応"],
        "対応中": by_status["対応中"],
        "保留": by_status["保留"],
        "完了": completed,
        "completion_rate": _completion_rate(completed, total),
        "overdue": sum(1 for item in inquiries if item.get("overdue")),
    }


def get_case_kpis(db_path=None, today=None):
    """案件の主要KPIを返す。"""
    cases = get_cases(db_path=db_path, today=today)
    by_status = _count_by_key(cases, "status", CASE_STATUSES)
    total = len(cases)
    completed = by_status["完了"]
    return {
        "total": total,
        "未着手": by_status["未着手"],
        "対応中": by_status["対応中"],
        "保留": by_status["保留"],
        "完了": completed,
        "completion_rate": _completion_rate(completed, total),
        "overdue": sum(1 for item in cases if item.get("overdue")),
    }


def count_inquiries_by_status(db_path=None):
    """問い合わせをステータス別に集計する。"""
    return _count_by_key(get_inquiries(db_path=db_path), "status", INQUIRY_STATUSES)


def count_inquiries_by_priority(db_path=None):
    """問い合わせを優先度別に集計する。"""
    return _count_by_key(get_inquiries(db_path=db_path), "priority", PRIORITIES)


def count_inquiries_by_assignee(db_path=None):
    """問い合わせを担当者別に集計する。未割当も含む。"""
    counts = {name: 0 for name in ASSIGNEES}
    for item in get_inquiries(db_path=db_path):
        name = item.get("assignee") or UNASSIGNED_ASSIGNEE
        counts[name] = counts.get(name, 0) + 1
    return counts


def get_monthly_inquiry_counts(db_path=None):
    """受付日を YYYY-MM 単位で集計し、年月順で返す。"""
    months = {}
    for item in get_inquiries(db_path=db_path):
        received = item.get("received_date") or ""
        if len(received) >= 7:
            year_month = received[:7]
            months[year_month] = months.get(year_month, 0) + 1
    return [{"year_month": key, "count": months[key]} for key in sorted(months)]


def get_monthly_completion_counts(db_path=None):
    """問い合わせごとに最後の完了履歴月を1件として集計する。

    完了月は histories の new_status=完了 のうち
    最も新しい action_datetime の年月を採用する。
    完了履歴が無い問い合わせは集計しない。
    """
    conn = get_connection(db_path)
    try:
        rows = conn.execute(
            """
            SELECT substr(last_completed, 1, 7) AS year_month, COUNT(*) AS count
            FROM (
                SELECT target_id, MAX(action_datetime) AS last_completed
                FROM histories
                WHERE target_type = ?
                  AND new_status = ?
                GROUP BY target_id
            )
            GROUP BY year_month
            ORDER BY year_month
            """,
            (INQUIRY_TARGET_TYPE, COMPLETED_STATUS),
        ).fetchall()
    finally:
        conn.close()

    return [{"year_month": row["year_month"], "count": row["count"]} for row in rows]


def count_cases_by_status(db_path=None):
    """案件をステータス別に集計する。"""
    return _count_by_key(get_cases(db_path=db_path), "status", CASE_STATUSES)
