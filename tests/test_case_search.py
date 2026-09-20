from datetime import date, time

from common.case_service import create_case_from_inquiry, get_cases, search_cases
from common.db import init_db
from common.inquiry_service import create_inquiry, is_overdue


TODAY = date(2026, 9, 21)


def _inquiry(**overrides):
    payload = {
        "received_date": date(2026, 9, 10),
        "received_time": time(10, 0, 0),
        "customer_name": "山田太郎",
        "company_name": "株式会社サンプル",
        "phone": "03-1111-1111",
        "email": "taro@example.com",
        "channel": "電話",
        "category": "商品",
        "subject": "見積依頼",
        "description": "商品の見積をお願いします。",
        "priority": "高",
        "assignee": "山田",
        "due_date": date(2026, 9, 30),
        "status": "未対応",
        "notes": "",
    }
    payload.update(overrides)
    return payload


def _setup(tmp_path):
    db_path = tmp_path / "inquiry_case_manager.db"
    init_db(db_path)
    first_id = create_inquiry(_inquiry(), db_path=db_path)
    second_id = create_inquiry(
        _inquiry(
            customer_name="佐藤花子",
            subject="契約内容確認",
            description="契約書を確認します。",
            priority="中",
            assignee="佐藤",
            due_date=date(2026, 9, 20),
        ),
        db_path=db_path,
    )
    third_id = create_inquiry(
        _inquiry(
            customer_name="鈴木一郎",
            subject="修理完了報告",
            description="修理が完了しました。",
            priority="低",
            assignee="鈴木",
            due_date=None,
        ),
        db_path=db_path,
    )
    create_case_from_inquiry(first_id, db_path=db_path, today=date(2026, 9, 21))
    create_case_from_inquiry(second_id, db_path=db_path, today=date(2026, 9, 20))
    create_case_from_inquiry(third_id, db_path=db_path, today=date(2026, 9, 19))
    return db_path


def test_get_all_cases(tmp_path):
    db_path = _setup(tmp_path)

    rows = get_cases(db_path=db_path, today=TODAY)

    assert len(rows) == 3


def test_freeword_search(tmp_path):
    db_path = _setup(tmp_path)

    rows = search_cases({"keyword": "見積"}, db_path=db_path, today=TODAY)

    assert [row["case_id"] for row in rows] == ["CASE-202609-0001"]


def test_filter_by_assignee(tmp_path):
    db_path = _setup(tmp_path)

    rows = search_cases({"assignees": ["佐藤"]}, db_path=db_path, today=TODAY)

    assert [row["assignee"] for row in rows] == ["佐藤"]


def test_filter_by_priority(tmp_path):
    db_path = _setup(tmp_path)

    rows = search_cases({"priorities": ["高"]}, db_path=db_path, today=TODAY)

    assert [row["priority"] for row in rows] == ["高"]


def test_filter_by_status(tmp_path):
    db_path = _setup(tmp_path)

    rows = search_cases({"statuses": ["未着手"]}, db_path=db_path, today=TODAY)

    assert len(rows) == 3


def test_overdue_when_due_date_before_today():
    assert is_overdue(date(2026, 9, 20), "未着手", today=TODAY) is True


def test_completed_case_is_not_overdue():
    assert is_overdue(date(2026, 9, 10), "完了", today=TODAY) is False


def test_missing_due_date_is_not_overdue():
    assert is_overdue(None, "未着手", today=TODAY) is False
    assert is_overdue("", "対応中", today=TODAY) is False
