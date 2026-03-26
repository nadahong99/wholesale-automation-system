import logging
from dataclasses import dataclass, field
from typing import Dict, List, Optional

from core.margin_calculator import MarginCalculator
from config.constants import MOQ_THRESHOLDS

logger = logging.getLogger(__name__)


@dataclass
class SourcingResult:
    total_scraped: int = 0
    golden_keyword_matches: int = 0
    auto_list_count: int = 0
    bundle_count: int = 0
    ceo_review_count: int = 0
    below_margin_count: int = 0
    products_auto_list: List[Dict] = field(default_factory=list)
    products_bundle: List[Dict] = field(default_factory=list)
    products_ceo_review: List[Dict] = field(default_factory=list)
    errors: List[str] = field(default_factory=list)

    @property
    def total_actionable(self) -> int:
        return self.auto_list_count + self.bundle_count + self.ceo_review_count


class SourcingEngine:
    """Aggregates products from all wholesalers and applies business filters."""

    def __init__(self, db_session=None, min_margin: float = 20.0):
        self.db = db_session
        self.margin_calc = MarginCalculator()
        self.min_margin = min_margin

    def _load_all_wholesaler_products(self) -> List[Dict]:
        """Import and run all wholesaler spiders."""
        from integrations.wholesalers import ALL_WHOLESALERS
        all_products: List[Dict] = []
        for spider_class in ALL_WHOLESALERS:
            spider_name = spider_class.__name__
            try:
                spider = spider_class()
                products = spider.get_products()
                for p in products:
                    p.setdefault("wholesaler", spider_name.lower().replace("spider", ""))
                all_products.extend(products)
                logger.info(f"{spider_name}: fetched {len(products)} products")
            except Exception as exc:
                logger.error(f"{spider_name} failed: {exc}")
        return all_products

    def _load_golden_keywords(self) -> List[str]:
        """Load golden keywords from database or return defaults."""
        if self.db:
            try:
                from database.crud import get_golden_keywords
                stats = get_golden_keywords(self.db)
                return [s.keyword for s in stats]
            except Exception as exc:
                logger.warning(f"Could not load keywords from DB: {exc}")
        # Default sample golden keywords
        return [
            "여름원피스", "니트가디건", "크로스백", "무선이어폰", "쿠션파운데이션",
            "에어프라이어", "텀블러", "캐리어", "운동화", "향수",
        ]

    def apply_golden_keyword_filter(
        self, products: List[Dict], keywords: List[str]
    ) -> List[Dict]:
        """Keep only products whose name/keyword matches a golden keyword."""
        if not keywords:
            return products
        keyword_set = {kw.lower() for kw in keywords}
        matched = []
        for product in products:
            name = (product.get("name") or "").lower()
            kw = (product.get("keyword") or "").lower()
            if any(gk in name or gk in kw for gk in keyword_set):
                matched.append(product)
        logger.info(
            f"Golden keyword filter: {len(products)} -> {len(matched)} products"
        )
        return matched

    def _calculate_and_attach_margin(self, product: Dict) -> Dict:
        """Attach margin_percent to product dict in place."""
        purchase = product.get("price", product.get("purchase_price", 0))
        platform = product.get("platform", "naver")
        sell_price = product.get("selling_price")
        if not sell_price:
            try:
                sell_price = self.margin_calc.suggest_selling_price(
                    purchase, platform, target_margin=0.25
                )
            except Exception:
                sell_price = int(purchase * 1.4)
        product["purchase_price"] = purchase
        product["selling_price"] = sell_price
        product["margin_percent"] = self.margin_calc.calculate_margin(
            purchase, sell_price, platform
        )
        return product

    def classify_by_moq(self, products: List[Dict]) -> Dict[str, List[Dict]]:
        """
        Classify products into auto_list, bundle, or ceo_review buckets
        based on MOQ thresholds.
        """
        auto_list: List[Dict] = []
        bundle: List[Dict] = []
        ceo_review: List[Dict] = []
        for product in products:
            moq = product.get("moq", 1)
            if moq <= MOQ_THRESHOLDS["auto_list"]:
                auto_list.append(product)
            elif moq <= MOQ_THRESHOLDS["bundle"]:
                bundle.append(product)
            else:
                ceo_review.append(product)
        logger.info(
            f"MOQ classification: auto={len(auto_list)} "
            f"bundle={len(bundle)} ceo={len(ceo_review)}"
        )
        return {"auto_list": auto_list, "bundle": bundle, "ceo_review": ceo_review}

    def _save_products_to_db(self, products: List[Dict], status: str = "SOURCED") -> int:
        """Persist products to the database and return count saved."""
        if not self.db:
            return 0
        from database.crud import create_product
        from database.schemas import ProductCreate
        saved = 0
        for p in products:
            try:
                schema = ProductCreate(
                    name=p.get("name", "Unknown")[:500],
                    purchase_price=int(p.get("purchase_price", p.get("price", 0))),
                    selling_price=int(p.get("selling_price", 0)),
                    platform=p.get("platform", "naver"),
                    url=p.get("url"),
                    image_url=p.get("image_url"),
                    moq=int(p.get("moq", 1)),
                    status=status,
                    keyword=p.get("keyword"),
                    wholesaler=p.get("wholesaler"),
                    category=p.get("category"),
                    margin_percent=p.get("margin_percent"),
                )
                create_product(self.db, schema)
                saved += 1
            except Exception as exc:
                logger.error(f"Failed to save product '{p.get('name')}': {exc}")
        return saved

    def run_full_sourcing(self) -> SourcingResult:
        """
        Full pipeline:
        1. Scrape all wholesalers
        2. Apply golden keyword filter
        3. Calculate margins
        4. Filter by minimum margin
        5. Classify by MOQ
        6. Save to database
        """
        result = SourcingResult()

        # Step 1: Scrape
        all_products = self._load_all_wholesaler_products()
        result.total_scraped = len(all_products)

        # Step 2: Golden keyword filter
        keywords = self._load_golden_keywords()
        # For sourcing we use a broad match - include all if no keywords
        if keywords:
            filtered = self.apply_golden_keyword_filter(all_products, keywords)
        else:
            filtered = all_products
        result.golden_keyword_matches = len(filtered)

        # Step 3+4: Margin calculation and filter
        margin_passed: List[Dict] = []
        for product in filtered:
            product = self._calculate_and_attach_margin(product)
            if product.get("margin_percent", 0) >= self.min_margin:
                margin_passed.append(product)
            else:
                result.below_margin_count += 1

        # Step 5: MOQ classification
        classified = self.classify_by_moq(margin_passed)
        result.products_auto_list = classified["auto_list"]
        result.products_bundle = classified["bundle"]
        result.products_ceo_review = classified["ceo_review"]
        result.auto_list_count = len(classified["auto_list"])
        result.bundle_count = len(classified["bundle"])
        result.ceo_review_count = len(classified["ceo_review"])

        # Step 6: Save to DB
        self._save_products_to_db(classified["auto_list"], "APPROVED")
        self._save_products_to_db(classified["bundle"], "PENDING_APPROVAL")
        self._save_products_to_db(classified["ceo_review"], "PENDING_APPROVAL")

        logger.info(
            f"Sourcing complete: scraped={result.total_scraped} "
            f"golden={result.golden_keyword_matches} "
            f"actionable={result.total_actionable}"
        )
        return result
