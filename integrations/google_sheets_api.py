import logging
from datetime import date, datetime
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


class GoogleSheetsAPI:
    """Google Sheets integration for ledger and reporting."""

    def __init__(self, credentials_file: str = "./service_account.json", spreadsheet_id: str = ""):
        self.credentials_file = credentials_file
        self.spreadsheet_id = spreadsheet_id
        self._client: Any = None
        self._spreadsheet: Any = None
        logger.info(f"GoogleSheetsAPI initialized spreadsheet={spreadsheet_id!r}")

    def _authenticate(self) -> bool:
        """Authenticate with Google Sheets API using service account."""
        try:
            import gspread
            from oauth2client.service_account import ServiceAccountCredentials
            scopes = [
                "https://spreadsheets.google.com/feeds",
                "https://www.googleapis.com/auth/drive",
            ]
            credentials = ServiceAccountCredentials.from_json_keyfile_name(
                self.credentials_file, scopes
            )
            self._client = gspread.authorize(credentials)
            if self.spreadsheet_id:
                self._spreadsheet = self._client.open_by_key(self.spreadsheet_id)
            logger.info("GoogleSheetsAPI authenticated successfully")
            return True
        except FileNotFoundError:
            logger.warning(f"Service account file not found: {self.credentials_file}")
            return False
        except Exception as exc:
            logger.error(f"Google Sheets authentication failed: {exc}")
            return False

    def _get_or_create_worksheet(self, title: str) -> Optional[Any]:
        """Get existing or create a new worksheet by title."""
        if not self._spreadsheet:
            if not self._authenticate():
                return None
        try:
            return self._spreadsheet.worksheet(title)
        except Exception:
            return self._spreadsheet.add_worksheet(title=title, rows="1000", cols="20")

    def log_transaction(self, transaction_data: Dict) -> bool:
        """Append a transaction row to the Transactions worksheet."""
        ws = self._get_or_create_worksheet("Transactions")
        if ws is None:
            logger.debug(f"[Mock] log_transaction: {transaction_data}")
            return False
        try:
            row = [
                datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S"),
                transaction_data.get("type", ""),
                transaction_data.get("amount", 0),
                transaction_data.get("description", ""),
                transaction_data.get("category", ""),
                transaction_data.get("order_id", ""),
            ]
            ws.append_row(row)
            logger.info(f"Transaction logged to Sheets: {transaction_data.get('description')}")
            return True
        except Exception as exc:
            logger.error(f"Failed to log transaction: {exc}")
            return False

    def update_daily_summary(self, target_date: date, summary_data: Dict) -> bool:
        """Update or append the daily summary row."""
        ws = self._get_or_create_worksheet("Daily Summary")
        if ws is None:
            logger.debug(f"[Mock] update_daily_summary: {target_date} {summary_data}")
            return False
        try:
            row = [
                str(target_date),
                summary_data.get("total_revenue", 0),
                summary_data.get("total_expense", 0),
                summary_data.get("net_profit", 0),
                summary_data.get("order_count", 0),
                summary_data.get("margin_percent", 0),
                summary_data.get("cash_balance", 0),
            ]
            ws.append_row(row)
            logger.info(f"Daily summary updated for {target_date}")
            return True
        except Exception as exc:
            logger.error(f"Failed to update daily summary: {exc}")
            return False

    def get_ledger(self, start_date: date, end_date: date) -> List[Dict]:
        """Retrieve ledger entries within a date range."""
        ws = self._get_or_create_worksheet("Transactions")
        if ws is None:
            return []
        try:
            all_rows = ws.get_all_records()
            filtered = [
                row for row in all_rows
                if start_date.strftime("%Y-%m-%d") <= str(row.get("date", ""))[:10] <= end_date.strftime("%Y-%m-%d")
            ]
            return filtered
        except Exception as exc:
            logger.error(f"Failed to get ledger: {exc}")
            return []

    def sync_products(self, products_list: List[Dict]) -> bool:
        """Write all products to the Products worksheet."""
        ws = self._get_or_create_worksheet("Products")
        if ws is None:
            logger.debug(f"[Mock] sync_products: {len(products_list)} products")
            return False
        try:
            headers = ["ID", "Name", "Purchase Price", "Selling Price", "Platform", "Margin %", "Status", "Wholesaler"]
            ws.clear()
            ws.append_row(headers)
            for p in products_list:
                ws.append_row([
                    p.get("id", ""),
                    p.get("name", ""),
                    p.get("purchase_price", 0),
                    p.get("selling_price", 0),
                    p.get("platform", ""),
                    p.get("margin_percent", 0),
                    p.get("status", ""),
                    p.get("wholesaler", ""),
                ])
            logger.info(f"Synced {len(products_list)} products to Google Sheets")
            return True
        except Exception as exc:
            logger.error(f"Failed to sync products: {exc}")
            return False

    def create_daily_sheet(self, target_date: date) -> bool:
        """Create a new worksheet for a specific date's records."""
        title = f"Daily_{target_date.strftime('%Y%m%d')}"
        ws = self._get_or_create_worksheet(title)
        if ws is None:
            return False
        try:
            ws.append_row(["Time", "Type", "Amount", "Description", "Running Balance"])
            logger.info(f"Daily sheet created: {title}")
            return True
        except Exception as exc:
            logger.error(f"Failed to create daily sheet: {exc}")
            return False

    def update_cash_balance(self, amount: int) -> bool:
        """Update the current cash balance cell."""
        ws = self._get_or_create_worksheet("Dashboard")
        if ws is None:
            logger.debug(f"[Mock] update_cash_balance: {amount}")
            return False
        try:
            ws.update("A1", f"현재 잔고: {amount:,}원")
            ws.update("B1", str(datetime.utcnow()))
            logger.info(f"Cash balance updated to {amount:,}원")
            return True
        except Exception as exc:
            logger.error(f"Failed to update cash balance: {exc}")
            return False
