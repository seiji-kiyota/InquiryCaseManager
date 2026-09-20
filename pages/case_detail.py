"""案件詳細・編集画面。"""

import streamlit as st

from common.case_service import get_case_by_id, update_case
from common.models import ASSIGNEES, CASE_STATUSES, PRIORITIES, UNASSIGNED_ASSIGNEE
from common.validators import parse_date, validate_case

EDIT_MODE_KEY = "case_detail_edit_id"
SUCCESS_ID_KEY = "case_detail_success_id"


def _choice_index(options, value, fallback=0):
    if value in options:
        return options.index(value)
    return fallback


def _show_readonly(case):
    col1, col2 = st.columns(2)
    with col1:
        st.write(f"案件ID：{case['case_id']}")
        st.write(f"元問い合わせID：{case['inquiry_id']}")
        st.write(f"案件名：{case['case_name']}")
        st.write(f"顧客名：{case['customer_name']}")
        st.write(f"担当者：{case['assignee']}")
        st.write(f"副担当者：{case['sub_assignee'] or '（未設定）'}")
        st.write(f"優先度：{case['priority']}")
        st.write(f"ステータス：{case['status']}")
    with col2:
        st.write(f"進捗率：{case['progress']}%")
        st.write(f"開始日：{case['start_date']}")
        st.write(f"期限：{case['due_date'] or '（未設定）'}")
        st.write(f"完了日：{case['completed_date'] or '（未設定）'}")
        st.write(f"作成日時：{case['created_at']}")
        st.write(f"更新日時：{case['updated_at']}")
    st.write(f"概要：{case['summary'] or '（未入力）'}")
    st.write(f"対応方針：{case['action_plan'] or '（未入力）'}")
    st.write(f"備考：{case['notes'] or '（未入力）'}")


def render_case_detail(case_id):
    st.subheader("案件詳細")

    case = get_case_by_id(case_id)
    if case is None:
        st.warning("対象の案件が見つかりません。")
        return

    success_id = st.session_state.pop(SUCCESS_ID_KEY, None)
    if success_id:
        st.success("案件を更新しました。")
        st.info(f"案件ID：{success_id}")

    editing = st.session_state.get(EDIT_MODE_KEY) == case["case_id"]
    if not editing:
        _show_readonly(case)
        if st.button("編集", key=f"case_edit_button_{case['case_id']}"):
            st.session_state[EDIT_MODE_KEY] = case["case_id"]
            st.rerun()
        return

    st.caption(f"案件ID：{case['case_id']}")
    st.caption(f"元問い合わせID：{case['inquiry_id']}")
    st.caption(f"作成日時：{case['created_at']}　更新日時：{case['updated_at']}")

    with st.form(f"case_edit_form_{case['case_id']}"):
        col1, col2 = st.columns(2)
        with col1:
            case_name = st.text_input("案件名（必須）", value=case["case_name"])
            customer_name = st.text_input("顧客名（必須）", value=case["customer_name"])
            assignee = st.selectbox(
                "担当者",
                ASSIGNEES,
                index=_choice_index(
                    ASSIGNEES,
                    case["assignee"],
                    ASSIGNEES.index(UNASSIGNED_ASSIGNEE),
                ),
            )
            sub_assignee = st.selectbox(
                "副担当者",
                ASSIGNEES,
                index=_choice_index(ASSIGNEES, case["sub_assignee"] or UNASSIGNED_ASSIGNEE),
            )
            priority = st.selectbox(
                "優先度（必須）",
                PRIORITIES,
                index=_choice_index(PRIORITIES, case["priority"]),
            )
            status = st.selectbox(
                "ステータス（必須）",
                CASE_STATUSES,
                index=_choice_index(CASE_STATUSES, case["status"]),
            )
        with col2:
            progress = st.slider("進捗率", min_value=0, max_value=100, value=int(case["progress"] or 0))
            start_date = st.date_input("開始日（必須）", value=parse_date(case["start_date"]))
            due_date = st.date_input("期限", value=parse_date(case["due_date"]))
            completed_date = st.date_input("完了日", value=parse_date(case["completed_date"]))

        summary = st.text_area("概要", value=case["summary"] or "")
        action_plan = st.text_area("対応方針", value=case["action_plan"] or "")
        notes = st.text_area("備考", value=case["notes"] or "")
        submitted = st.form_submit_button("更新する")

    if st.button("編集をやめる", key=f"case_edit_cancel_{case['case_id']}"):
        st.session_state[EDIT_MODE_KEY] = None
        st.rerun()

    if not submitted:
        return

    payload = {
        "case_name": case_name,
        "customer_name": customer_name,
        "assignee": assignee,
        "sub_assignee": "" if sub_assignee == UNASSIGNED_ASSIGNEE else sub_assignee,
        "priority": priority,
        "status": status,
        "progress": progress,
        "start_date": start_date,
        "due_date": due_date,
        "completed_date": completed_date,
        "summary": summary,
        "action_plan": action_plan,
        "notes": notes,
    }
    errors = validate_case(payload)
    if errors:
        for error in errors:
            st.error(error)
        return

    updated_id = update_case(case["case_id"], payload)
    if updated_id is None:
        st.warning("対象の案件が見つかりません。")
        return

    st.session_state[SUCCESS_ID_KEY] = updated_id
    st.session_state[EDIT_MODE_KEY] = None
    st.rerun()
