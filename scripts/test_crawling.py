#!/usr/bin/env python3
# scripts/test_crawling.py
"""Test scraping a single page from each wholesaler (no authentication)."""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from integrations.wholesalers import (
    DaemaetopiaClient,
    EasymarketClient,
    DaemaepartnerClient,
    SinsangClient,
    MurraykoreaClient,
    DalgolmartClient,
)

CLIENTS = [
    DaemaetopiaClient,
    EasymarketClient,
    DaemaepartnerClient,
    SinsangClient,
    MurraykoreaClient,
    DalgolmartClient,
]


def main():
    for ClientClass in CLIENTS:
        client = ClientClass()
        print(f"\n── {client.wholesaler_name} ──")
        try:
            products = client.scrape_products(max_products=5)
            print(f"  ✅ Scraped {len(products)} products")
            for p in products[:2]:
                print(f"    · {p.name[:50]} – {int(p.wholesale_price):,}원")
        except Exception as exc:
            print(f"  ❌ Error: {exc}")


if __name__ == "__main__":
    main()
