# wholesale-automation-system
국내 위탁판매 자동화 시스템 – AI-powered Korean Wholesale Automation Platform

## 📋 Overview

A production-ready, fully-automated wholesale system that:
- **Scrapes 6 Korean wholesalers** daily (06:00 & 14:00 KST)
- **Filters products** using Naver Datalab AI golden-keyword scoring
- **Sends candidates to CEO** via Telegram inline buttons (✅ Approve / ❌ Reject)
- **Auto-lists** approved products on Naver Smartstore & Coupang
- **Monitors competitor prices** hourly and auto-adjusts to maintain ≥20% margin
- **Reports** daily P&L, cash flow and top-5 products via Telegram + Google Sheets
- **Streamlit dashboard** for real-time monitoring

---

## 🗂 Folder Structure

```
wholesale-automation-system/
├── api/                     # FastAPI REST API
│   ├── main.py
│   ├── models.py
│   └── routes/
│       ├── sourcing.py
│       ├── orders.py
│       └── monitoring.py
├── core/                    # Business logic
│   ├── sourcing_engine.py   # Daily wholesaler scraping
│   ├── margin_calculator.py # Margin + golden-keyword filter
│   ├── pricing_engine.py    # Competitive price engine
│   ├── order_processor.py   # Wholesaler order fulfilment
│   └── image_generator.py   # Image processing & GCS upload
├── integrations/
│   ├── wholesalers/         # 6 wholesaler scrapers
│   ├── naver_api.py         # Naver Datalab + Shopping
│   ├── coupang_api.py
│   ├── telegram_bot.py      # CEO approval bot
│   ├── google_sheets_api.py
│   └── gcs_upload.py
├── monitoring/
│   ├── dashboard.py         # Streamlit dashboard
│   ├── price_monitor.py
│   ├── cash_flow_monitor.py
│   └── performance_tracker.py
├── database/
│   ├── models.py            # SQLAlchemy ORM models
│   ├── schemas.py           # Pydantic schemas
│   ├── crud.py
│   └── session.py
├── scheduler/
│   ├── celery_app.py        # Celery beat schedule
│   └── tasks.py             # Celery tasks
├── tests/                   # pytest test suite (100+ tests)
├── scripts/                 # Utility scripts
├── config/                  # Settings & constants
├── utils/                   # Helpers, decorators, logger
├── data/                    # Downloaded images (gitignored)
├── logs/                    # Log files (gitignored)
├── results/                 # Export results (gitignored)
├── requirements.txt
├── .env.example
├── Dockerfile
├── docker-compose.yml
├── supervisor.conf
├── nginx.conf
└── setup.py
```

---

## ⚡ Daily Automation Schedule

| Time (KST) | Task |
|------------|------|
| 06:00 | Auto-sourcing – scrape 6 wholesalers (500+ products) |
| 09:00 | Golden-keyword filter → send top 50-100 to CEO |
| 14:00 | Auto-sourcing again |
| 16:00 | Competitor price monitoring + auto-adjust |
| 20:00 | Daily P&L report (Telegram + Google Sheets) |
| Every hour | Price check for all listed products |

---

## 🚀 Setup

### 1. Clone & configure

```bash
git clone https://github.com/nadahong99/wholesale-automation-system.git
cd wholesale-automation-system
cp .env.example .env
# Fill in .env with your API credentials
```

### 2. Install dependencies

```bash
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

### 3. Initialise the database

```bash
python scripts/init_db.py
```

### 4. Run the simulation (no external APIs required)

```bash
python scripts/run_simulation.py
```

### 5. Start with Docker Compose (production)

```bash
docker-compose up -d
```

Services:
- FastAPI: http://localhost:8000
- Dashboard: http://localhost:8501
- API docs: http://localhost:8000/docs

---

## 🐳 Deployment (AWS EC2)

```bash
# On your EC2 instance (Ubuntu 22.04)
git clone https://github.com/nadahong99/wholesale-automation-system.git
cd wholesale-automation-system
bash scripts/deploy.sh
```

The deploy script will:
1. Pull latest code
2. Create virtual environment
3. Install dependencies
4. Initialise the database
5. Start all services via Docker Compose

---

## 🤖 Telegram Bot Commands

| Command | Description |
|---------|-------------|
| `/start` | Show available commands |
| `/set_budget [금액]` | Set daily budget (CEO only) |
| `/check_budget` | Check current budget |
| `/sales_report` | Today's sales report |
| `/top_products` | Top 5 selling products |

When products are sourced, the bot sends an inline-keyboard message:
- **✅ 승인** – Approve product → auto-listed on Naver/Coupang
- **❌ 거절** – Reject product

---

## 📊 API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/health` | Health check |
| POST | `/sourcing/trigger` | Trigger manual sourcing run |
| POST | `/sourcing/golden-keyword` | Trigger keyword filter |
| POST | `/orders/` | Create customer order |
| GET | `/orders/{id}` | Get order details |
| POST | `/monitoring/price-monitor` | Run price monitoring |
| GET | `/monitoring/cash-flow` | Get cash flow summary |
| POST | `/monitoring/budget` | Set daily budget |
| GET | `/monitoring/budget` | Get current budget |

---

## 🧪 Running Tests

```bash
pytest tests/ -v --cov=. --cov-report=term-missing
```

---

## 🔑 Required API Credentials

| Service | Environment Variable |
|---------|---------------------|
| Naver Datalab | `NAVER_DATALAB_CLIENT_ID` / `SECRET` |
| Naver Shopping | `NAVER_CLIENT_ID` / `SECRET` |
| Coupang | `COUPANG_ACCESS_KEY` / `SECRET_KEY` / `VENDOR_ID` |
| Telegram Bot | `TELEGRAM_BOT_TOKEN` / `TELEGRAM_CEO_CHAT_ID` |
| Google Cloud Storage | `GCS_BUCKET_NAME` / `GCS_CREDENTIALS_PATH` |
| Google Sheets | `GOOGLE_SHEETS_CREDENTIALS_PATH` / `SPREADSHEET_ID` |

---

## ⚠️ Troubleshooting

| Problem | Solution |
|---------|----------|
| Celery tasks not running | Check Redis is running: `redis-cli ping` |
| Telegram bot not responding | Verify `TELEGRAM_BOT_TOKEN` in `.env` |
| Scraping returns 0 products | Check wholesaler credentials & network access |
| GCS upload fails | Verify `GCS_CREDENTIALS_PATH` points to valid service account JSON |
| Database errors | Run `python scripts/init_db.py` to re-initialise |
