"""SQLite接続とテーブル初期化。"""

import sqlite3
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
DEFAULT_DB_PATH = BASE_DIR / "data" / "inquiry_case_manager.db"

CREATE_TABLES_SQL = """
CREATE TABLE IF NOT EXISTS inquiries (
    inquiry_id TEXT PRIMARY KEY,
    received_date TEXT,
    received_time TEXT,
    customer_name TEXT,
    company_name TEXT,
    phone TEXT,
    email TEXT,
    channel TEXT,
    category TEXT,
    subject TEXT,
    description TEXT,
    priority TEXT,
    assignee TEXT,
    due_date TEXT,
    status TEXT,
    notes TEXT,
    created_at TEXT,
    updated_at TEXT
);

CREATE TABLE IF NOT EXISTS cases (
    case_id TEXT PRIMARY KEY,
    inquiry_id TEXT,
    case_name TEXT,
    customer_name TEXT,
    assignee TEXT,
    sub_assignee TEXT,
    priority TEXT,
    status TEXT,
    progress INTEGER,
    start_date TEXT,
    due_date TEXT,
    completed_date TEXT,
    summary TEXT,
    action_plan TEXT,
    notes TEXT,
    created_at TEXT,
    updated_at TEXT
);

CREATE TABLE IF NOT EXISTS histories (
    history_id TEXT PRIMARY KEY,
    target_type TEXT,
    target_id TEXT,
    action_datetime TEXT,
    operator TEXT,
    action_type TEXT,
    action_detail TEXT,
    next_action_date TEXT,
    old_status TEXT,
    new_status TEXT,
    created_at TEXT
);
"""


def get_db_path(db_path=None):
    """利用するDBファイルパスを返す。"""
    return Path(db_path) if db_path is not None else DEFAULT_DB_PATH


def get_connection(db_path=None):
    """SQLite接続を返す。"""
    path = get_db_path(db_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(path)
    conn.row_factory = sqlite3.Row
    return conn


def init_db(db_path=None):
    """必要なテーブルを作成する。"""
    conn = get_connection(db_path)
    try:
        conn.executescript(CREATE_TABLES_SQL)
        conn.commit()
    finally:
        conn.close()
