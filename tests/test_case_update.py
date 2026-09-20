from datetime import date, datetime, time

from common.case_service import create_case_from_inquiry, get_case_by_id, update_case
from common.db import init_db
from common.inquiry_service import create_inquiry


def _inquiry():
    return {
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


def _update(**overrides):
    payload = {
        "case_name": "見積依頼",
        "customer_name": "山田太郎",
        "assignee": "山田",
        "sub_assignee": "",
        "priority": "高",
        "status": "未着手",
        "progress": 0,
        "start_date": date(2026, 9, 21),
        "due_date": date(2026, 9, 30),
        "completed_date": None,
        "summary": "商品の見積をお願いします。",
        "action_plan": "",
        "notes": "",
    }
    payload.update(overrides)
    return payload


def _setup(tmp_path):
    db_path = tmp_path / "inquiry_case_manager.db"
    init_db(db_path)
    inquiry_id = create_inquiry(_inquiry(), db_path=db_path)
    case_id = create_case_from_inquiry(inquiry_id, db_path=db_path, today=date(2026, 9, 21))
    return db_path, case_id


def test_update_case_name(tmp_path):
    db_path, case_id = _setup(tmp_path)

    update_case(case_id, _update(case_name="見積対応案件"), db_path=db_path)

    assert get_case_by_id(case_id, db_path=db_path)["case_name"] == "見積対応案件"


def test_update_assignee(tmp_path):
    db_path, case_id = _setup(tmp_path)

    update_case(case_id, _update(assignee="佐藤"), db_path=db_path)

    assert get_case_by_id(case_id, db_path=db_path)["assignee"] == "佐藤"


def test_update_sub_assignee(tmp_path):
    db_path, case_id = _setup(tmp_path)

    update_case(case_id, _update(sub_assignee="鈴木"), db_path=db_path)

    assert get_case_by_id(case_id, db_path=db_path)["sub_assignee"] == "鈴木"


def test_update_priority(tmp_path):
    db_path, case_id = _setup(tmp_path)

    update_case(case_id, _update(priority="緊急"), db_path=db_path)

    assert get_case_by_id(case_id, db_path=db_path)["priority"] == "緊急"


def test_update_status(tmp_path):
    db_path, case_id = _setup(tmp_path)

    update_case(case_id, _update(status="対応中", progress=20), db_path=db_path)

    assert get_case_by_id(case_id, db_path=db_path)["status"] == "対応中"


def test_update_progress(tmp_path):
    db_path, case_id = _setup(tmp_path)

    update_case(case_id, _update(status="対応中", progress=40), db_path=db_path)

    assert get_case_by_id(case_id, db_path=db_path)["progress"] == 40


def test_update_due_date(tmp_path):
    db_path, case_id = _setup(tmp_path)

    update_case(case_id, _update(due_date=date(2026, 10, 5)), db_path=db_path)

    assert get_case_by_id(case_id, db_path=db_path)["due_date"] == "2026-10-05"


def test_update_action_plan(tmp_path):
    db_path, case_id = _setup(tmp_path)

    update_case(case_id, _update(action_plan="見積を作成して送付する"), db_path=db_path)

    assert get_case_by_id(case_id, db_path=db_path)["action_plan"] == "見積を作成して送付する"


def test_update_changes_updated_at(tmp_path):
    db_path, case_id = _setup(tmp_path)
    before = get_case_by_id(case_id, db_path=db_path)

    update_case(
        case_id,
        _update(status="対応中", progress=10),
        db_path=db_path,
        now=datetime(2026, 9, 21, 18, 0, 0),
    )

    after = get_case_by_id(case_id, db_path=db_path)
    assert after["updated_at"] == "2026-09-21 18:00:00"
    assert after["updated_at"] != before["updated_at"]


def test_update_keeps_created_at(tmp_path):
    db_path, case_id = _setup(tmp_path)
    before = get_case_by_id(case_id, db_path=db_path)

    update_case(
        case_id,
        _update(status="対応中", progress=10),
        db_path=db_path,
        now=datetime(2026, 9, 21, 18, 0, 0),
    )

    assert get_case_by_id(case_id, db_path=db_path)["created_at"] == before["created_at"]


def test_update_keeps_case_id(tmp_path):
    db_path, case_id = _setup(tmp_path)

    updated_id = update_case(case_id, _update(status="対応中", progress=10), db_path=db_path)

    assert updated_id == case_id
    assert get_case_by_id(case_id, db_path=db_path)["case_id"] == "CASE-202609-0001"


def test_complete_sets_progress_to_100(tmp_path):
    db_path, case_id = _setup(tmp_path)

    update_case(
        case_id,
        _update(status="完了", progress=40),
        db_path=db_path,
        today=date(2026, 9, 21),
    )

    assert get_case_by_id(case_id, db_path=db_path)["progress"] == 100


def test_complete_sets_completed_date(tmp_path):
    db_path, case_id = _setup(tmp_path)

    update_case(
        case_id,
        _update(status="完了", progress=40, completed_date=None),
        db_path=db_path,
        today=date(2026, 9, 21),
    )

    assert get_case_by_id(case_id, db_path=db_path)["completed_date"] == "2026-09-21"


def test_uncomplete_clears_completed_date(tmp_path):
    db_path, case_id = _setup(tmp_path)
    update_case(
        case_id,
        _update(status="完了", progress=100),
        db_path=db_path,
        today=date(2026, 9, 21),
    )

    update_case(
        case_id,
        _update(status="対応中", progress=80, completed_date=date(2026, 9, 21)),
        db_path=db_path,
        today=date(2026, 9, 21),
    )

    row = get_case_by_id(case_id, db_path=db_path)
    assert row["status"] == "対応中"
    assert row["completed_date"] == ""
    assert row["progress"] == 80
