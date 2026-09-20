import threading
from datetime import date

from common.case_service import count_cases, get_case_by_id, search_cases
from common.dashboard_service import (
    count_cases_by_status,
    count_inquiries_by_status,
    get_case_kpis,
    get_inquiry_kpis,
)
from common.db import get_connection, init_db
from common.demo_data import is_database_empty, seed_demo_data_if_empty
from common.history_service import get_histories_by_target
from common.inquiry_service import count_inquiries, create_inquiry, is_overdue, search_inquiries
from common.models import INQUIRY_TARGET_TYPE


TODAY = date(2026, 9, 21)


def _setup(tmp_path):
    db_path = tmp_path / "inquiry_case_manager.db"
    init_db(db_path)
    return db_path


def _history_count(db_path):
    conn = get_connection(db_path)
    try:
        return conn.execute("SELECT COUNT(*) AS n FROM histories").fetchone()["n"]
    finally:
        conn.close()


def test_empty_database_is_seeded(tmp_path):
    db_path = _setup(tmp_path)

    assert is_database_empty(db_path=db_path)
    assert seed_demo_data_if_empty(db_path=db_path, today=TODAY) is True
    assert count_inquiries(db_path=db_path) >= 10
    assert count_cases(db_path=db_path) >= 5
    assert _history_count(db_path) >= 5


def test_seed_is_not_duplicated(tmp_path):
    db_path = _setup(tmp_path)
    seed_demo_data_if_empty(db_path=db_path, today=TODAY)
    inquiries = count_inquiries(db_path=db_path)
    cases = count_cases(db_path=db_path)
    histories = _history_count(db_path)

    assert seed_demo_data_if_empty(db_path=db_path, today=TODAY) is False
    assert count_inquiries(db_path=db_path) == inquiries == 12
    assert count_cases(db_path=db_path) == cases == 8
    assert _history_count(db_path) == histories == 13


def test_concurrent_seed_runs_once(tmp_path):
    db_path = _setup(tmp_path)
    barrier = threading.Barrier(2)
    results = []
    errors = []

    def worker():
        try:
            barrier.wait(timeout=5)
            results.append(seed_demo_data_if_empty(db_path=db_path, today=TODAY))
        except Exception as error:
            errors.append(error)

    threads = [threading.Thread(target=worker) for _ in range(2)]
    for thread in threads:
        thread.start()
    for thread in threads:
        thread.join()

    assert errors == []
    assert results.count(True) == 1
    assert results.count(False) == 1
    assert count_inquiries(db_path=db_path) == 12
    assert count_cases(db_path=db_path) == 8
    assert _history_count(db_path) == 13


def test_existing_data_is_not_seeded(tmp_path):
    db_path = _setup(tmp_path)
    create_inquiry(
        {
            "received_date": TODAY,
            "received_time": "10:00:00",
            "customer_name": "既存顧客",
            "company_name": "",
            "phone": "",
            "email": "",
            "channel": "電話",
            "category": "商品",
            "subject": "既存データ",
            "description": "既存の問い合わせです。",
            "priority": "中",
            "assignee": "山田",
            "due_date": "",
            "status": "未対応",
            "notes": "",
        },
        db_path=db_path,
    )

    assert is_database_empty(db_path=db_path) is False
    assert seed_demo_data_if_empty(db_path=db_path, today=TODAY) is False
    assert count_inquiries(db_path=db_path) == 1
    assert count_cases(db_path=db_path) == 0


def test_seeded_cases_link_to_inquiries(tmp_path):
    db_path = _setup(tmp_path)
    seed_demo_data_if_empty(db_path=db_path, today=TODAY)

    for case in search_cases(db_path=db_path, today=TODAY):
        linked = get_case_by_id(case["case_id"], db_path=db_path)
        assert linked["inquiry_id"]
        assert any(
            item["inquiry_id"] == linked["inquiry_id"]
            for item in search_inquiries(db_path=db_path, today=TODAY)
        )


def test_seeded_data_has_completions_and_overdue(tmp_path):
    db_path = _setup(tmp_path)
    seed_demo_data_if_empty(db_path=db_path, today=TODAY)
    inquiries = search_inquiries(db_path=db_path, today=TODAY)
    cases = search_cases(db_path=db_path, today=TODAY)

    completion_histories = []
    for item in inquiries:
        for history in get_histories_by_target(
            INQUIRY_TARGET_TYPE, item["inquiry_id"], db_path=db_path
        ):
            if history.get("new_status") == "完了":
                completion_histories.append(history)

    assert completion_histories
    assert any(is_overdue(item["due_date"], item["status"], today=TODAY) for item in inquiries)
    assert any(case["overdue"] for case in cases)


def test_seeded_dashboard_aggregations(tmp_path):
    db_path = _setup(tmp_path)
    seed_demo_data_if_empty(db_path=db_path, today=TODAY)

    inquiry_kpis = get_inquiry_kpis(db_path=db_path, today=TODAY)
    case_kpis = get_case_kpis(db_path=db_path, today=TODAY)
    assert inquiry_kpis["total"] == sum(count_inquiries_by_status(db_path=db_path).values())
    assert case_kpis["total"] == sum(count_cases_by_status(db_path=db_path).values())
    assert inquiry_kpis["total"] > 0
    assert case_kpis["total"] > 0
    assert inquiry_kpis["overdue"] >= 1
    assert case_kpis["overdue"] >= 1
