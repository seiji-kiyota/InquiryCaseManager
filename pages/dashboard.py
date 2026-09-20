"""ダッシュボード画面。"""

import plotly.express as px
import streamlit as st

from common.dashboard_service import (
    count_cases_by_status,
    count_inquiries_by_assignee,
    count_inquiries_by_priority,
    count_inquiries_by_status,
    get_case_kpis,
    get_inquiry_kpis,
    get_monthly_completion_counts,
    get_monthly_inquiry_counts,
)

EMPTY_CHART_MESSAGE = "表示するデータがありません"


def _show_metrics(items):
    columns = st.columns(len(items))
    for column, (label, value) in zip(columns, items):
        column.metric(label, value)


def _bar_chart(counts, x_title):
    if not counts or sum(counts.values()) == 0:
        st.info(EMPTY_CHART_MESSAGE)
        return

    figure = px.bar(
        x=list(counts.keys()),
        y=list(counts.values()),
        labels={"x": x_title, "y": "件数"},
    )
    figure.update_layout(showlegend=False, margin=dict(t=16, b=40, l=40, r=16))
    st.plotly_chart(figure, width="stretch")


def _line_chart(rows, x_title):
    if not rows:
        st.info(EMPTY_CHART_MESSAGE)
        return

    figure = px.line(
        x=[row["year_month"] for row in rows],
        y=[row["count"] for row in rows],
        markers=True,
        labels={"x": x_title, "y": "件数"},
    )
    figure.update_layout(showlegend=False, margin=dict(t=16, b=40, l=40, r=16))
    st.plotly_chart(figure, width="stretch")


def render_dashboard():
    st.subheader("ダッシュボード")

    inquiry_kpis = get_inquiry_kpis()
    case_kpis = get_case_kpis()

    st.markdown("#### 問い合わせKPI")
    _show_metrics(
        (
            ("総問い合わせ件数", inquiry_kpis["total"]),
            ("未対応件数", inquiry_kpis["未対応"]),
            ("対応中件数", inquiry_kpis["対応中"]),
            ("保留件数", inquiry_kpis["保留"]),
        )
    )
    _show_metrics(
        (
            ("完了件数", inquiry_kpis["完了"]),
            ("問い合わせ完了率", f"{inquiry_kpis['completion_rate']:.1f}%"),
            ("問い合わせ期限超過件数", inquiry_kpis["overdue"]),
        )
    )

    st.markdown("#### 案件KPI")
    _show_metrics(
        (
            ("総案件数", case_kpis["total"]),
            ("未着手件数", case_kpis["未着手"]),
            ("対応中件数", case_kpis["対応中"]),
            ("保留件数", case_kpis["保留"]),
        )
    )
    _show_metrics(
        (
            ("完了件数", case_kpis["完了"]),
            ("案件完了率", f"{case_kpis['completion_rate']:.1f}%"),
            ("案件期限超過件数", case_kpis["overdue"]),
        )
    )

    st.markdown("#### 集計グラフ")
    col1, col2 = st.columns(2)
    with col1:
        st.markdown("##### 問い合わせステータス別")
        _bar_chart(count_inquiries_by_status(), "ステータス")
    with col2:
        st.markdown("##### 問い合わせ優先度別")
        _bar_chart(count_inquiries_by_priority(), "優先度")

    col3, col4 = st.columns(2)
    with col3:
        st.markdown("##### 問い合わせ担当者別")
        _bar_chart(count_inquiries_by_assignee(), "担当者")
    with col4:
        st.markdown("##### 案件ステータス別")
        _bar_chart(count_cases_by_status(), "ステータス")

    st.markdown("##### 月別問い合わせ件数")
    _line_chart(get_monthly_inquiry_counts(), "年月")

    st.markdown("##### 月別完了件数")
    _line_chart(get_monthly_completion_counts(), "年月")
