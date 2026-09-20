"""問い合わせ登録画面。"""

from datetime import date, datetime

import streamlit as st

from common.inquiry_service import create_inquiry
from common.models import (
    ASSIGNEES,
    CATEGORIES,
    CHANNELS,
    INQUIRY_STATUSES,
    PRIORITIES,
    UNASSIGNED_ASSIGNEE,
)
from common.validators import validate_inquiry

FORM_VERSION_KEY = "inquiry_form_version"
SUCCESS_ID_KEY = "inquiry_register_success_id"


def render_inquiry_register():
    st.subheader("問い合わせ登録")

    if FORM_VERSION_KEY not in st.session_state:
        st.session_state[FORM_VERSION_KEY] = 0

    success_id = st.session_state.pop(SUCCESS_ID_KEY, None)
    if success_id:
        st.success("問い合わせを登録しました。")
        st.info(f"問い合わせID：{success_id}")

    form_key = f"inquiry_register_form_{st.session_state[FORM_VERSION_KEY]}"
    with st.form(form_key, clear_on_submit=False):
        col1, col2 = st.columns(2)
        with col1:
            received_date = st.date_input("受付日", value=date.today())
            customer_name = st.text_input("顧客名（必須）")
            company_name = st.text_input("会社名")
            phone = st.text_input("電話番号")
            email = st.text_input("メールアドレス")
            channel = st.selectbox("受付方法（必須）", CHANNELS)
            category = st.selectbox("カテゴリ（必須）", CATEGORIES)
        with col2:
            received_time = st.time_input(
                "受付時刻",
                value=datetime.now().time().replace(microsecond=0),
            )
            subject = st.text_input("件名（必須）")
            priority = st.selectbox(
                "優先度（必須）",
                PRIORITIES,
                index=PRIORITIES.index("中"),
            )
            assignee = st.selectbox(
                "担当者",
                ASSIGNEES,
                index=ASSIGNEES.index(UNASSIGNED_ASSIGNEE),
            )
            due_date = st.date_input("対応期限", value=None)
            status = st.selectbox(
                "ステータス（必須）",
                INQUIRY_STATUSES,
                index=INQUIRY_STATUSES.index("未対応"),
            )

        description = st.text_area("問い合わせ内容（必須）")
        notes = st.text_area("備考")
        submitted = st.form_submit_button("登録")

    if not submitted:
        return

    payload = {
        "received_date": received_date,
        "received_time": received_time,
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
    }
    errors = validate_inquiry(payload)
    if errors:
        for error in errors:
            st.error(error)
        return

    inquiry_id = create_inquiry(payload)
    st.session_state[SUCCESS_ID_KEY] = inquiry_id
    st.session_state[FORM_VERSION_KEY] += 1
    st.rerun()
