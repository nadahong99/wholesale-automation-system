# monitoring/dashboard.py
"""Streamlit real-time dashboard."""
import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
from database.session import SessionLocal
from database import models
from monitoring.performance_tracker import get_top_products, compute_daily_metrics, get_weekly_summary
from monitoring.cash_flow_monitor import get_cash_flow_summary

st.set_page_config(
    page_title="도매 자동화 대시보드",
    page_icon="📊",
    layout="wide",
)


@st.cache_data(ttl=300)  # refresh every 5 minutes
def _load_weekly_data():
    db = SessionLocal()
    try:
        return get_weekly_summary(db)
    finally:
        db.close()


@st.cache_data(ttl=60)
def _load_today_metrics():
    db = SessionLocal()
    try:
        return compute_daily_metrics(db)
    finally:
        db.close()


@st.cache_data(ttl=60)
def _load_top_products():
    db = SessionLocal()
    try:
        return get_top_products(db, limit=10)
    finally:
        db.close()


@st.cache_data(ttl=60)
def _load_cash_flow():
    db = SessionLocal()
    try:
        return get_cash_flow_summary(db)
    finally:
        db.close()


def main():
    st.title("📊 도매 자동화 시스템 대시보드")
    st.caption(f"마지막 업데이트: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

    # ── Top-level KPIs ────────────────────────────────────────────────────────
    today = _load_today_metrics()
    cash = _load_cash_flow()

    col1, col2, col3, col4 = st.columns(4)
    col1.metric("오늘 매출", f"₩{int(today['total_revenue']):,}")
    col2.metric("오늘 이익", f"₩{int(today['total_profit']):,}")
    col3.metric("마진율", f"{today['margin_percent']:.1f}%")
    col4.metric("잔여 예산", f"₩{int(cash['cash_available']):,}")

    st.divider()

    # ── Weekly revenue chart ──────────────────────────────────────────────────
    st.subheader("📈 주간 매출 및 이익")
    weekly = _load_weekly_data()
    if weekly:
        df = pd.DataFrame(weekly).sort_values("date")
        st.line_chart(df.set_index("date")[["total_revenue", "total_profit"]])

    st.divider()

    # ── Top products ──────────────────────────────────────────────────────────
    st.subheader("🏆 오늘 상위 판매 상품 TOP 10")
    top = _load_top_products()
    if top:
        df_top = pd.DataFrame(top)
        st.dataframe(df_top, use_container_width=True)
    else:
        st.info("오늘 판매된 상품이 없습니다.")

    st.divider()

    # ── Cash flow status ─────────────────────────────────────────────────────
    st.subheader("💰 캐시플로우 현황")
    col_a, col_b, col_c = st.columns(3)
    col_a.metric("일일 예산", f"₩{int(cash['daily_budget']):,}")
    col_b.metric("사용 금액", f"₩{int(cash['budget_spent']):,}")
    col_c.metric("남은 예산", f"₩{int(cash['cash_available']):,}")

    if cash["cash_available"] < 100_000:
        st.error("⚠️ 현금 잔액이 10만원 미만입니다!")

    # Auto-refresh button
    if st.button("🔄 새로고침"):
        st.cache_data.clear()
        st.rerun()


if __name__ == "__main__":
    main()
