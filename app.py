import streamlit as st

from common.db import init_db
from pages.case_list import render_case_list
from pages.dashboard import render_dashboard
from pages.inquiry_list import render_inquiry_list
from pages.inquiry_register import render_inquiry_register

st.set_page_config(page_title="問い合わせ・案件管理ツール", layout="wide")

init_db()

MENU_ITEMS = (
    "ダッシュボード",
    "問い合わせ登録",
    "問い合わせ一覧",
    "案件一覧",
    "集計・分析",
    "設定",
)

st.sidebar.title("メニュー")
selected_menu = st.sidebar.radio("画面選択", MENU_ITEMS)

st.title("問い合わせ・案件管理ツール")

if selected_menu == "ダッシュボード":
    render_dashboard()
elif selected_menu == "問い合わせ登録":
    render_inquiry_register()
elif selected_menu == "問い合わせ一覧":
    render_inquiry_list()
elif selected_menu == "案件一覧":
    render_case_list()
else:
    st.subheader(selected_menu)
    st.info("この機能は今後実装予定です")
