#!/usr/bin/env python3
# scripts/test_price_monitor.py
"""Test the price monitoring pipeline."""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from monitoring.price_monitor import run_price_monitoring


def main():
    print("Running price monitoring…")
    adjusted = run_price_monitoring()
    print(f"✅ Done – {adjusted} products price-adjusted.")


if __name__ == "__main__":
    main()
