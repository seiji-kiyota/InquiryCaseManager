from datetime import date, datetime, time

from common.case_service import create_case_from_inquiry, update_case
from common.dashboard_service import (
    count_cases_by_status,
    count_inquiries_by_assignee,
    count_inquiries_by_priority,
    count_inquiries_by_status,
    get_case_kpis,
    get_inquiry_kpis,
    get_monthly_completion_counts,
    get_monthly_inquiry_counts,
)
from common.db import init_db
from common.history_service import create_history
from common.inquiry_service import create_inquiry
from common.models import INQUIRY_TARGET_TYPE, STATUS_CHANGE_ACTION_TYPE


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
    return db_path


def _add_completion_history(db_path, inquiry_id, action_datetime, operator="山田"):
    return create_history(
        {
            "target_type": INQUIRY_TARGET_TYPE,
            "target_id": inquiry_id,
            "action_datetime": action_datetime,
            "operator": operator,
            "action_type": STATUS_CHANGE_ACTION_TYPE,
            "action_detail": "ステータスを完了に変更しました。",
            "old_status": "対応中",
            "new_status": "完了",
        },
        db_path=db_path,
        now=action_datetime,
    )


def _case_update(**overrides):
    payload = {
        "case_name": "見積依頼",
        "customer_name": "山田太郎",
        "assignee": "山田",
        "sub_assignee": "",
        "priority": "高",
        "status": "未着手",
        "progress": 0,
        "start_date": TODAY,
        "due_date": date(2026, 9, 30),
        "completed_date": None,
        "summary": "商品の見積をお願いします。",
        "action_plan": "",
        "notes": "",
    }
    payload.update(overrides)
    return payload


def test_inquiry_kpis_are_zero_when_empty(tmp_path):
    db_path = _setup(tmp_path)

    kpis = get_inquiry_kpis(db_path=db_path, today=TODAY)

    assert kpis["total"] == 0
    assert kpis["未対応"] == 0
    assert kpis["対応中"] == 0
    assert kpis["保留"] == 0
    assert kpis["完了"] == 0
    assert kpis["completion_rate"] == 0.0
    assert kpis["overdue"] == 0


def test_inquiry_kpis_count_each_status(tmp_path):
    db_path = _setup(tmp_path)
    create_inquiry(_inquiry(status="未対応", subject="未対応1"), db_path=db_path)
    create_inquiry(_inquiry(status="未対応", subject="未対応2"), db_path=db_path)
    create_inquiry(_inquiry(status="対応中", subject="対応中1"), db_path=db_path)
    create_inquiry(_inquiry(status="保留", subject="保留1"), db_path=db_path)
    create_inquiry(_inquiry(status="完了", subject="完了1"), db_path=db_path)
    create_inquiry(_inquiry(status="完了", subject="完了2"), db_path=db_path)

    kpis = get_inquiry_kpis(db_path=db_path, today=TODAY)

    assert kpis["total"] == 6
    assert kpis["未対応"] == 2
    assert kpis["対応中"] == 1
    assert kpis["保留"] == 1
    assert kpis["完了"] == 2
    assert kpis["completion_rate"] == 33.3


def test_inquiry_overdue_count(tmp_path):
    db_path = _setup(tmp_path)
    create_inquiry(
        _inquiry(subject="超過", due_date=date(2026, 9, 10), status="未対応"),
        db_path=db_path,
    )
    create_inquiry(
        _inquiry(subject="期限内", due_date=date(2026, 9, 30), status="対応中"),
        db_path=db_path,
    )
    create_inquiry(
        _inquiry(subject="完了済み超過", due_date=date(2026, 9, 10), status="完了"),
        db_path=db_path,
    )
    create_inquiry(_inquiry(subject="期限なし", due_date="", status="保留"), db_path=db_path)

    kpis = get_inquiry_kpis(db_path=db_path, today=TODAY)

    assert kpis["overdue"] == 1


def test_case_kpis_are_zero_when_empty(tmp_path):
    db_path = _setup(tmp_path)

    kpis = get_case_kpis(db_path=db_path, today=TODAY)

    assert kpis["total"] == 0
    assert kpis["未着手"] == 0
    assert kpis["対応中"] == 0
    assert kpis["保留"] == 0
    assert kpis["完了"] == 0
    assert kpis["completion_rate"] == 0.0
    assert kpis["overdue"] == 0


def test_case_kpis_count_each_status_and_rate(tmp_path):
    db_path = _setup(tmp_path)
    case_ids = []
    for index, subject in enumerate(("案件A", "案件B", "案件C", "案件D"), start=1):
        inquiry_id = create_inquiry(
            _inquiry(subject=subject, customer_name=f"顧客{index}"),
            db_path=db_path,
        )
        case_ids.append(
            create_case_from_inquiry(inquiry_id, db_path=db_path, today=TODAY)
        )

    update_case(case_ids[1], _case_update(status="対応中", progress=40), db_path=db_path)
    update_case(case_ids[2], _case_update(status="保留", progress=20), db_path=db_path)
    update_case(case_ids[3], _case_update(status="完了"), db_path=db_path, today=TODAY)

    kpis = get_case_kpis(db_path=db_path, today=TODAY)

    assert kpis["total"] == 4
    assert kpis["未着手"] == 1
    assert kpis["対応中"] == 1
    assert kpis["保留"] == 1
    assert kpis["完了"] == 1
    assert kpis["completion_rate"] == 25.0


def test_case_overdue_count(tmp_path):
    db_path = _setup(tmp_path)
    overdue_inquiry = create_inquiry(
        _inquiry(subject="期限超過案件", due_date=date(2026, 9, 10)),
        db_path=db_path,
    )
    open_inquiry = create_inquiry(
        _inquiry(subject="期限内案件", due_date=date(2026, 9, 30)),
        db_path=db_path,
    )
    completed_inquiry = create_inquiry(
        _inquiry(subject="完了案件", due_date=date(2026, 9, 10)),
        db_path=db_path,
    )
    overdue_case_id = create_case_from_inquiry(
        overdue_inquiry, db_path=db_path, today=TODAY
    )
    create_case_from_inquiry(open_inquiry, db_path=db_path, today=TODAY)
    completed_case_id = create_case_from_inquiry(
        completed_inquiry, db_path=db_path, today=TODAY
    )
    update_case(
        completed_case_id,
        _case_update(status="完了"),
        db_path=db_path,
        today=TODAY,
    )

    kpis = get_case_kpis(db_path=db_path, today=TODAY)

    assert overdue_case_id is not None
    assert kpis["overdue"] == 1


def test_inquiry_status_counts(tmp_path):
    db_path = _setup(tmp_path)
    create_inquiry(_inquiry(status="未対応", subject="A"), db_path=db_path)
    create_inquiry(_inquiry(status="対応中", subject="B"), db_path=db_path)
    create_inquiry(_inquiry(status="対応中", subject="C"), db_path=db_path)
    create_inquiry(_inquiry(status="保留", subject="D"), db_path=db_path)
    create_inquiry(_inquiry(status="完了", subject="E"), db_path=db_path)

    counts = count_inquiries_by_status(db_path=db_path)

    assert counts == {"未対応": 1, "対応中": 2, "保留": 1, "完了": 1}


def test_inquiry_priority_counts(tmp_path):
    db_path = _setup(tmp_path)
    create_inquiry(_inquiry(priority="低", subject="低"), db_path=db_path)
    create_inquiry(_inquiry(priority="中", subject="中1"), db_path=db_path)
    create_inquiry(_inquiry(priority="中", subject="中2"), db_path=db_path)
    create_inquiry(_inquiry(priority="高", subject="高"), db_path=db_path)
    create_inquiry(_inquiry(priority="緊急", subject="緊急"), db_path=db_path)

    counts = count_inquiries_by_priority(db_path=db_path)

    assert counts == {"低": 1, "中": 2, "高": 1, "緊急": 1}


def test_inquiry_assignee_counts_include_unassigned(tmp_path):
    db_path = _setup(tmp_path)
    create_inquiry(_inquiry(assignee="山田", subject="山田担当"), db_path=db_path)
    create_inquiry(_inquiry(assignee="山田", subject="山田担当2"), db_path=db_path)
    create_inquiry(_inquiry(assignee="佐藤", subject="佐藤担当"), db_path=db_path)
    create_inquiry(_inquiry(assignee="未割当", subject="未割当1"), db_path=db_path)
    create_inquiry(_inquiry(assignee="", subject="未割当2"), db_path=db_path)

    counts = count_inquiries_by_assignee(db_path=db_path)

    assert counts["山田"] == 2
    assert counts["佐藤"] == 1
    assert counts["未割当"] == 2
    assert counts["鈴木"] == 0


def test_monthly_inquiry_counts_and_order(tmp_path):
    db_path = _setup(tmp_path)
    create_inquiry(
        _inquiry(received_date=date(2026, 9, 10), subject="9月1"),
        db_path=db_path,
    )
    create_inquiry(
        _inquiry(received_date=date(2026, 7, 5), due_date=date(2026, 7, 20), subject="7月"),
        db_path=db_path,
    )
    create_inquiry(
        _inquiry(received_date=date(2026, 8, 12), due_date=date(2026, 8, 30), subject="8月"),
        db_path=db_path,
    )
    create_inquiry(
        _inquiry(received_date=date(2026, 9, 18), subject="9月2"),
        db_path=db_path,
    )

    rows = get_monthly_inquiry_counts(db_path=db_path)

    assert [row["year_month"] for row in rows] == ["2026-07", "2026-08", "2026-09"]
    assert [row["count"] for row in rows] == [1, 1, 2]


def test_case_status_counts(tmp_path):
    db_path = _setup(tmp_path)
    case_ids = []
    for index, subject in enumerate(("A", "B", "C", "D"), start=1):
        inquiry_id = create_inquiry(
            _inquiry(subject=subject, customer_name=f"顧客{index}"),
            db_path=db_path,
        )
        case_ids.append(create_case_from_inquiry(inquiry_id, db_path=db_path, today=TODAY))

    update_case(case_ids[1], _case_update(status="対応中", progress=50), db_path=db_path)
    update_case(case_ids[2], _case_update(status="保留", progress=10), db_path=db_path)
    update_case(case_ids[3], _case_update(status="完了"), db_path=db_path, today=TODAY)

    counts = count_cases_by_status(db_path=db_path)

    assert counts == {"未着手": 1, "対応中": 1, "保留": 1, "完了": 1}


def test_monthly_completion_uses_last_history_month(tmp_path):
    db_path = _setup(tmp_path)
    completed_id = create_inquiry(_inquiry(status="完了", subject="完了1"), db_path=db_path)
    reopened_id = create_inquiry(_inquiry(status="完了", subject="再完了"), db_path=db_path)
    open_id = create_inquiry(_inquiry(status="対応中", subject="未完了"), db_path=db_path)

    _add_completion_history(db_path, completed_id, datetime(2026, 8, 20, 10, 0, 0))
    _add_completion_history(db_path, reopened_id, datetime(2026, 7, 10, 9, 0, 0))
    _add_completion_history(db_path, reopened_id, datetime(2026, 9, 5, 15, 30, 0))

    rows = get_monthly_completion_counts(db_path=db_path)

    assert open_id is not None
    assert rows == [
        {"year_month": "2026-08", "count": 1},
        {"year_month": "2026-09", "count": 1},
    ]


def test_monthly_completion_excludes_never_completed(tmp_path):
    db_path = _setup(tmp_path)
    create_inquiry(_inquiry(status="未対応", subject="未完了"), db_path=db_path)
    create_history(
        {
            "target_type": INQUIRY_TARGET_TYPE,
            "target_id": create_inquiry(
                _inquiry(status="対応中", subject="再開のみ"),
                db_path=db_path,
            ),
            "action_datetime": datetime(2026, 8, 1, 10, 0, 0),
            "operator": "山田",
            "action_type": STATUS_CHANGE_ACTION_TYPE,
            "action_detail": "対応中に変更しました。",
            "old_status": "未対応",
            "new_status": "対応中",
        },
        db_path=db_path,
    )

    assert get_monthly_completion_counts(db_path=db_path) == []


def test_inquiry_total_matches_status_sum(tmp_path):
    db_path = _setup(tmp_path)
    create_inquiry(_inquiry(status="未対応", subject="A"), db_path=db_path)
    create_inquiry(_inquiry(status="対応中", subject="B"), db_path=db_path)
    create_inquiry(_inquiry(status="保留", subject="C"), db_path=db_path)
    create_inquiry(_inquiry(status="完了", subject="D"), db_path=db_path)

    kpis = get_inquiry_kpis(db_path=db_path, today=TODAY)
    counts = count_inquiries_by_status(db_path=db_path)

    assert kpis["total"] == sum(counts.values())


def test_case_total_matches_status_sum(tmp_path):
    db_path = _setup(tmp_path)
    for index, subject in enumerate(("A", "B", "C"), start=1):
        inquiry_id = create_inquiry(
            _inquiry(subject=subject, customer_name=f"顧客{index}"),
            db_path=db_path,
        )
        create_case_from_inquiry(inquiry_id, db_path=db_path, today=TODAY)

    kpis = get_case_kpis(db_path=db_path, today=TODAY)
    counts = count_cases_by_status(db_path=db_path)

    assert kpis["total"] == sum(counts.values()) == 3
