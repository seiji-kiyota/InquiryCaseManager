"""公開デモ用サンプルデータの投入。"""

from datetime import date, datetime, time, timedelta

from common.case_service import count_cases, create_case_from_inquiry, get_case_by_id, update_case
from common.db import get_connection
from common.history_service import create_history
from common.inquiry_service import count_inquiries, create_inquiry, get_inquiry_by_id, update_inquiry
from common.models import INQUIRY_TARGET_TYPE

DEMO_NOTES = "デモ用サンプルデータ"


def is_database_empty(db_path=None):
    """問い合わせ・案件・履歴がすべて0件なら True。"""
    conn = get_connection(db_path)
    try:
        history_count = conn.execute("SELECT COUNT(*) AS n FROM histories").fetchone()["n"]
    finally:
        conn.close()
    return count_inquiries(db_path=db_path) == 0 and count_cases(db_path=db_path) == 0 and history_count == 0


def has_demo_data(db_path=None):
    """デモ用サンプルデータが登録済みなら True。"""
    conn = get_connection(db_path)
    try:
        count = conn.execute(
            "SELECT COUNT(*) AS n FROM inquiries WHERE notes = ?",
            (DEMO_NOTES,),
        ).fetchone()["n"]
    finally:
        conn.close()
    return count > 0


def seed_demo_data_if_empty(db_path=None, today=None):
    """空DBのときだけサンプルデータを投入する。投入したら True。"""
    if not is_database_empty(db_path=db_path):
        return False
    _seed_demo_data(db_path=db_path, today=today or date.today())
    return True


def _day(today, offset):
    return today + timedelta(days=offset)


def _at(today, offset, hour=10, minute=0):
    return datetime.combine(_day(today, offset), time(hour, minute, 0))


def _inquiry_payload(today, spec):
    due_offset = spec.get("due_offset")
    return {
        "received_date": _day(today, spec["received_offset"]),
        "received_time": time(spec.get("hour", 10), 0, 0),
        "customer_name": spec["customer_name"],
        "company_name": spec.get("company_name", ""),
        "phone": spec.get("phone", "03-1234-5678"),
        "email": spec.get("email", "demo@example.com"),
        "channel": spec["channel"],
        "category": spec["category"],
        "subject": spec["subject"],
        "description": spec["description"],
        "priority": spec["priority"],
        "assignee": spec["assignee"],
        "due_date": "" if due_offset is None else _day(today, due_offset),
        "status": "未対応",
        "notes": DEMO_NOTES,
    }


def _inquiry_update(row, **overrides):
    payload = {
        key: row[key]
        for key in (
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
        )
    }
    payload.update(overrides)
    return payload


def _case_update(case, **overrides):
    payload = {
        "case_name": case["case_name"],
        "customer_name": case["customer_name"],
        "assignee": case["assignee"],
        "sub_assignee": case["sub_assignee"],
        "priority": case["priority"],
        "status": case["status"],
        "progress": case["progress"],
        "start_date": case["start_date"],
        "due_date": case["due_date"],
        "completed_date": case["completed_date"],
        "summary": case["summary"],
        "action_plan": case["action_plan"],
        "notes": case["notes"],
    }
    payload.update(overrides)
    return payload


def _add_history(db_path, inquiry_id, spec, today):
    create_history(
        {
            "target_type": INQUIRY_TARGET_TYPE,
            "target_id": inquiry_id,
            "action_datetime": _at(today, spec["offset"], spec.get("hour", 14)),
            "operator": spec["operator"],
            "action_type": spec["action_type"],
            "action_detail": spec["action_detail"],
            "next_action_date": (
                "" if spec.get("next_offset") is None else _day(today, spec["next_offset"])
            ),
        },
        db_path=db_path,
        now=_at(today, spec["offset"], spec.get("hour", 14)),
    )


def _seed_demo_data(db_path, today):
    specs = (
        {
            "received_offset": -20,
            "due_offset": -10,
            "hour": 9,
            "customer_name": "高橋一郎",
            "company_name": "高橋商事",
            "channel": "電話",
            "category": "商品",
            "subject": "カタログ送付依頼",
            "description": "新商品のカタログ送付を希望されています。",
            "priority": "低",
            "assignee": "未割当",
            "status": "未対応",
            "convert": "overdue",
        },
        {
            "received_offset": -15,
            "due_offset": 7,
            "hour": 11,
            "customer_name": "伊藤美咲",
            "company_name": "伊藤電機",
            "channel": "メール",
            "category": "契約",
            "subject": "契約内容の確認",
            "description": "契約期間と更新条件の確認依頼です。",
            "priority": "中",
            "assignee": "山田",
            "status": "対応中",
            "histories": (
                {
                    "offset": -12,
                    "hour": 13,
                    "operator": "山田",
                    "action_type": "電話",
                    "action_detail": "契約書の該当箇所を案内しました。",
                    "next_offset": 3,
                },
            ),
            "convert": {"status": "対応中", "progress": 40},
        },
        {
            "received_offset": -12,
            "due_offset": 14,
            "hour": 14,
            "customer_name": "渡辺健",
            "company_name": "渡辺工業",
            "channel": "Web",
            "category": "修理",
            "subject": "修理見積の依頼",
            "description": "点検後の修理見積を依頼されています。",
            "priority": "高",
            "assignee": "佐藤",
            "status": "保留",
            "histories": (
                {
                    "offset": -10,
                    "hour": 16,
                    "operator": "佐藤",
                    "action_type": "社内確認",
                    "action_detail": "部品在庫を確認中です。",
                    "next_offset": 5,
                },
            ),
            "convert": {"status": "保留", "progress": 30},
        },
        {
            "received_offset": -60,
            "due_offset": -40,
            "hour": 10,
            "customer_name": "中村優子",
            "company_name": "中村商店",
            "channel": "来店",
            "category": "クレーム",
            "subject": "配送遅延への苦情",
            "description": "納品遅延について説明を求められました。",
            "priority": "緊急",
            "assignee": "鈴木",
            "status": "完了",
            "complete_offset": -50,
        },
        {
            "received_offset": -8,
            "due_offset": None,
            "hour": 15,
            "customer_name": "小林誠",
            "company_name": "小林物産",
            "channel": "その他",
            "category": "要望",
            "subject": "営業時間の延長要望",
            "description": "土曜午後の窓口延長を希望されています。",
            "priority": "低",
            "assignee": "山田",
            "status": "未対応",
        },
        {
            "received_offset": -30,
            "due_offset": 3,
            "hour": 10,
            "customer_name": "加藤花",
            "company_name": "加藤商店",
            "channel": "電話",
            "category": "その他",
            "subject": "資料再送の依頼",
            "description": "前回送付した資料の再送依頼です。",
            "priority": "中",
            "assignee": "佐藤",
            "status": "対応中",
            "histories": (
                {
                    "offset": -28,
                    "hour": 11,
                    "operator": "佐藤",
                    "action_type": "メール",
                    "action_detail": "再送用資料を作成しています。",
                    "next_offset": 1,
                },
            ),
            "convert": {"status": "対応中", "progress": 60},
        },
        {
            "received_offset": -45,
            "due_offset": -20,
            "hour": 9,
            "customer_name": "吉田翔",
            "company_name": "吉田製作所",
            "channel": "メール",
            "category": "商品",
            "subject": "在庫確認",
            "description": "後継機種の在庫確認依頼です。",
            "priority": "高",
            "assignee": "鈴木",
            "status": "完了",
            "complete_offset": -25,
        },
        {
            "received_offset": -5,
            "due_offset": -2,
            "hour": 16,
            "customer_name": "松本直樹",
            "company_name": "松本商事",
            "channel": "Web",
            "category": "契約",
            "subject": "解約手続きの確認",
            "description": "解約申請の進捗確認です。",
            "priority": "緊急",
            "assignee": "未割当",
            "status": "未対応",
            "convert": "overdue",
        },
        {
            "received_offset": -18,
            "due_offset": 21,
            "hour": 13,
            "customer_name": "山本彩",
            "company_name": "山本デザイン",
            "channel": "来店",
            "category": "修理",
            "subject": "点検日程の調整",
            "description": "現地点検の日程調整を依頼されています。",
            "priority": "中",
            "assignee": "山田",
            "status": "保留",
            "convert": {"status": "未着手", "progress": 0},
        },
        {
            "received_offset": -10,
            "due_offset": 1,
            "hour": 11,
            "customer_name": "斎藤大輔",
            "company_name": "斎藤交通",
            "channel": "電話",
            "category": "クレーム",
            "subject": "請求金額の照会",
            "description": "前回請求の内訳確認です。",
            "priority": "低",
            "assignee": "佐藤",
            "status": "完了",
            "complete_offset": -3,
            "histories": (
                {
                    "offset": -8,
                    "hour": 15,
                    "operator": "佐藤",
                    "action_type": "メール",
                    "action_detail": "内訳資料を送付しました。",
                    "next_offset": None,
                },
            ),
            "convert": {"status": "完了", "progress": 100},
        },
        {
            "received_offset": -7,
            "due_offset": 0,
            "hour": 10,
            "customer_name": "森田真由",
            "company_name": "森田企画",
            "channel": "メール",
            "category": "要望",
            "subject": "新プランの提案依頼",
            "description": "来期向けのプラン提案を依頼されています。",
            "priority": "高",
            "assignee": "鈴木",
            "status": "対応中",
            "convert": {"status": "対応中", "progress": 80},
        },
        {
            "received_offset": -70,
            "due_offset": -40,
            "hour": 9,
            "customer_name": "藤田悠",
            "company_name": "藤田商店",
            "channel": "Web",
            "category": "商品",
            "subject": "旧型部品の調達",
            "description": "旧型部品の調達可否確認です。",
            "priority": "中",
            "assignee": "山田",
            "status": "完了",
            "complete_offset": -35,
        },
    )

    created = {}
    for spec in specs:
        inquiry_id = create_inquiry(_inquiry_payload(today, spec), db_path=db_path)
        created[spec["subject"]] = inquiry_id
        row = get_inquiry_by_id(inquiry_id, db_path=db_path)
        target_status = spec["status"]
        if target_status != "未対応":
            complete_offset = spec.get("complete_offset", spec["received_offset"] + 2)
            update_inquiry(
                inquiry_id,
                _inquiry_update(row, status=target_status),
                db_path=db_path,
                now=_at(today, complete_offset if target_status == "完了" else spec["received_offset"] + 1),
            )
            row = get_inquiry_by_id(inquiry_id, db_path=db_path)
        for history in spec.get("histories") or ():
            _add_history(db_path, inquiry_id, history, today)

        convert = spec.get("convert")
        if not convert:
            continue
        case_id = create_case_from_inquiry(inquiry_id, db_path=db_path, today=today)
        if convert == "overdue" or case_id is None:
            continue
        case = get_case_by_id(case_id, db_path=db_path, today=today)
        update_case(
            case_id,
            _case_update(case, status=convert["status"], progress=convert["progress"]),
            db_path=db_path,
            today=today,
        )
