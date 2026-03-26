#!/usr/bin/env python3
# scripts/check_schedule.py
"""Display the Celery beat schedule in a human-readable format."""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from scheduler.celery_app import celery_app


def main():
    schedule = celery_app.conf.beat_schedule
    print("=== Celery Beat Schedule ===\n")
    for name, entry in schedule.items():
        cron = entry["schedule"]
        print(f"  {name}")
        print(f"    Task    : {entry['task']}")
        print(f"    Schedule: {cron}")
        print()


if __name__ == "__main__":
    main()
