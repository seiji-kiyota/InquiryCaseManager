from datetime import date, datetime

from common.validators import validate_history


def _valid_history(**overrides):
    payload = {
        "action_datetime": datetime(2026, 9, 21, 10, 0, 0),
        "operator": "山田",
        "action_type": "電話",
        "action_detail": "内容を確認しました。",
        "next_action_date": None,
    }
    payload.update(overrides)
    return payload


def test_reject_empty_action_detail():
    errors = validate_history(_valid_history(action_detail="   "))

    assert "対応内容を入力してください。" in errors


def test_reject_empty_operator():
    errors = validate_history(_valid_history(operator=""))

    assert "対応者を入力してください。" in errors


def test_reject_empty_action_type():
    errors = validate_history(_valid_history(action_type=""))

    assert "対応種別を入力してください。" in errors


def test_reject_next_action_date_before_action_date():
    errors = validate_history(
        _valid_history(
            action_datetime=datetime(2026, 9, 21, 10, 0, 0),
            next_action_date=date(2026, 9, 20),
        )
    )

    assert "次回対応予定日は対応日以降の日付を指定してください。" in errors


def test_accept_missing_next_action_date():
    errors = validate_history(_valid_history(next_action_date=None))

    assert errors == []
