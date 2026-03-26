#!/usr/bin/env python3
# scripts/run_simulation.py
"""
End-to-end simulation: seed fake products, run golden keyword filter,
simulate CEO approval, then trigger price monitoring.
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from datetime import date, datetime
from database.session import init_db, SessionLocal
from database import crud
from database.schemas import ProductCreate, DailyProductCreate
from core.margin_calculator import GoldenKeywordFilter, MarginCalculator
from utils.logger import get_logger

logger = get_logger("simulation")

FAKE_PRODUCTS = [
    {"name": "여성 캐주얼 원피스", "wholesale_price": 15000, "category": "패션의류"},
    {"name": "남성 슬림핏 청바지", "wholesale_price": 22000, "category": "패션의류"},
    {"name": "레이어드 니트 스웨터", "wholesale_price": 18000, "category": "패션의류"},
    {"name": "캔버스 토트백", "wholesale_price": 12000, "category": "패션잡화"},
    {"name": "무선 이어폰 케이스", "wholesale_price": 8000, "category": "디지털/가전"},
    {"name": "스마트폰 거치대", "wholesale_price": 5000, "category": "디지털/가전"},
    {"name": "다이어리 플래너", "wholesale_price": 7000, "category": "기타"},
    {"name": "미니 향수 세트", "wholesale_price": 20000, "category": "화장품/미용"},
]


def main():
    print("=== Wholesale Automation Simulation ===\n")

    # 1. Init DB
    print("[1] Initialising database…")
    init_db()
    db = SessionLocal()

    # 2. Create a fake wholesaler
    wholesaler = crud.get_or_create_wholesaler(db, "sim_wholesaler", "https://example.com")

    # 3. Seed fake products
    print("[2] Seeding fake products…")
    calc = MarginCalculator()
    product_ids = []
    for fp in FAKE_PRODUCTS:
        p = crud.create_product(
            db,
            ProductCreate(
                name=fp["name"],
                category=fp["category"],
                wholesale_price=fp["wholesale_price"],
                suggested_selling_price=float(calc.compute_selling_price(fp["wholesale_price"])),
                wholesaler_id=wholesaler.id,
            ),
        )
        product_ids.append(p.id)
        print(f"  + {p.name} | 도매가: {int(p.wholesale_price):,}원 | 판매가: {int(p.suggested_selling_price):,}원")

    # 4. Run golden keyword filter (using fake search volumes)
    print("\n[3] Running golden keyword filter (simulated volumes)…")
    gk = GoldenKeywordFilter(threshold=5.0)

    today = date.today()
    candidates = []
    for idx, pid in enumerate(product_ids):
        sv = (idx + 1) * 120  # simulated search volume
        pc = (idx + 1) * 10   # simulated product count
        candidates.append(
            {
                "product_id": pid,
                "name": FAKE_PRODUCTS[idx]["name"],
                "wholesale_price": FAKE_PRODUCTS[idx]["wholesale_price"],
                "suggested_selling_price": calc.compute_selling_price(FAKE_PRODUCTS[idx]["wholesale_price"]),
                "search_volume": sv,
                "product_count_in_market": pc,
            }
        )

    golden = gk.filter_products(candidates, min_results=0, max_results=100)
    print(f"  Golden products: {len(golden)}")

    # 5. Persist daily products and simulate CEO approval
    print("\n[4] Simulating CEO approval…")
    for item in golden[:3]:
        dp = crud.create_daily_product(
            db,
            DailyProductCreate(
                date=today,
                product_id=item["product_id"],
                search_volume=item["search_volume"],
                product_count_in_market=item["product_count_in_market"],
                golden_keyword_score=item["golden_keyword_score"],
            ),
        )
        crud.approve_daily_product(db, dp.id)
        print(f"  ✅ Approved: {item['name']} (score={item['golden_keyword_score']:.1f})")

    db.close()
    print("\n=== Simulation Complete ===")


if __name__ == "__main__":
    main()
