from datetime import date, time

from common.db import init_db
from common.inquiry_service import (
    create_inquiry,
    get_inquiries,
    is_overdue,
    search_inquiries,
)


TODAY = date(2026, 9, 21)


def _inquiry(**overrides):
    payload = {
        "received_date": date(2026, 9, 21),
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
        "due_date": date(2026, 9, 20),
        "status": "未対応",
        "notes": "",
    }
    payload.update(overrides)
    return payload


def _seed(db_path):
    init_db(db_path)
    create_inquiry(
        _inquiry(
            received_date=date(2026, 9, 10),
            received_time=time(10, 0, 0),
            customer_name="山田太郎",
            company_name="株式会社サンプル",
            phone="03-1111-1111",
            email="taro@example.com",
            category="商品",
            subject="見積依頼",
            description="商品の見積をお願いします。",
            priority="高",
            assignee="山田",
            due_date=date(2026, 9, 20),
            status="未対応",
        ),
        db_path=db_path,
    )
    create_inquiry(
        _inquiry(
            received_date=date(2026, 9, 21),
            received_time=time(16, 0, 0),
            customer_name="佐藤花子",
            company_name="佐藤商事",
            phone="06-2222-2222",
            email="hanako@sato.example",
            category="契約",
            subject="契約内容確認",
            description="契約書の条項を確認したいです。",
            priority="中",
            assignee="佐藤",
            due_date=date(2026, 9, 30),
            status="対応中",
        ),
        db_path=db_path,
    )
    create_inquiry(
        _inquiry(
            received_date=date(2026, 9, 21),
            received_time=time(9, 0, 0),
            customer_name="鈴木一郎",
            company_name="鈴木工業",
            phone="052-333-3333",
            email="ichiro@suzuki.example",
            category="修理",
            subject="修理完了報告",
            description="修理対応が完了しました。",
            priority="低",
            assignee="鈴木",
            due_date=date(2026, 9, 21),
            status="完了",
        ),
        db_path=db_path,
    )
    create_inquiry(
        _inquiry(
            received_date=date(2026, 8, 1),
            received_time=time(11, 0, 0),
            customer_name="山田太郎",
            company_name="株式会社サンプル",
            phone="03-1111-1111",
            email="taro@example.com",
            category="クレーム",
            subject="納期遅延",
            description="納期が遅れています。",
            priority="緊急",
            assignee="未割当",
            due_date=None,
            status="未対応",
        ),
        db_path=db_path,
    )


def _ids(rows):
    return [row["inquiry_id"] for row in rows]


def test_get_all_inquiries(tmp_path):
    db_path = tmp_path / "inquiry_case_manager.db"
    _seed(db_path)

    rows = get_inquiries(db_path=db_path, today=TODAY)

    assert len(rows) == 4


def test_order_by_received_date_desc(tmp_path):
    db_path = tmp_path / "inquiry_case_manager.db"
    _seed(db_path)

    rows = get_inquiries(db_path=db_path, today=TODAY)

    assert _ids(rows) == [
        "INQ-202609-0002",
        "INQ-202609-0003",
        "INQ-202609-0001",
        "INQ-202608-0001",
    ]
    assert rows[0]["received_time"] == "16:00:00"
    assert rows[1]["received_time"] == "09:00:00"


def test_freeword_search(tmp_path):
    db_path = tmp_path / "inquiry_case_manager.db"
    _seed(db_path)

    rows = search_inquiries({"keyword": "見積"}, db_path=db_path, today=TODAY)

    assert _ids(rows) == ["INQ-202609-0001"]


def test_customer_name_partial_match(tmp_path):
    db_path = tmp_path / "inquiry_case_manager.db"
    _seed(db_path)

    rows = search_inquiries({"customer_name": "山田"}, db_path=db_path, today=TODAY)

    assert _ids(rows) == ["INQ-202609-0001", "INQ-202608-0001"]


def test_filter_by_category(tmp_path):
    db_path = tmp_path / "inquiry_case_manager.db"
    _seed(db_path)

    rows = search_inquiries({"categories": ["契約"]}, db_path=db_path, today=TODAY)

    assert _ids(rows) == ["INQ-202609-0002"]


def test_filter_by_assignee(tmp_path):
    db_path = tmp_path / "inquiry_case_manager.db"
    _seed(db_path)

    rows = search_inquiries({"assignees": ["佐藤"]}, db_path=db_path, today=TODAY)

    assert _ids(rows) == ["INQ-202609-0002"]


def test_filter_by_priority(tmp_path):
    db_path = tmp_path / "inquiry_case_manager.db"
    _seed(db_path)

    rows = search_inquiries({"priorities": ["高", "緊急"]}, db_path=db_path, today=TODAY)

    assert _ids(rows) == ["INQ-202609-0001", "INQ-202608-0001"]


def test_filter_by_status(tmp_path):
    db_path = tmp_path / "inquiry_case_manager.db"
    _seed(db_path)

    rows = search_inquiries({"statuses": ["対応中"]}, db_path=db_path, today=TODAY)

    assert _ids(rows) == ["INQ-202609-0002"]


def test_filter_by_received_date_range(tmp_path):
    db_path = tmp_path / "inquiry_case_manager.db"
    _seed(db_path)

    rows = search_inquiries(
        {
            "received_date_from": date(2026, 9, 19),
            "received_date_to": date(2026, 9, 21),
        },
        db_path=db_path,
        today=TODAY,
    )

    assert _ids(rows) == ["INQ-202609-0002", "INQ-202609-0003"]


def test_overdue_when_due_date_before_today():
    assert is_overdue(date(2026, 9, 20), "未対応", today=TODAY) is True


def test_completed_is_not_overdue():
    assert is_overdue(date(2026, 9, 10), "完了", today=TODAY) is False


def test_missing_due_date_is_not_overdue():
    assert is_overdue(None, "未対応", today=TODAY) is False
    assert is_overdue("", "未対応", today=TODAY) is False


def test_overdue_only_filter(tmp_path):
    db_path = tmp_path / "inquiry_case_manager.db"
    _seed(db_path)

    rows = search_inquiries({"overdue_only": True}, db_path=db_path, today=TODAY)

    assert _ids(rows) == ["INQ-202609-0001"]
    assert rows[0]["overdue"] is True


def test_and_search_with_multiple_filters(tmp_path):
    db_path = tmp_path / "inquiry_case_manager.db"
    _seed(db_path)

    rows = search_inquiries(
        {
            "keyword": "山田",
            "categories": ["商品"],
            "statuses": ["未対応"],
            "priorities": ["高"],
        },
        db_path=db_path,
        today=TODAY,
    )

    assert _ids(rows) == ["INQ-202609-0001"]
