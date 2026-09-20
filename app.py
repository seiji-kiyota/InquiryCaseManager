import streamlit as st

from common.db import init_db
from pages.case_list import render_case_list
from pages.dashboard import render_dashboard
from pages.inquiry_list import render_inquiry_list
from pages.inquiry_register import render_inquiry_register
from pages.ui import render_page_header

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
st.sidebar.caption("問い合わせ・案件管理ツール")
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
elif selected_menu == "集計・分析":
    render_page_header(
        "集計・分析",
        "ステータス別・優先度別・担当者別・月別の集計はダッシュボードで確認できます。",
    )
    st.info("集計機能はダッシュボードに統合しています。「ダッシュボード」メニューからご覧ください。")
elif selected_menu == "設定":
    render_page_header(
        "設定",
        "担当者やカテゴリなどのマスタ設定は Ver1.0 では未実装です。",
    )
    st.info("ユーザー認証、権限管理、マスタ管理は今後の拡張予定です。")
