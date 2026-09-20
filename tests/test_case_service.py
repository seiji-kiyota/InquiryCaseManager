from datetime import date, time

import pytest

from common.case_service import (
    create_case_from_inquiry,
    generate_case_id,
    get_case_by_id,
    get_case_by_inquiry_id,
)
from common.db import init_db
from common.inquiry_service import create_inquiry


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


def _setup_inquiry(tmp_path, **overrides):
    db_path = tmp_path / "inquiry_case_manager.db"
    init_db(db_path)
    inquiry_id = create_inquiry(_inquiry(**overrides), db_path=db_path)
    return db_path, inquiry_id


def test_generate_case_id_starts_from_0001(tmp_path):
    db_path = tmp_path / "inquiry_case_manager.db"
    init_db(db_path)

    case_id = generate_case_id(date(2026, 9, 21), db_path=db_path)

    assert case_id == "CASE-202609-0001"


def test_generate_case_id_increments_in_same_month(tmp_path):
    db_path, inquiry_id = _setup_inquiry(tmp_path)
    create_case_from_inquiry(inquiry_id, db_path=db_path, today=date(2026, 9, 21))

    case_id = generate_case_id(date(2026, 9, 22), db_path=db_path)

    assert case_id == "CASE-202609-0002"


def test_generate_case_id_resets_in_new_month(tmp_path):
    db_path, inquiry_id = _setup_inquiry(tmp_path)
    create_case_from_inquiry(inquiry_id, db_path=db_path, today=date(2026, 9, 21))

    case_id = generate_case_id(date(2026, 10, 1), db_path=db_path)

    assert case_id == "CASE-202610-0001"


def test_create_case_from_inquiry(tmp_path):
    db_path, inquiry_id = _setup_inquiry(tmp_path)

    case_id = create_case_from_inquiry(inquiry_id, db_path=db_path, today=date(2026, 9, 21))

    assert case_id == "CASE-202609-0001"
    case = get_case_by_id(case_id, db_path=db_path)
    assert case["inquiry_id"] == inquiry_id
    assert case["customer_name"] == "山田太郎"
    assert case["case_name"] == "見積依頼"
    assert case["priority"] == "高"
    assert case["assignee"] == "山田"
    assert case["status"] == "未着手"
    assert case["progress"] == 0
    assert case["start_date"] == "2026-09-21"
    assert case["summary"] == "商品の見積をお願いします。"


def test_create_case_links_inquiry_id(tmp_path):
    db_path, inquiry_id = _setup_inquiry(tmp_path)

    case_id = create_case_from_inquiry(inquiry_id, db_path=db_path, today=date(2026, 9, 21))

    assert get_case_by_inquiry_id(inquiry_id, db_path=db_path)["case_id"] == case_id


def test_reject_duplicate_conversion(tmp_path):
    db_path, inquiry_id = _setup_inquiry(tmp_path)
    create_case_from_inquiry(inquiry_id, db_path=db_path, today=date(2026, 9, 21))

    with pytest.raises(ValueError, match="案件化済み"):
        create_case_from_inquiry(inquiry_id, db_path=db_path, today=date(2026, 9, 21))


def test_reject_missing_inquiry_conversion(tmp_path):
    db_path = tmp_path / "inquiry_case_manager.db"
    init_db(db_path)

    result = create_case_from_inquiry("INQ-202609-9999", db_path=db_path, today=date(2026, 9, 21))

    assert result is None
