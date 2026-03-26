# integrations/google_sheets_api.py
"""Google Sheets API integration for real-time ledger and reporting."""
import json
from datetime import date, datetime
from typing import List, Optional
from utils.logger import get_logger

logger = get_logger("google_sheets")


def _get_service():
    """Return an authenticated Google Sheets service object."""
    try:
        from google.oauth2.service_account import Credentials
        from googleapiclient.discovery import build
        from config.settings import settings

        scopes = ["https://www.googleapis.com/auth/spreadsheets"]
        creds = Credentials.from_service_account_file(
            settings.GOOGLE_SHEETS_CREDENTIALS_PATH, scopes=scopes
        )
        service = build("sheets", "v4", credentials=creds)
        return service
    except Exception as exc:
        logger.error(f"Failed to build Sheets service: {exc}")
        return None


class GoogleSheetsClient:
    def __init__(self):
        from config.settings import settings
        self.spreadsheet_id = settings.GOOGLE_SHEETS_SPREADSHEET_ID
        self.service = _get_service()

    def _append_rows(self, sheet_name: str, rows: List[List]) -> bool:
        """Append rows to *sheet_name* in the spreadsheet."""
        if not self.service or not self.spreadsheet_id:
            logger.warning("Google Sheets not configured.")
            return False
        try:
            body = {"values": rows}
            self.service.spreadsheets().values().append(
                spreadsheetId=self.spreadsheet_id,
                range=f"{sheet_name}!A1",
                valueInputOption="USER_ENTERED",
                body=body,
            ).execute()
            return True
        except Exception as exc:
            logger.error(f"Failed to append rows to {sheet_name}: {exc}")
            return False

    def _update_range(self, range_notation: str, values: List[List]) -> bool:
        if not self.service or not self.spreadsheet_id:
            return False
        try:
            body = {"values": values}
            self.service.spreadsheets().values().update(
                spreadsheetId=self.spreadsheet_id,
                range=range_notation,
                valueInputOption="USER_ENTERED",
                body=body,
            ).execute()
            return True
        except Exception as exc:
            logger.error(f"Failed to update range {range_notation}: {exc}")
            return False

    def log_sale(
        self,
        sale_date: date,
        product_name: str,
        sales_amount: float,
        cost: float,
        profit: float,
        margin_percent: float,
    ) -> bool:
        """Append a single sale record to the 'Ledger' sheet."""
        row = [
            sale_date.isoformat(),
            product_name,
            int(sales_amount),
            int(cost),
            int(profit),
            f"{margin_percent:.1f}%",
        ]
        return self._append_rows("Ledger", [row])

    def update_daily_summary(
        self,
        report_date: date,
        total_sales: float,
        total_cost: float,
        total_profit: float,
        margin_percent: float,
        total_orders: int,
    ) -> bool:
        """Append a daily summary row to the 'Daily' sheet."""
        row = [
            report_date.isoformat(),
            int(total_sales),
            int(total_cost),
            int(total_profit),
            f"{margin_percent:.1f}%",
            total_orders,
        ]
        return self._append_rows("Daily", [row])

    def ensure_headers(self) -> None:
        """Write column headers if sheets are empty (idempotent)."""
        ledger_headers = [["Date", "Product", "Sales", "Cost", "Profit", "Margin%"]]
        daily_headers = [["Date", "Total Sales", "Total Cost", "Total Profit", "Margin%", "Orders"]]
        self._update_range("Ledger!A1", ledger_headers)
        self._update_range("Daily!A1", daily_headers)
