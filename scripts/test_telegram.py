#!/usr/bin/env python3
# scripts/test_telegram.py
"""Quick sanity-check: send a test Telegram message."""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from integrations.telegram_bot import send_message


def main():
    ok = send_message("🤖 Wholesale Automation System – Telegram 연결 테스트 성공!")
    print("✅ Sent" if ok else "❌ Failed (check TELEGRAM_BOT_TOKEN / TELEGRAM_CEO_CHAT_ID)")


if __name__ == "__main__":
    main()
