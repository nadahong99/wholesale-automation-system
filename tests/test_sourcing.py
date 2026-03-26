import pytest
from unittest.mock import MagicMock, patch
from core.sourcing_engine import SourcingEngine, SourcingResult
from integrations.wholesalers.daemaetopia import DaemaetopiaSpider
from integrations.wholesalers.easymarket import EasyMarketSpider
from integrations.wholesalers.sinsang import SinsangSpider
from integrations.wholesalers import ALL_WHOLESALERS


def test_daemaetopia_returns_list():
    spider = DaemaetopiaSpider()
    products = spider.get_products()
    assert isinstance(products, list)
    assert len(products) >= 10


def test_daemaetopia_product_has_required_fields():
    spider = DaemaetopiaSpider()
    for product in spider.get_products():
        assert "name" in product
        assert "price" in product
        assert "moq" in product
        assert "wholesaler" in product
        assert product["wholesaler"] == "daemaetopia"


def test_easymarket_returns_list():
    spider = EasyMarketSpider()
    products = spider.get_products()
    assert isinstance(products, list)
    assert len(products) >= 10


def test_sinsang_returns_beauty_products():
    spider = SinsangSpider()
    products = spider.get_products()
    categories = {p["category"] for p in products}
    assert "beauty" in categories


def test_all_wholesalers_return_products():
    for SpiderClass in ALL_WHOLESALERS:
        spider = SpiderClass()
        products = spider.get_products()
        assert len(products) >= 10, f"{SpiderClass.__name__} returned < 10 products"


def test_all_wholesalers_products_have_price():
    for SpiderClass in ALL_WHOLESALERS:
        spider = SpiderClass()
        for product in spider.get_products():
            assert product.get("price", 0) > 0


def test_all_wholesalers_products_have_moq():
    for SpiderClass in ALL_WHOLESALERS:
        spider = SpiderClass()
        for product in spider.get_products():
            assert product.get("moq", 0) >= 1


def test_spider_search_returns_matching_products():
    spider = DaemaetopiaSpider()
    results = spider.search_products("원피스")
    for r in results:
        assert "원피스" in r["name"]


def test_spider_get_product_detail_valid_url():
    spider = DaemaetopiaSpider()
    detail = spider.get_product_detail("https://www.daemaetopia.com/product/1")
    assert detail is not None
    assert "name" in detail
    assert "price" in detail


def test_spider_get_product_detail_invalid_url():
    spider = DaemaetopiaSpider()
    detail = spider.get_product_detail("https://www.daemaetopia.com/product/9999")
    assert detail is None


def test_golden_keyword_filter_matches():
    engine = SourcingEngine()
    products = [
        {"name": "여름원피스 신상", "keyword": "여름원피스"},
        {"name": "청바지 슬림핏", "keyword": "청바지"},
        {"name": "크로스백 미니", "keyword": "크로스백"},
    ]
    keywords = ["여름원피스", "크로스백"]
    filtered = engine.apply_golden_keyword_filter(products, keywords)
    assert len(filtered) == 2


def test_golden_keyword_filter_empty_keywords():
    engine = SourcingEngine()
    products = [{"name": "test", "keyword": "test"}]
    filtered = engine.apply_golden_keyword_filter(products, [])
    assert filtered == products


def test_golden_keyword_filter_no_match():
    engine = SourcingEngine()
    products = [{"name": "청바지", "keyword": "청바지"}]
    filtered = engine.apply_golden_keyword_filter(products, ["원피스"])
    assert len(filtered) == 0


def test_classify_by_moq_auto_list():
    engine = SourcingEngine()
    products = [{"name": "A", "moq": 5}, {"name": "B", "moq": 10}]
    result = engine.classify_by_moq(products)
    assert len(result["auto_list"]) == 2
    assert len(result["bundle"]) == 0
    assert len(result["ceo_review"]) == 0


def test_classify_by_moq_bundle():
    engine = SourcingEngine()
    products = [{"name": "A", "moq": 25}]
    result = engine.classify_by_moq(products)
    assert len(result["bundle"]) == 1


def test_classify_by_moq_ceo_review():
    engine = SourcingEngine()
    products = [{"name": "A", "moq": 100}]
    result = engine.classify_by_moq(products)
    assert len(result["ceo_review"]) == 1


def test_classify_by_moq_boundary_10():
    engine = SourcingEngine()
    products = [{"name": "A", "moq": 10}, {"name": "B", "moq": 11}]
    result = engine.classify_by_moq(products)
    assert result["auto_list"][0]["name"] == "A"
    assert result["bundle"][0]["name"] == "B"


def test_classify_by_moq_boundary_50():
    engine = SourcingEngine()
    products = [{"name": "A", "moq": 50}, {"name": "B", "moq": 51}]
    result = engine.classify_by_moq(products)
    assert result["bundle"][0]["name"] == "A"
    assert result["ceo_review"][0]["name"] == "B"


def test_sourcing_result_total_actionable():
    result = SourcingResult(
        auto_list_count=5,
        bundle_count=3,
        ceo_review_count=2,
    )
    assert result.total_actionable == 10


def test_run_full_sourcing_returns_result():
    engine = SourcingEngine()
    result = engine.run_full_sourcing()
    assert isinstance(result, SourcingResult)
    assert result.total_scraped >= 0
    assert result.total_actionable >= 0


def test_run_full_sourcing_scraped_count():
    engine = SourcingEngine()
    result = engine.run_full_sourcing()
    assert result.total_scraped >= 60  # 6 spiders * 10 products each
