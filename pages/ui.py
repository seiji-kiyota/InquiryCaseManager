"""画面共通の見出し・メッセージ・出力ボタン。"""

from datetime import datetime

import streamlit as st

from common.export_service import generate_export_filename


def render_page_header(title, description):
    st.subheader(title)
    if description:
        st.caption(description)


def render_section(title):
    st.markdown(f"##### {title}")


def choice_index(options, value, fallback=0):
    if value in options:
        return options.index(value)
    return fallback


def show_success_with_id(message, id_label, id_value):
    st.success(message)
    if id_value:
        st.info(f"{id_label}：{id_value}")


def show_validation_errors(errors):
    for error in errors:
        st.error(error)


def overdue_label(is_overdue):
    return "期限超過" if is_overdue else ""


def render_export_buttons(rows, *, prefix, create_csv, create_excel, key_prefix):
    disabled = len(rows) == 0
    now = datetime.now()
    csv_bytes = b""
    excel_bytes = b""
    if not disabled:
        try:
            csv_bytes = create_csv(rows)
        except Exception:
            st.error("CSVの作成に失敗しました。")
            csv_bytes = None
        try:
            excel_bytes = create_excel(rows)
        except Exception:
            st.error("Excelの作成に失敗しました。")
            excel_bytes = None

    col1, col2 = st.columns(2)
    with col1:
        st.download_button(
            "CSVダウンロード",
            data=csv_bytes or b"",
            file_name=generate_export_filename(prefix, "csv", now=now),
            mime="text/csv",
            disabled=disabled or csv_bytes is None,
            key=f"{key_prefix}_csv_download",
        )
    with col2:
        st.download_button(
            "Excelダウンロード",
            data=excel_bytes or b"",
            file_name=generate_export_filename(prefix, "xlsx", now=now),
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            disabled=disabled or excel_bytes is None,
            key=f"{key_prefix}_excel_download",
        )
