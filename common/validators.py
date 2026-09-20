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


def parse_datetime(value):
    """日時値を datetime に変換する。空または不正な場合は None。"""
    if _is_blank(value):
        return None
    if isinstance(value, datetime):
        return value
    if isinstance(value, date):
        return datetime.combine(value, datetime.min.time())

    text = str(value).strip()
    for format_name in ("%Y-%m-%d %H:%M:%S", "%Y-%m-%d %H:%M", "%Y-%m-%dT%H:%M:%S"):
        try:
            return datetime.strptime(text, format_name)
        except ValueError:
            continue
    try:
        return datetime.fromisoformat(text)
    except ValueError:
        return None


def validate_history(data):
    """対応履歴データを検証し、日本語のエラーメッセージ一覧を返す。"""
    errors = []
    payload = data or {}

    action_datetime = parse_datetime(payload.get("action_datetime"))
    if action_datetime is None:
        errors.append("対応日時を入力してください。")

    if _is_blank(payload.get("operator")):
        errors.append("対応者を入力してください。")

    if _is_blank(payload.get("action_type")):
        errors.append("対応種別を入力してください。")

    if _is_blank(payload.get("action_detail")):
        errors.append("対応内容を入力してください。")

    next_action_date = parse_date(payload.get("next_action_date"))
    if (
        next_action_date is not None
        and action_datetime is not None
        and next_action_date < action_datetime.date()
    ):
        errors.append("次回対応予定日は対応日以降の日付を指定してください。")

    return errors
