"""問い合わせ一覧・検索画面。"""

import streamlit as st

from common.inquiry_service import count_inquiries, search_inquiries
from common.models import ASSIGNEES, CATEGORIES, INQUIRY_STATUSES, PRIORITIES

FILTER_VERSION_KEY = "inquiry_list_filter_version"

LIST_COLUMNS = (
    "問い合わせID",
    "受付日",
    "顧客名",
    "件名",
    "カテゴリ",
    "優先度",
    "担当者",
    "ステータス",
    "対応期限",
    "期限超過",
)


def _to_display_rows(inquiries):
    return [
        {
            "問い合わせID": item["inquiry_id"],
            "受付日": item["received_date"],
            "顧客名": item["customer_name"],
            "件名": item["subject"],
            "カテゴリ": item["category"],
            "優先度": item["priority"],
            "担当者": item["assignee"],
            "ステータス": item["status"],
            "対応期限": item["due_date"] or "",
            "期限超過": "期限超過" if item["overdue"] else "",
        }
        for item in inquiries
    ]


def render_inquiry_list():
    st.subheader("問い合わせ一覧")

    if FILTER_VERSION_KEY not in st.session_state:
        st.session_state[FILTER_VERSION_KEY] = 0

    prefix = f"inquiry_list_{st.session_state[FILTER_VERSION_KEY]}_"
    col1, col2, col3 = st.columns(3)
    with col1:
        keyword = st.text_input("フリーワード", key=f"{prefix}keyword")
        customer_name = st.text_input("顧客名", key=f"{prefix}customer_name")
        overdue_only = st.checkbox("期限超過のみ", key=f"{prefix}overdue_only")
    with col2:
        received_date_from = st.date_input(
            "受付日（開始）",
            value=None,
            key=f"{prefix}received_date_from",
        )
        received_date_to = st.date_input(
            "受付日（終了）",
            value=None,
            key=f"{prefix}received_date_to",
        )
        categories = st.multiselect("カテゴリ", CATEGORIES, key=f"{prefix}categories")
    with col3:
        assignees = st.multiselect("担当者", ASSIGNEES, key=f"{prefix}assignees")
        priorities = st.multiselect("優先度", PRIORITIES, key=f"{prefix}priorities")
        statuses = st.multiselect("ステータス", INQUIRY_STATUSES, key=f"{prefix}statuses")

    if st.button("検索条件をクリア"):
        st.session_state[FILTER_VERSION_KEY] += 1
        st.rerun()

    filters = {
        "keyword": keyword,
        "customer_name": customer_name,
        "received_date_from": received_date_from,
        "received_date_to": received_date_to,
        "categories": categories,
        "assignees": assignees,
        "priorities": priorities,
        "statuses": statuses,
        "overdue_only": overdue_only,
    }
    inquiries = search_inquiries(filters)
    total_count = count_inquiries()

    st.write(f"検索結果：{len(inquiries)}件")

    if total_count == 0:
        st.info("登録されている問い合わせはありません。")
        return

    if not inquiries:
        st.info("条件に一致する問い合わせはありません。")
        return

    st.dataframe(
        _to_display_rows(inquiries),
        hide_index=True,
        width="stretch",
        column_order=LIST_COLUMNS,
    )
