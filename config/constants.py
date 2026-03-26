# config/constants.py

# Wholesaler names
WHOLESALER_DAEMAETOPIA = "daemaetopia"
WHOLESALER_EASYMARKET = "easymarket"
WHOLESALER_DAEMAEPARTNER = "daemaepartner"
WHOLESALER_SINSANG = "sinsang"
WHOLESALER_MURRAYKOREA = "murraykorea"
WHOLESALER_DALGOLMART = "dalgolmart"

ALL_WHOLESALERS = [
    WHOLESALER_DAEMAETOPIA,
    WHOLESALER_EASYMARKET,
    WHOLESALER_DAEMAEPARTNER,
    WHOLESALER_SINSANG,
    WHOLESALER_MURRAYKOREA,
    WHOLESALER_DALGOLMART,
]

# Wholesaler base URLs
WHOLESALER_URLS = {
    WHOLESALER_DAEMAETOPIA: "https://www.daemaetopia.com",
    WHOLESALER_EASYMARKET: "https://www.easyshop.co.kr",
    WHOLESALER_DAEMAEPARTNER: "https://www.daemaepartner.com",
    WHOLESALER_SINSANG: "https://www.sinsangmarket.kr",
    WHOLESALER_MURRAYKOREA: "https://www.murraykorea.com",
    WHOLESALER_DALGOLMART: "https://www.dalgolmart.com",
}

# Order status
ORDER_STATUS_PENDING = "pending"
ORDER_STATUS_ORDERED = "ordered"
ORDER_STATUS_SHIPPED = "shipped"
ORDER_STATUS_DELIVERED = "delivered"
ORDER_STATUS_CANCELLED = "cancelled"
ORDER_STATUS_FAILED = "failed"

# MOQ thresholds
MOQ_DIRECT_MAX = 1
MOQ_BUNDLE_MAX = 9
MOQ_CEO_REVIEW_MIN = 10

# Price monitoring
PRICE_MONITOR_INTERVAL_HOURS = 1
MIN_MARGIN_PERCENT = 20.0
GOLDEN_KEYWORD_THRESHOLD = 10.0
TARGET_MARGIN_PERCENT = 25.0
MAX_PRICE_ADJUSTMENT_PERCENT = 10.0

# Scheduler times (24h format)
SCHEDULE_SOURCING_MORNING = "06:00"
SCHEDULE_GOLDEN_KEYWORD = "09:00"
SCHEDULE_SOURCING_AFTERNOON = "14:00"
SCHEDULE_PRICE_MONITOR = "16:00"
SCHEDULE_DAILY_REPORT = "20:00"

# Telegram callback data
TELEGRAM_CALLBACK_APPROVE = "approve"
TELEGRAM_CALLBACK_REJECT = "reject"

# Product approval status
APPROVAL_PENDING = "pending"
APPROVAL_APPROVED = "approved"
APPROVAL_REJECTED = "rejected"

# Report thresholds
CASH_WARNING_THRESHOLD = 100000  # 100K KRW

# Image settings
IMAGE_WIDTH = 800
IMAGE_HEIGHT = 800
THUMBNAIL_SIZE = (200, 200)

# API retry settings
API_RETRY_COUNT = 3
API_RETRY_DELAY = 2  # seconds

# Naver platform
NAVER_SMARTSTORE = "naver_smartstore"
COUPANG = "coupang"

# Categories
PRODUCT_CATEGORIES = [
    "패션의류",
    "패션잡화",
    "화장품/미용",
    "디지털/가전",
    "가구/인테리어",
    "식품",
    "스포츠/레저",
    "생활/건강",
    "여행/문화",
    "출산/육아",
    "반려동물",
    "기타",
]
