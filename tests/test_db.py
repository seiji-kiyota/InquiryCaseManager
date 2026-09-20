from common.db import get_connection, init_db


INQUIRY_COLUMNS = {
    "inquiry_id",
    "received_date",
    "received_time",
    "customer_name",
    "company_name",
    "phone",
    "email",
    "channel",
    "category",
    "subject",
    "description",
    "priority",
    "assignee",
    "due_date",
    "status",
    "notes",
    "created_at",
    "updated_at",
}

CASE_COLUMNS = {
    "case_id",
    "inquiry_id",
    "case_name",
    "customer_name",
    "assignee",
    "sub_assignee",
    "priority",
    "status",
    "progress",
    "start_date",
    "due_date",
    "completed_date",
    "summary",
    "action_plan",
    "notes",
    "created_at",
    "updated_at",
}

HISTORY_COLUMNS = {
    "history_id",
    "target_type",
    "target_id",
    "action_datetime",
    "operator",
    "action_type",
    "action_detail",
    "next_action_date",
    "old_status",
    "new_status",
    "created_at",
}


def _table_names(conn):
    rows = conn.execute(
        "SELECT name FROM sqlite_master WHERE type = 'table'"
    ).fetchall()
    return {row["name"] for row in rows}


def _column_names(conn, table_name):
    rows = conn.execute(f"PRAGMA table_info({table_name})").fetchall()
    return {row["name"] for row in rows}


def test_init_db_succeeds(tmp_path):
    db_path = tmp_path / "inquiry_case_manager.db"

    init_db(db_path)

    assert db_path.exists()


def test_inquiries_table_exists(tmp_path):
    db_path = tmp_path / "inquiry_case_manager.db"
    init_db(db_path)

    conn = get_connection(db_path)
    try:
        assert "inquiries" in _table_names(conn)
    finally:
        conn.close()


def test_cases_table_exists(tmp_path):
    db_path = tmp_path / "inquiry_case_manager.db"
    init_db(db_path)

    conn = get_connection(db_path)
    try:
        assert "cases" in _table_names(conn)
    finally:
        conn.close()


def test_histories_table_exists(tmp_path):
    db_path = tmp_path / "inquiry_case_manager.db"
    init_db(db_path)

    conn = get_connection(db_path)
    try:
        assert "histories" in _table_names(conn)
    finally:
        conn.close()


def test_main_columns_exist(tmp_path):
    db_path = tmp_path / "inquiry_case_manager.db"
    init_db(db_path)

    conn = get_connection(db_path)
    try:
        assert INQUIRY_COLUMNS.issubset(_column_names(conn, "inquiries"))
        assert CASE_COLUMNS.issubset(_column_names(conn, "cases"))
        assert HISTORY_COLUMNS.issubset(_column_names(conn, "histories"))
    finally:
        conn.close()
