from datetime import date, datetime, time

import pytest

from common.db import init_db
from common.inquiry_service import create_inquiry, get_inquiry_by_id, update_inquiry


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


def _update_payload(**overrides):
    payload = {
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


def _create(tmp_path, **overrides):
    db_path = tmp_path / "inquiry_case_manager.db"
    init_db(db_path)
    inquiry_id = create_inquiry(_valid_inquiry(**overrides), db_path=db_path)
    return db_path, inquiry_id


def test_get_inquiry_by_id(tmp_path):
    db_path, inquiry_id = _create(tmp_path)

    row = get_inquiry_by_id(inquiry_id, db_path=db_path)

    assert row is not None
    assert row["inquiry_id"] == "INQ-202609-0001"
    assert row["customer_name"] == "山田太郎"
    assert row["subject"] == "見積依頼"


def test_get_inquiry_by_id_returns_none_when_missing(tmp_path):
    db_path, _inquiry_id = _create(tmp_path)

    row = get_inquiry_by_id("INQ-202609-9999", db_path=db_path)

    assert row is None


def test_update_customer_name(tmp_path):
    db_path, inquiry_id = _create(tmp_path)

    update_inquiry(inquiry_id, _update_payload(customer_name="佐藤花子"), db_path=db_path)

    assert get_inquiry_by_id(inquiry_id, db_path=db_path)["customer_name"] == "佐藤花子"


def test_update_subject(tmp_path):
    db_path, inquiry_id = _create(tmp_path)

    update_inquiry(inquiry_id, _update_payload(subject="納期確認"), db_path=db_path)

    assert get_inquiry_by_id(inquiry_id, db_path=db_path)["subject"] == "納期確認"


def test_update_description(tmp_path):
    db_path, inquiry_id = _create(tmp_path)

    update_inquiry(
        inquiry_id,
        _update_payload(description="納期を教えてください。"),
        db_path=db_path,
    )

    assert get_inquiry_by_id(inquiry_id, db_path=db_path)["description"] == "納期を教えてください。"


def test_update_assignee(tmp_path):
    db_path, inquiry_id = _create(tmp_path)

    update_inquiry(inquiry_id, _update_payload(assignee="鈴木"), db_path=db_path)

    assert get_inquiry_by_id(inquiry_id, db_path=db_path)["assignee"] == "鈴木"


def test_update_priority(tmp_path):
    db_path, inquiry_id = _create(tmp_path)

    update_inquiry(inquiry_id, _update_payload(priority="緊急"), db_path=db_path)

    assert get_inquiry_by_id(inquiry_id, db_path=db_path)["priority"] == "緊急"


def test_update_status(tmp_path):
    db_path, inquiry_id = _create(tmp_path)

    update_inquiry(inquiry_id, _update_payload(status="対応中"), db_path=db_path)

    assert get_inquiry_by_id(inquiry_id, db_path=db_path)["status"] == "対応中"


def test_update_due_date(tmp_path):
    db_path, inquiry_id = _create(tmp_path)

    update_inquiry(inquiry_id, _update_payload(due_date=date(2026, 10, 5)), db_path=db_path)

    assert get_inquiry_by_id(inquiry_id, db_path=db_path)["due_date"] == "2026-10-05"


def test_update_optional_fields_to_empty(tmp_path):
    db_path, inquiry_id = _create(tmp_path)

    update_inquiry(
        inquiry_id,
        _update_payload(
            company_name="",
            phone="",
            email="",
            due_date=None,
            notes="",
            assignee="未割当",
        ),
        db_path=db_path,
    )

    row = get_inquiry_by_id(inquiry_id, db_path=db_path)
    assert row["company_name"] == ""
    assert row["phone"] == ""
    assert row["email"] == ""
    assert row["due_date"] == ""
    assert row["notes"] == ""
    assert row["assignee"] == "未割当"


def test_update_changes_updated_at(tmp_path):
    db_path, inquiry_id = _create(tmp_path)
    before = get_inquiry_by_id(inquiry_id, db_path=db_path)

    update_inquiry(
        inquiry_id,
        _update_payload(status="対応中"),
        db_path=db_path,
        now=datetime(2026, 9, 21, 18, 0, 0),
    )

    after = get_inquiry_by_id(inquiry_id, db_path=db_path)
    assert after["updated_at"] == "2026-09-21 18:00:00"
    assert after["updated_at"] != before["updated_at"]


def test_update_keeps_created_at(tmp_path):
    db_path, inquiry_id = _create(tmp_path)
    before = get_inquiry_by_id(inquiry_id, db_path=db_path)

    update_inquiry(
        inquiry_id,
        _update_payload(status="対応中"),
        db_path=db_path,
        now=datetime(2026, 9, 21, 18, 0, 0),
    )

    after = get_inquiry_by_id(inquiry_id, db_path=db_path)
    assert after["created_at"] == before["created_at"]


def test_update_keeps_inquiry_id(tmp_path):
    db_path, inquiry_id = _create(tmp_path)

    updated_id = update_inquiry(inquiry_id, _update_payload(status="対応中"), db_path=db_path)

    assert updated_id == "INQ-202609-0001"
    assert get_inquiry_by_id(inquiry_id, db_path=db_path)["inquiry_id"] == "INQ-202609-0001"


def test_update_rejects_invalid_email(tmp_path):
    db_path, inquiry_id = _create(tmp_path)

    with pytest.raises(ValueError, match="メールアドレス"):
        update_inquiry(inquiry_id, _update_payload(email="invalid-email"), db_path=db_path)

    assert get_inquiry_by_id(inquiry_id, db_path=db_path)["email"] == "taro@example.com"


def test_update_rejects_empty_required_fields(tmp_path):
    db_path, inquiry_id = _create(tmp_path)

    with pytest.raises(ValueError, match="顧客名"):
        update_inquiry(inquiry_id, _update_payload(customer_name=""), db_path=db_path)

    assert get_inquiry_by_id(inquiry_id, db_path=db_path)["customer_name"] == "山田太郎"


def test_update_rejects_due_date_before_received_date(tmp_path):
    db_path, inquiry_id = _create(tmp_path)

    with pytest.raises(ValueError, match="対応期限"):
        update_inquiry(
            inquiry_id,
            _update_payload(due_date=date(2026, 9, 20)),
            db_path=db_path,
        )

    assert get_inquiry_by_id(inquiry_id, db_path=db_path)["due_date"] == "2026-09-30"


def test_update_missing_id_returns_none(tmp_path):
    db_path, _inquiry_id = _create(tmp_path)

    result = update_inquiry("INQ-202609-9999", _update_payload(), db_path=db_path)

    assert result is None
