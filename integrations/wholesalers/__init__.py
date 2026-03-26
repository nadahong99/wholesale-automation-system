from integrations.wholesalers.daemaetopia import DaemaetopiaSpider
from integrations.wholesalers.easymarket import EasyMarketSpider
from integrations.wholesalers.daemaepartner import DaemaepartnerSpider
from integrations.wholesalers.sinsang import SinsangSpider
from integrations.wholesalers.murraykorea import MurrayKoreaSpider
from integrations.wholesalers.dalgolmart import DalgolmartSpider

ALL_WHOLESALERS = [
    DaemaetopiaSpider,
    EasyMarketSpider,
    DaemaepartnerSpider,
    SinsangSpider,
    MurrayKoreaSpider,
    DalgolmartSpider,
]

__all__ = [
    "DaemaetopiaSpider",
    "EasyMarketSpider",
    "DaemaepartnerSpider",
    "SinsangSpider",
    "MurrayKoreaSpider",
    "DalgolmartSpider",
    "ALL_WHOLESALERS",
]
