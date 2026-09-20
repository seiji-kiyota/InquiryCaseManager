"""問い合わせ詳細・編集画面。"""

import streamlit as st

from common.inquiry_service import get_inquiry_by_id, update_inquiry
from common.models import (
    ASSIGNEES,
    CATEGORIES,
    CHANNELS,
    INQUIRY_STATUSES,
    PRIORITIES,
    UNASSIGNED_ASSIGNEE,
)
from common.validators import parse_date, validate_inquiry

EDIT_MODE_KEY = "inquiry_detail_edit_id"
SUCCESS_ID_KEY = "inquiry_detail_success_id"


def _choice_index(options, value, fallback=0):
    if value in options:
        return options.index(value)
    return fallback


def _show_readonly(inquiry):
    col1, col2 = st.columns(2)
    with col1:
        st.write(f"問い合わせID：{inquiry['inquiry_id']}")
        st.write(f"受付日：{inquiry['received_date']}")
        st.write(f"受付時刻：{inquiry['received_time']}")
        st.write(f"顧客名：{inquiry['customer_name']}")
        st.write(f"会社名：{inquiry['company_name'] or '（未入力）'}")
        st.write(f"電話番号：{inquiry['phone'] or '（未入力）'}")
        st.write(f"メールアドレス：{inquiry['email'] or '（未入力）'}")
        st.write(f"受付方法：{inquiry['channel']}")
        st.write(f"カテゴリ：{inquiry['category']}")
    with col2:
        st.write(f"件名：{inquiry['subject']}")
        st.write(f"優先度：{inquiry['priority']}")
        st.write(f"担当者：{inquiry['assignee']}")
        st.write(f"対応期限：{inquiry['due_date'] or '（未設定）'}")
        st.write(f"ステータス：{inquiry['status']}")
        st.write(f"作成日時：{inquiry['created_at']}")
        st.write(f"更新日時：{inquiry['updated_at']}")
    st.write(f"問い合わせ内容：{inquiry['description']}")
    st.write(f"備考：{inquiry['notes'] or '（未入力）'}")


def render_inquiry_detail(inquiry_id):
    st.subheader("問い合わせ詳細")

    inquiry = get_inquiry_by_id(inquiry_id)
    if inquiry is None:
        st.warning("対象の問い合わせが見つかりません。")
        return

    success_id = st.session_state.pop(SUCCESS_ID_KEY, None)
    if success_id:
        st.success("問い合わせを更新しました。")
        st.info(f"問い合わせID：{success_id}")

    editing = st.session_state.get(EDIT_MODE_KEY) == inquiry["inquiry_id"]
    if not editing:
        _show_readonly(inquiry)
        if st.button("編集", key=f"inquiry_edit_button_{inquiry['inquiry_id']}"):
            st.session_state[EDIT_MODE_KEY] = inquiry["inquiry_id"]
            st.rerun()
        return

    st.caption(f"問い合わせID：{inquiry['inquiry_id']}")
    st.caption(f"受付日：{inquiry['received_date']}　受付時刻：{inquiry['received_time']}")
    st.caption(f"作成日時：{inquiry['created_at']}　更新日時：{inquiry['updated_at']}")

    with st.form(f"inquiry_edit_form_{inquiry['inquiry_id']}"):
        col1, col2 = st.columns(2)
        with col1:
            customer_name = st.text_input("顧客名（必須）", value=inquiry["customer_name"])
            company_name = st.text_input("会社名", value=inquiry["company_name"] or "")
            phone = st.text_input("電話番号", value=inquiry["phone"] or "")
            email = st.text_input("メールアドレス", value=inquiry["email"] or "")
            channel = st.selectbox(
                "受付方法（必須）",
                CHANNELS,
                index=_choice_index(CHANNELS, inquiry["channel"]),
            )
            category = st.selectbox(
                "カテゴリ（必須）",
                CATEGORIES,
                index=_choice_index(CATEGORIES, inquiry["category"]),
            )
        with col2:
            subject = st.text_input("件名（必須）", value=inquiry["subject"])
            priority = st.selectbox(
                "優先度（必須）",
                PRIORITIES,
                index=_choice_index(PRIORITIES, inquiry["priority"]),
            )
            assignee = st.selectbox(
                "担当者",
                ASSIGNEES,
                index=_choice_index(ASSIGNEES, inquiry["assignee"], ASSIGNEES.index(UNASSIGNED_ASSIGNEE)),
            )
            due_date = st.date_input("対応期限", value=parse_date(inquiry["due_date"]))
            status = st.selectbox(
                "ステータス（必須）",
                INQUIRY_STATUSES,
                index=_choice_index(INQUIRY_STATUSES, inquiry["status"]),
            )

        description = st.text_area("問い合わせ内容（必須）", value=inquiry["description"])
        notes = st.text_area("備考", value=inquiry["notes"] or "")
        submitted = st.form_submit_button("更新する")

    if st.button("編集をやめる", key=f"inquiry_edit_cancel_{inquiry['inquiry_id']}"):
        st.session_state[EDIT_MODE_KEY] = None
        st.rerun()

    if not submitted:
        return

    payload = {
        "customer_name": customer_name,
        "company_name": company_name,
        "phone": phone,
        "email": email,
        "channel": channel,
        "category": category,
        "subject": subject,
        "description": description,
        "priority": priority,
        "assignee": assignee,
        "due_date": due_date,
        "status": status,
        "notes": notes,
        "received_date": inquiry["received_date"],
    }
    errors = validate_inquiry(payload)
    if errors:
        for error in errors:
            st.error(error)
        return

    updated_id = update_inquiry(inquiry["inquiry_id"], payload)
    if updated_id is None:
        st.warning("対象の問い合わせが見つかりません。")
        return

    st.session_state[SUCCESS_ID_KEY] = updated_id
    st.session_state[EDIT_MODE_KEY] = None
    st.rerun()
