from datetime import date, datetime, time

from common.db import init_db
from common.history_service import (
    create_history,
    generate_history_id,
    get_histories_by_target,
)
from common.inquiry_service import create_inquiry
from common.models import INQUIRY_TARGET_TYPE


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


def _history(target_id, **overrides):
    payload = {
        "target_type": INQUIRY_TARGET_TYPE,
        "target_id": target_id,
        "action_datetime": datetime(2026, 9, 21, 10, 0, 0),
        "operator": "山田",
        "action_type": "電話",
        "action_detail": "内容を確認しました。",
        "next_action_date": date(2026, 9, 25),
    }
    payload.update(overrides)
    return payload


def _setup(tmp_path):
    db_path = tmp_path / "inquiry_case_manager.db"
    init_db(db_path)
    inquiry_id = create_inquiry(_inquiry(), db_path=db_path)
    return db_path, inquiry_id


def test_generate_history_id_starts_from_000001(tmp_path):
    db_path = tmp_path / "inquiry_case_manager.db"
    init_db(db_path)

    history_id = generate_history_id(db_path=db_path)

    assert history_id == "HIS-000001"


def test_generate_history_id_increments(tmp_path):
    db_path, inquiry_id = _setup(tmp_path)
    create_history(_history(inquiry_id), db_path=db_path)

    history_id = generate_history_id(db_path=db_path)

    assert history_id == "HIS-000002"


def test_create_history(tmp_path):
    db_path, inquiry_id = _setup(tmp_path)

    history_id = create_history(_history(inquiry_id), db_path=db_path)

    assert history_id == "HIS-000001"


def test_get_histories_by_target(tmp_path):
    db_path, inquiry_id = _setup(tmp_path)
    create_history(_history(inquiry_id), db_path=db_path)

    rows = get_histories_by_target(INQUIRY_TARGET_TYPE, inquiry_id, db_path=db_path)

    assert len(rows) == 1
    assert rows[0]["history_id"] == "HIS-000001"
    assert rows[0]["action_type"] == "電話"
    assert rows[0]["action_detail"] == "内容を確認しました。"
    assert rows[0]["next_action_date"] == "2026-09-25"
    assert rows[0]["old_status"] == ""
    assert rows[0]["new_status"] == ""


def test_histories_are_ordered_newest_first(tmp_path):
    db_path, inquiry_id = _setup(tmp_path)
    create_history(
        _history(inquiry_id, action_datetime=datetime(2026, 9, 21, 10, 0, 0)),
        db_path=db_path,
        now=datetime(2026, 9, 21, 10, 0, 0),
    )
    create_history(
        _history(
            inquiry_id,
            action_datetime=datetime(2026, 9, 21, 15, 0, 0),
            action_detail="再確認しました。",
        ),
        db_path=db_path,
        now=datetime(2026, 9, 21, 15, 0, 0),
    )

    rows = get_histories_by_target(INQUIRY_TARGET_TYPE, inquiry_id, db_path=db_path)

    assert [row["action_datetime"] for row in rows] == [
        "2026-09-21 15:00:00",
        "2026-09-21 10:00:00",
    ]


def test_histories_are_separated_by_inquiry(tmp_path):
    db_path, first_id = _setup(tmp_path)
    second_id = create_inquiry(
        _inquiry(customer_name="佐藤花子", subject="契約確認"),
        db_path=db_path,
    )
    create_history(_history(first_id, action_detail="山田対応"), db_path=db_path)
    create_history(_history(second_id, action_detail="佐藤対応"), db_path=db_path)

    first_rows = get_histories_by_target(INQUIRY_TARGET_TYPE, first_id, db_path=db_path)
    second_rows = get_histories_by_target(INQUIRY_TARGET_TYPE, second_id, db_path=db_path)

    assert [row["action_detail"] for row in first_rows] == ["山田対応"]
    assert [row["action_detail"] for row in second_rows] == ["佐藤対応"]


def test_create_history_rejects_missing_inquiry(tmp_path):
    db_path = tmp_path / "inquiry_case_manager.db"
    init_db(db_path)

    result = create_history(_history("INQ-202609-9999"), db_path=db_path)

    assert result is None
    assert get_histories_by_target(INQUIRY_TARGET_TYPE, "INQ-202609-9999", db_path=db_path) == []
