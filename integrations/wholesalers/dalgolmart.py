# integrations/wholesalers/dalgolmart.py
"""Scraper for Dalgolmart (달골마트) wholesale site."""
import re
from typing import List
from integrations.wholesalers.base import BaseWholesalerClient, RawProduct
from config.settings import settings


class DalgolmartClient(BaseWholesalerClient):
    wholesaler_name = "dalgolmart"
    base_url = "https://www.dalgolmart.com"
    login_url = "https://www.dalgolmart.com/member/login.html"

    def __init__(self):
        super().__init__(
            username=settings.DALGOLMART_USERNAME,
            password=settings.DALGOLMART_PASSWORD,
        )

    def _do_login(self) -> bool:
        payload = {
            "member_id": self.username,
            "member_passwd": self.password,
        }
        resp = self.session.post(self.login_url, data=payload, timeout=30)
        return resp.status_code == 200 and "로그아웃" in resp.text

    def _scrape_products(self, max_products: int = 200) -> List[RawProduct]:
        products: List[RawProduct] = []
        page = 1

        while len(products) < max_products:
            url = f"{self.base_url}/product/list.html"
            soup = self._get_soup(url, params={"page": page})
            if not soup:
                break

            items = soup.select(".xans-record- li.item, .product-item, .item")
            if not items:
                break

            for item in items:
                if len(products) >= max_products:
                    break
                try:
                    name_el = item.select_one(".name .title, .prd-name")
                    price_el = item.select_one(".price .sale, .sale-price, .price")
                    img_el = item.select_one("img")
                    link_el = item.select_one("a[href]")

                    if not (name_el and price_el):
                        continue

                    name = name_el.get_text(strip=True)
                    price = self._parse_price(price_el.get_text(strip=True))
                    if not price:
                        continue

                    image_url = ""
                    if img_el:
                        image_url = img_el.get("src", img_el.get("data-src", ""))
                        if image_url.startswith("//"):
                            image_url = "https:" + image_url

                    product_id = ""
                    if link_el:
                        match = re.search(r"product_no=(\d+)", link_el.get("href", ""))
                        if match:
                            product_id = match.group(1)

                    products.append(
                        RawProduct(
                            name=name,
                            wholesale_price=price,
                            image_url=image_url,
                            wholesaler_name=self.wholesaler_name,
                            external_product_id=product_id,
                        )
                    )
                except Exception as exc:
                    self.logger.warning(f"Error parsing product: {exc}")

            page += 1
            self._sleep(1.0)

        self.logger.info(f"[{self.wholesaler_name}] Scraped {len(products)} products.")
        return products
