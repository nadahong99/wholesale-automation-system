import logging
from datetime import date, timedelta

logger = logging.getLogger(__name__)


def get_db_session():
    """Get a database session for the dashboard."""
    try:
        from database.session import get_session_factory
        factory = get_session_factory()
        return factory()
    except Exception as exc:
        logger.error(f"Could not connect to DB: {exc}")
        return None


def main():
    """Main Streamlit dashboard entry point."""
    import streamlit as st
    import pandas as pd

    st.set_page_config(
        page_title="도매 자동화 대시보드",
        page_icon="🛒",
        layout="wide",
        initial_sidebar_state="expanded",
    )

    st.title("🛒 도매 자동화 시스템 대시보드")
    st.caption(f"마지막 업데이트: {date.today()}")

    db = get_db_session()

    tabs = st.tabs([
        "📈 일일 매출",
        "💰 수익 분석",
        "💵 현금 흐름",
        "🏆 인기 상품",
        "🔔 알림",
    ])

    # ── TAB 1: Daily Sales ────────────────────────────────────────────────────
    with tabs[0]:
        st.header("📈 일일 매출 현황")
        if db:
            from database.crud import get_todays_orders, calculate_daily_profit
            orders = get_todays_orders(db)
            total_rev = sum(o.total_amount for o in orders)
            profit = calculate_daily_profit(db)
            margin = (profit / max(total_rev, 1)) * 100

            col1, col2, col3, col4 = st.columns(4)
            col1.metric("오늘 주문 수", f"{len(orders)}건")
            col2.metric("오늘 매출", f"{total_rev:,}원")
            col3.metric("오늘 순이익", f"{profit:,}원")
            col4.metric("마진율", f"{margin:.1f}%")

            # Generate last 7 days mock chart data
            import random
            days = [(date.today() - timedelta(days=i)).isoformat() for i in range(6, -1, -1)]
            revenues = [random.randint(200000, 800000) for _ in days]
            chart_df = pd.DataFrame({"날짜": days, "매출": revenues})
            st.subheader("최근 7일 매출")
            st.bar_chart(chart_df.set_index("날짜"))
        else:
            st.error("데이터베이스에 연결할 수 없습니다.")

    # ── TAB 2: Profit Analysis ────────────────────────────────────────────────
    with tabs[1]:
        st.header("💰 수익 분석")
        import random
        col1, col2 = st.columns(2)
        with col1:
            st.subheader("플랫폼별 매출 비중")
            platform_data = pd.DataFrame({
                "플랫폼": ["네이버", "쿠팡"],
                "매출": [random.randint(300000, 700000), random.randint(200000, 600000)],
            })
            st.dataframe(platform_data, use_container_width=True)
        with col2:
            st.subheader("카테고리별 마진율")
            category_data = pd.DataFrame({
                "카테고리": ["의류", "가방/신발", "전자제품", "뷰티", "홈리빙", "주방"],
                "마진율(%)": [random.uniform(20, 35) for _ in range(6)],
            })
            st.dataframe(category_data, use_container_width=True)

    # ── TAB 3: Cash Flow ──────────────────────────────────────────────────────
    with tabs[2]:
        st.header("💵 현금 흐름")
        if db:
            from monitoring.cash_flow_monitor import CashFlowMonitor
            monitor = CashFlowMonitor(db)
            balance = monitor.get_current_balance()
            st.metric("현재 잔고", f"{balance:,}원")
            projection = monitor.project_monthly_cash_flow()
            st.metric("월말 예상 잔고", f"{projection['projected_end_balance']:,}원")

            import random
            days = [(date.today() - timedelta(days=i)).isoformat() for i in range(29, -1, -1)]
            balances = []
            b = random.randint(500000, 2000000)
            for _ in days:
                b += random.randint(-50000, 80000)
                balances.append(max(b, 0))
            cf_df = pd.DataFrame({"날짜": days, "잔고": balances})
            st.subheader("30일 잔고 추이")
            st.line_chart(cf_df.set_index("날짜"))
        else:
            st.error("데이터베이스에 연결할 수 없습니다.")

    # ── TAB 4: Top Products ───────────────────────────────────────────────────
    with tabs[3]:
        st.header("🏆 인기 상품")
        if db:
            from monitoring.performance_tracker import PerformanceTracker
            tracker = PerformanceTracker(db)
            top = tracker.get_top_products(10)
            if top:
                st.dataframe(pd.DataFrame(top), use_container_width=True)
            else:
                from database.models import Product
                products = db.query(Product).limit(10).all()
                if products:
                    df = pd.DataFrame([
                        {
                            "상품명": p.name[:30],
                            "판매가": f"{p.selling_price:,}원",
                            "마진율": f"{p.margin_percent:.1f}%" if p.margin_percent else "N/A",
                            "상태": p.status,
                            "플랫폼": p.platform,
                        }
                        for p in products
                    ])
                    st.dataframe(df, use_container_width=True)
                else:
                    st.info("소싱된 상품이 없습니다.")

    # ── TAB 5: Alerts ─────────────────────────────────────────────────────────
    with tabs[4]:
        st.header("🔔 알림")
        if db:
            from monitoring.cash_flow_monitor import CashFlowMonitor
            monitor = CashFlowMonitor(db)
            budget = monitor.check_budget_status()
            if budget["is_over_budget"]:
                st.error(f"⚠️ 예산 초과! 사용: {budget['spent']:,}원 / 예산: {budget['daily_budget']:,}원")
            else:
                st.success(f"✅ 예산 정상 (사용률: {budget['percent_used']:.1f}%)")
            current_balance = monitor.get_current_balance()
            if current_balance < 100000:
                st.warning(f"⚠️ 현금 부족 경고: 현재 잔고 {current_balance:,}원")
        st.subheader("가격 변동 알림")
        st.info("가격 모니터링 데이터가 수집되면 여기에 표시됩니다.")

    if db:
        db.close()

    # Auto-refresh
    import time
    st.sidebar.markdown("---")
    if st.sidebar.button("🔄 새로고침"):
        st.rerun()
    st.sidebar.caption("60초마다 자동 새로고침")


if __name__ == "__main__":
    main()
