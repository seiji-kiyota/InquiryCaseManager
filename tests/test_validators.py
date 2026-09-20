from datetime import date

from common.validators import validate_inquiry


def _valid_payload(**overrides):
    payload = {
        "received_date": date(2026, 9, 21),
        "customer_name": "山田太郎",
        "subject": "見積依頼",
        "description": "商品の見積をお願いします。",
        "channel": "電話",
        "category": "商品",
        "priority": "中",
        "status": "未対応",
        "company_name": "",
        "phone": "",
        "email": "",
        "assignee": "未割当",
        "due_date": None,
        "notes": "",
    }
    payload.update(overrides)
    return payload


def test_reject_empty_customer_name():
    errors = validate_inquiry(_valid_payload(customer_name=""))

    assert "顧客名を入力してください。" in errors


def test_reject_empty_subject():
    errors = validate_inquiry(_valid_payload(subject="   "))

    assert "件名を入力してください。" in errors


def test_reject_empty_description():
    errors = validate_inquiry(_valid_payload(description=""))

    assert "問い合わせ内容を入力してください。" in errors


def test_reject_invalid_email():
    errors = validate_inquiry(_valid_payload(email="not-an-email"))

    assert "メールアドレスの形式が正しくありません。" in errors


def test_reject_due_date_before_received_date():
    errors = validate_inquiry(
        _valid_payload(
            received_date=date(2026, 9, 21),
            due_date=date(2026, 9, 20),
        )
    )

    assert "対応期限は受付日以降の日付を指定してください。" in errors


def test_accept_optional_fields_empty():
    errors = validate_inquiry(_valid_payload())

    assert errors == []
