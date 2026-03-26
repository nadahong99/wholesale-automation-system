# tests/test_integration.py
"""Integration tests – use an in-memory SQLite database."""
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from database.session import Base
from database import crud, models
from database.schemas import ProductCreate, DailyProductCreate, OrderCreate
from core.margin_calculator import MarginCalculator, GoldenKeywordFilter
from datetime import date


@pytest.fixture()
def db():
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(bind=engine)
    Session = sessionmaker(bind=engine)
    session = Session()
    yield session
    session.close()
    Base.metadata.drop_all(bind=engine)


class TestDatabaseIntegration:
    def test_create_wholesaler(self, db):
        w = crud.get_or_create_wholesaler(db, "test", "https://example.com")
        assert w.id is not None
        assert w.name == "test"

    def test_create_product(self, db):
        w = crud.get_or_create_wholesaler(db, "test")
        product = crud.create_product(
            db,
            ProductCreate(
                name="테스트 상품",
                wholesale_price=10000,
                suggested_selling_price=12500,
                wholesaler_id=w.id,
            ),
        )
        assert product.id is not None
        assert product.wholesale_price == 10000

    def test_update_product(self, db):
        w = crud.get_or_create_wholesaler(db, "test2")
        p = crud.create_product(
            db,
            ProductCreate(name="업데이트 테스트", wholesale_price=5000, wholesaler_id=w.id),
        )
        from database.schemas import ProductUpdate
        updated = crud.update_product(db, p.id, ProductUpdate(actual_selling_price=7000))
        assert updated.actual_selling_price == 7000

    def test_create_daily_product(self, db):
        w = crud.get_or_create_wholesaler(db, "test3")
        p = crud.create_product(
            db, ProductCreate(name="일별 상품", wholesale_price=8000, wholesaler_id=w.id)
        )
        today = date.today()
        dp = crud.create_daily_product(
            db,
            DailyProductCreate(
                date=today,
                product_id=p.id,
                search_volume=1000,
                product_count_in_market=50,
                golden_keyword_score=20.0,
            ),
        )
        assert dp.id is not None
        assert dp.golden_keyword_score == 20.0

    def test_approve_daily_product(self, db):
        w = crud.get_or_create_wholesaler(db, "test4")
        p = crud.create_product(
            db, ProductCreate(name="승인 테스트", wholesale_price=9000, wholesaler_id=w.id)
        )
        dp = crud.create_daily_product(
            db,
            DailyProductCreate(date=date.today(), product_id=p.id),
        )
        result = crud.approve_daily_product(db, dp.id)
        assert result.approved_by_ceo == "approved"

    def test_reject_daily_product(self, db):
        w = crud.get_or_create_wholesaler(db, "test5")
        p = crud.create_product(
            db, ProductCreate(name="거절 테스트", wholesale_price=9000, wholesaler_id=w.id)
        )
        dp = crud.create_daily_product(
            db,
            DailyProductCreate(date=date.today(), product_id=p.id),
        )
        result = crud.reject_daily_product(db, dp.id)
        assert result.approved_by_ceo == "rejected"

    def test_create_order(self, db):
        w = crud.get_or_create_wholesaler(db, "test6")
        p = crud.create_product(
            db, ProductCreate(name="주문 테스트", wholesale_price=10000, wholesaler_id=w.id)
        )
        order = crud.create_order(
            db,
            OrderCreate(product_id=p.id, customer_order_id="TEST-001", quantity=2),
        )
        assert order.id is not None
        assert order.quantity == 2

    def test_budget_workflow(self, db):
        budget = crud.get_or_create_budget(db, daily_amount=1_000_000)
        assert budget.remaining == 1_000_000

        deducted = crud.deduct_budget(db, 50_000)
        assert deducted.spent == 50_000
        assert deducted.remaining == 950_000

    def test_price_history(self, db):
        w = crud.get_or_create_wholesaler(db, "test7")
        p = crud.create_product(
            db, ProductCreate(name="가격 히스토리 테스트", wholesale_price=10000, wholesaler_id=w.id)
        )
        ph = crud.add_price_history(db, p.id, 15000.0, 12500.0, 20.0, "naver")
        assert ph.id is not None
        assert ph.margin_percent == 20.0

    def test_get_listed_products_empty(self, db):
        result = crud.get_listed_products(db)
        assert result == []

    def test_get_listed_products_after_listing(self, db):
        w = crud.get_or_create_wholesaler(db, "test8")
        p = crud.create_product(
            db, ProductCreate(name="등록 상품", wholesale_price=10000, wholesaler_id=w.id, is_listed=True)
        )
        result = crud.get_listed_products(db)
        assert len(result) == 1
        assert result[0].name == "등록 상품"


class TestMarginAndFilterIntegration:
    def test_full_margin_pipeline(self):
        calc = MarginCalculator(20.0)
        gk = GoldenKeywordFilter(threshold=10.0)

        # Simulate products with different scores
        products = [
            {"product_id": i, "name": f"상품{i}", "wholesale_price": 10000,
             "search_volume": i * 500, "product_count_in_market": 100}
            for i in range(1, 21)
        ]
        golden = gk.filter_products(products, min_results=0, max_results=10)

        for item in golden:
            price = calc.compute_selling_price(item["wholesale_price"])
            margin = calc.compute_margin(item["wholesale_price"], price)
            assert margin >= 20.0
