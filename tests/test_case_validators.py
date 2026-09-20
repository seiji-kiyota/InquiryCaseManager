from datetime import date

from common.validators import validate_case


def _valid_case(**overrides):
    payload = {
        "case_name": "見積対応案件",
        "customer_name": "山田太郎",
        "priority": "高",
        "status": "対応中",
        "start_date": date(2026, 9, 21),
        "progress": 20,
        "due_date": date(2026, 9, 30),
        "completed_date": None,
    }
    payload.update(overrides)
    return payload


def test_reject_progress_below_zero():
    errors = validate_case(_valid_case(progress=-1))

    assert "進捗率は0以上で入力してください。" in errors


def test_reject_progress_above_100():
    errors = validate_case(_valid_case(progress=101))

    assert "進捗率は100以下で入力してください。" in errors


def test_reject_due_date_before_start_date():
    errors = validate_case(
        _valid_case(start_date=date(2026, 9, 21), due_date=date(2026, 9, 20))
    )

    assert "期限は開始日以降の日付を指定してください。" in errors


def test_reject_empty_required_fields():
    errors = validate_case(_valid_case(case_name="", customer_name=""))

    assert "案件名を入力してください。" in errors
    assert "顧客名を入力してください。" in errors
