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
from pages.ui import render_page_header, render_section, show_success_with_id, show_validation_errors

FORM_VERSION_KEY = "inquiry_form_version"
SUCCESS_ID_KEY = "inquiry_register_success_id"


def render_inquiry_register():
    render_page_header(
        "問い合わせ登録",
        "受付した問い合わせを登録します。必須項目を入力して「問い合わせを登録」を押してください。",
    )

    if FORM_VERSION_KEY not in st.session_state:
        st.session_state[FORM_VERSION_KEY] = 0

    success_id = st.session_state.pop(SUCCESS_ID_KEY, None)
    if success_id:
        show_success_with_id("問い合わせを登録しました。", "問い合わせID", success_id)

    form_key = f"inquiry_register_form_{st.session_state[FORM_VERSION_KEY]}"
    with st.form(form_key, clear_on_submit=False):
        render_section("受付情報")
        col1, col2 = st.columns(2)
        with col1:
            received_date = st.date_input("受付日", value=date.today())
        with col2:
            received_time = st.time_input(
                "受付時刻",
                value=datetime.now().time().replace(microsecond=0),
            )

        render_section("顧客情報")
        col1, col2 = st.columns(2)
        with col1:
            customer_name = st.text_input("顧客名（必須）")
            company_name = st.text_input("会社名")
        with col2:
            phone = st.text_input("電話番号")
            email = st.text_input("メールアドレス")

        render_section("分類")
        col1, col2 = st.columns(2)
        with col1:
            channel = st.selectbox("受付方法（必須）", CHANNELS)
            category = st.selectbox("カテゴリ（必須）", CATEGORIES)
        with col2:
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

        render_section("対応状況")
        col1, col2 = st.columns(2)
        with col1:
            due_date = st.date_input("対応期限", value=None)
        with col2:
            status = st.selectbox(
                "ステータス（必須）",
                INQUIRY_STATUSES,
                index=INQUIRY_STATUSES.index("未対応"),
            )

        render_section("内容")
        subject = st.text_input("件名（必須）")
        description = st.text_area("問い合わせ内容（必須）")
        notes = st.text_area("備考")
        submitted = st.form_submit_button("問い合わせを登録")

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
        show_validation_errors(errors)
        return

    try:
        inquiry_id = create_inquiry(payload)
    except Exception:
        st.error("問い合わせの登録に失敗しました。")
        return

    st.session_state[SUCCESS_ID_KEY] = inquiry_id
    st.session_state[FORM_VERSION_KEY] += 1
    st.rerun()
