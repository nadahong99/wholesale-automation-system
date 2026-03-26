# scripts/init_db.py
"""Initialise the database by creating all tables."""
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database.session import init_db
from utils.logger import get_logger

logger = get_logger("init_db")


def main():
    logger.info("Initialising database…")
    init_db()
    logger.info("Database initialised successfully.")


if __name__ == "__main__":
    main()
