"""案件一覧・検索画面。"""

from datetime import datetime

import streamlit as st

from common.case_service import count_cases, search_cases
from common.export_service import (
    create_case_csv_bytes,
    create_case_excel_bytes,
    generate_export_filename,
)
from common.models import ASSIGNEES, CASE_STATUSES, PRIORITIES
from pages.case_detail import render_case_detail

FILTER_VERSION_KEY = "case_list_filter_version"

LIST_COLUMNS = (
    "案件ID",
    "元問い合わせID",
    "案件名",
    "顧客名",
    "担当者",
    "優先度",
    "進捗率",
    "ステータス",
    "開始日",
    "期限",
    "期限超過",
)


def _to_display_rows(cases):
    return [
        {
            "案件ID": item["case_id"],
            "元問い合わせID": item["inquiry_id"],
            "案件名": item["case_name"],
            "顧客名": item["customer_name"],
            "担当者": item["assignee"],
            "優先度": item["priority"],
            "進捗率": item["progress"],
            "ステータス": item["status"],
            "開始日": item["start_date"],
            "期限": item["due_date"] or "",
            "期限超過": "期限超過" if item["overdue"] else "",
        }
        for item in cases
    ]


def render_case_list():
    st.subheader("案件一覧")

    if FILTER_VERSION_KEY not in st.session_state:
        st.session_state[FILTER_VERSION_KEY] = 0

    prefix = f"case_list_{st.session_state[FILTER_VERSION_KEY]}_"
    col1, col2 = st.columns(2)
    with col1:
        keyword = st.text_input("フリーワード", key=f"{prefix}keyword")
        overdue_only = st.checkbox("期限超過のみ", key=f"{prefix}overdue_only")
        assignees = st.multiselect("担当者", ASSIGNEES, key=f"{prefix}assignees")
    with col2:
        priorities = st.multiselect("優先度", PRIORITIES, key=f"{prefix}priorities")
        statuses = st.multiselect("ステータス", CASE_STATUSES, key=f"{prefix}statuses")

    if st.button("検索条件をクリア"):
        st.session_state[FILTER_VERSION_KEY] += 1
        st.rerun()

    filters = {
        "keyword": keyword,
        "assignees": assignees,
        "priorities": priorities,
        "statuses": statuses,
        "overdue_only": overdue_only,
    }
    cases = search_cases(filters)
    total_count = count_cases()

    st.write(f"検索結果：{len(cases)}件")
    _show_export_buttons(cases)

    if total_count == 0:
        st.info("登録されている案件はありません。")
        return

    if not cases:
        st.info("条件に一致する案件はありません。")
        return

    st.dataframe(
        _to_display_rows(cases),
        hide_index=True,
        width="stretch",
        column_order=LIST_COLUMNS,
    )

    st.divider()
    case_ids = [item["case_id"] for item in cases]
    selected_id = st.selectbox(
        "詳細表示する案件",
        case_ids,
        index=None,
        placeholder="選択してください",
    )
    direct_id = st.text_input("案件IDを直接指定", placeholder="CASE-YYYYMM-0001")
    target_id = (direct_id or "").strip() or selected_id
    if target_id:
        render_case_detail(target_id)


def _show_export_buttons(cases):
    disabled = len(cases) == 0
    now = datetime.now()
    csv_bytes = b""
    excel_bytes = b""
    if not disabled:
        try:
            csv_bytes = create_case_csv_bytes(cases)
        except Exception:
            st.error("CSVの作成に失敗しました。")
            csv_bytes = None
        try:
            excel_bytes = create_case_excel_bytes(cases)
        except Exception:
            st.error("Excelの作成に失敗しました。")
            excel_bytes = None

    col1, col2 = st.columns(2)
    with col1:
        st.download_button(
            "CSVダウンロード",
            data=csv_bytes or b"",
            file_name=generate_export_filename("cases", "csv", now=now),
            mime="text/csv",
            disabled=disabled or csv_bytes is None,
            key="case_csv_download",
        )
    with col2:
        st.download_button(
            "Excelダウンロード",
            data=excel_bytes or b"",
            file_name=generate_export_filename("cases", "xlsx", now=now),
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            disabled=disabled or excel_bytes is None,
            key="case_excel_download",
        )
