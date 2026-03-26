# integrations/wholesalers/daemaetopia.py
"""Scraper for Daemaetopia (대매토피아) wholesale site."""
import re
from typing import List
from integrations.wholesalers.base import BaseWholesalerClient, RawProduct
from config.settings import settings


class DaemaetopiaClient(BaseWholesalerClient):
    wholesaler_name = "daemaetopia"
    base_url = "https://www.daemaetopia.com"
    login_url = "https://www.daemaetopia.com/member/login.html"

    def __init__(self):
        super().__init__(
            username=settings.DAEMAETOPIA_USERNAME,
            password=settings.DAEMAETOPIA_PASSWORD,
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
        per_page = 20

        while len(products) < max_products:
            url = f"{self.base_url}/product/list.html"
            soup = self._get_soup(url, params={"page": page})
            if not soup:
                break

            items = soup.select(".xans-record- li.item")
            if not items:
                break

            for item in items:
                if len(products) >= max_products:
                    break
                try:
                    name_el = item.select_one(".name .title")
                    price_el = item.select_one(".price .sale")
                    img_el = item.select_one("img.thumb")
                    link_el = item.select_one("a[href]")

                    if not (name_el and price_el):
                        continue

                    name = name_el.get_text(strip=True)
                    price = self._parse_price(price_el.get_text(strip=True))
                    if not price:
                        continue

                    image_url = img_el.get("src", "") if img_el else ""
                    if image_url and image_url.startswith("//"):
                        image_url = "https:" + image_url

                    product_id = ""
                    if link_el:
                        href = link_el.get("href", "")
                        match = re.search(r"product_no=(\d+)", href)
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
                    self.logger.warning(f"Error parsing product item: {exc}")

            page += 1
            self._sleep(1.0)

        self.logger.info(f"[{self.wholesaler_name}] Scraped {len(products)} products.")
        return products
