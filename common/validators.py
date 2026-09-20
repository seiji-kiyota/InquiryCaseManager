"""問い合わせ登録の入力チェック。"""

import re
from datetime import date, datetime


REQUIRED_FIELDS = (
    ("customer_name", "顧客名"),
    ("subject", "件名"),
    ("description", "問い合わせ内容"),
    ("channel", "受付方法"),
    ("category", "カテゴリ"),
    ("priority", "優先度"),
    ("status", "ステータス"),
)

EMAIL_PATTERN = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")


def _is_blank(value):
    return value is None or str(value).strip() == ""


def parse_date(value):
    """日付値を date に変換する。空の場合は None。"""
    if _is_blank(value):
        return None
    if isinstance(value, datetime):
        return value.date()
    if isinstance(value, date):
        return value
    return date.fromisoformat(str(value).strip()[:10])


def validate_inquiry(data):
    """問い合わせ登録データを検証し、日本語のエラーメッセージ一覧を返す。"""
    errors = []
    payload = data or {}

    for key, label in REQUIRED_FIELDS:
        if _is_blank(payload.get(key)):
            errors.append(f"{label}を入力してください。")

    email = payload.get("email")
    if not _is_blank(email) and EMAIL_PATTERN.match(str(email).strip()) is None:
        errors.append("メールアドレスの形式が正しくありません。")

    received_date = parse_date(payload.get("received_date"))
    due_date = parse_date(payload.get("due_date"))
    if due_date is not None and received_date is not None and due_date < received_date:
        errors.append("対応期限は受付日以降の日付を指定してください。")

    return errors
