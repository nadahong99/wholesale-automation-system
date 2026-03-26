WHOLESALER_NAMES = [
    "daemaetopia",
    "easymarket",
    "daemaepartner",
    "sinsang",
    "murraykorea",
    "dalgolmart",
]

PLATFORM_FEES = {
    "naver": 0.055,
    "coupang": 0.108,
}

ORDER_STATUS = [
    "PENDING",
    "CONFIRMED",
    "PROCESSING",
    "SHIPPED",
    "DELIVERED",
    "CANCELLED",
    "REFUNDED",
]

PRODUCT_STATUS = [
    "SOURCED",
    "PENDING_APPROVAL",
    "APPROVED",
    "LISTED",
    "SOLD_OUT",
    "REJECTED",
    "DELISTED",
]

MOQ_THRESHOLDS = {
    "auto_list": 10,       # MOQ <= 10: auto-list immediately
    "bundle": 50,          # 10 < MOQ <= 50: bundle strategy
    "ceo_review": 51,      # MOQ > 50: requires CEO review
}

SCHEDULE_TIMES = {
    "sourcing_morning": {"hour": 6, "minute": 0},
    "price_monitor_morning": {"hour": 9, "minute": 0},
    "sourcing_afternoon": {"hour": 14, "minute": 0},
    "price_monitor_afternoon": {"hour": 16, "minute": 0},
    "daily_report": {"hour": 20, "minute": 0},
}

KOREAN_PLATFORM_URLS = {
    "naver": "https://shopping.naver.com",
    "coupang": "https://www.coupang.com",
    "gmarket": "https://www.gmarket.co.kr",
    "auction": "https://www.auction.co.kr",
    "11st": "https://www.11st.co.kr",
}

IMAGE_SIZES = {
    "naver": (1000, 1000),
    "coupang": (1000, 1000),
    "thumbnail": (300, 300),
}

CATEGORIES = {
    "clothing": "의류",
    "bags": "가방",
    "shoes": "신발",
    "accessories": "액세서리",
    "beauty": "뷰티/화장품",
    "electronics": "전자제품",
    "home": "홈/인테리어",
    "kitchen": "주방용품",
    "food": "식품",
}
