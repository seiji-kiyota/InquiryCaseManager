from datetime import date, datetime, time

import pytest

from common.db import init_db
from common.history_service import get_histories_by_target
from common.inquiry_service import create_inquiry, get_inquiry_by_id, update_inquiry
from common.models import INQUIRY_TARGET_TYPE, STATUS_CHANGE_ACTION_TYPE


def _inquiry(**overrides):
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
        "notes": "",
    }
    payload.update(overrides)
    return payload


def _update(**overrides):
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
        "notes": "",
    }
    payload.update(overrides)
    return payload


def _setup(tmp_path):
    db_path = tmp_path / "inquiry_case_manager.db"
    init_db(db_path)
    inquiry_id = create_inquiry(_inquiry(), db_path=db_path)
    return db_path, inquiry_id


def test_status_change_creates_history(tmp_path):
    db_path, inquiry_id = _setup(tmp_path)

    update_inquiry(
        inquiry_id,
        _update(status="対応中"),
        db_path=db_path,
        now=datetime(2026, 9, 21, 11, 0, 0),
    )

    rows = get_histories_by_target(INQUIRY_TARGET_TYPE, inquiry_id, db_path=db_path)
    assert len(rows) == 1
    assert rows[0]["action_type"] == STATUS_CHANGE_ACTION_TYPE
    assert rows[0]["old_status"] == "未対応"
    assert rows[0]["new_status"] == "対応中"
    assert "未対応" in rows[0]["action_detail"]
    assert "対応中" in rows[0]["action_detail"]


def test_status_change_history_has_old_and_new_status(tmp_path):
    db_path, inquiry_id = _setup(tmp_path)

    update_inquiry(inquiry_id, _update(status="保留"), db_path=db_path)

    row = get_histories_by_target(INQUIRY_TARGET_TYPE, inquiry_id, db_path=db_path)[0]
    assert row["old_status"] == "未対応"
    assert row["new_status"] == "保留"


def test_no_history_when_status_unchanged(tmp_path):
    db_path, inquiry_id = _setup(tmp_path)

    update_inquiry(inquiry_id, _update(subject="件名変更"), db_path=db_path)

    rows = get_histories_by_target(INQUIRY_TARGET_TYPE, inquiry_id, db_path=db_path)
    assert rows == []
    assert get_inquiry_by_id(inquiry_id, db_path=db_path)["subject"] == "件名変更"


def test_multiple_status_changes_are_kept_in_order(tmp_path):
    db_path, inquiry_id = _setup(tmp_path)

    update_inquiry(
        inquiry_id,
        _update(status="対応中"),
        db_path=db_path,
        now=datetime(2026, 9, 21, 11, 0, 0),
    )
    update_inquiry(
        inquiry_id,
        _update(status="完了"),
        db_path=db_path,
        now=datetime(2026, 9, 21, 16, 0, 0),
    )

    rows = get_histories_by_target(INQUIRY_TARGET_TYPE, inquiry_id, db_path=db_path)
    assert [row["new_status"] for row in rows] == ["完了", "対応中"]
    assert [row["old_status"] for row in rows] == ["対応中", "未対応"]


def test_failed_update_does_not_create_history(tmp_path):
    db_path, inquiry_id = _setup(tmp_path)

    with pytest.raises(ValueError, match="メールアドレス"):
        update_inquiry(
            inquiry_id,
            _update(email="invalid-email", status="対応中"),
            db_path=db_path,
        )

    assert get_inquiry_by_id(inquiry_id, db_path=db_path)["status"] == "未対応"
    assert get_histories_by_target(INQUIRY_TARGET_TYPE, inquiry_id, db_path=db_path) == []
