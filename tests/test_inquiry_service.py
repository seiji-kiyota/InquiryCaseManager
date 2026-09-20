from datetime import date, time

from common.db import get_connection, init_db
from common.inquiry_service import create_inquiry, generate_inquiry_id


def _valid_inquiry(**overrides):
    payload = {
        "received_date": date(2026, 9, 21),
        "received_time": time(9, 30, 0),
        "customer_name": "山田太郎",
        "company_name": "株式会社サンプル",
        "phone": "03-1234-5678",
        "email": "taro@example.com",
        "channel": "電話",
        "category": "商品",
        "subject": "見積依頼",
        "description": "商品の見積をお願いします。",
        "priority": "中",
        "assignee": "山田",
        "due_date": date(2026, 9, 30),
        "status": "未対応",
        "notes": "午前中希望",
    }
    payload.update(overrides)
    return payload


def test_generate_inquiry_id_starts_from_0001(tmp_path):
    db_path = tmp_path / "inquiry_case_manager.db"
    init_db(db_path)

    inquiry_id = generate_inquiry_id(date(2026, 9, 21), db_path=db_path)

    assert inquiry_id == "INQ-202609-0001"


def test_generate_inquiry_id_increments_in_same_month(tmp_path):
    db_path = tmp_path / "inquiry_case_manager.db"
    init_db(db_path)
    create_inquiry(_valid_inquiry(), db_path=db_path)

    inquiry_id = generate_inquiry_id(date(2026, 9, 22), db_path=db_path)

    assert inquiry_id == "INQ-202609-0002"


def test_generate_inquiry_id_resets_in_new_month(tmp_path):
    db_path = tmp_path / "inquiry_case_manager.db"
    init_db(db_path)
    create_inquiry(_valid_inquiry(received_date=date(2026, 9, 21)), db_path=db_path)

    inquiry_id = generate_inquiry_id(date(2026, 10, 1), db_path=db_path)

    assert inquiry_id == "INQ-202610-0001"


def test_create_inquiry_saves_valid_data(tmp_path):
    db_path = tmp_path / "inquiry_case_manager.db"
    init_db(db_path)
    payload = _valid_inquiry()

    inquiry_id = create_inquiry(payload, db_path=db_path)

    assert inquiry_id == "INQ-202609-0001"

    conn = get_connection(db_path)
    try:
        row = conn.execute(
            "SELECT * FROM inquiries WHERE inquiry_id = ?",
            (inquiry_id,),
        ).fetchone()
    finally:
        conn.close()

    assert row is not None
    assert row["inquiry_id"] == "INQ-202609-0001"
    assert row["received_date"] == "2026-09-21"
    assert row["received_time"] == "09:30:00"
    assert row["customer_name"] == "山田太郎"
    assert row["company_name"] == "株式会社サンプル"
    assert row["phone"] == "03-1234-5678"
    assert row["email"] == "taro@example.com"
    assert row["channel"] == "電話"
    assert row["category"] == "商品"
    assert row["subject"] == "見積依頼"
    assert row["description"] == "商品の見積をお願いします。"
    assert row["priority"] == "中"
    assert row["assignee"] == "山田"
    assert row["due_date"] == "2026-09-30"
    assert row["status"] == "未対応"
    assert row["notes"] == "午前中希望"
    assert row["created_at"]
    assert row["updated_at"]
