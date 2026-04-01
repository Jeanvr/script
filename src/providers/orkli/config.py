from src.providers.base import ProviderConfig
from src.spiders.orkli import OrkliSpider
from src.spiders.orkli_catalog import OrkliCatalogSpider
from src.spiders.orkli_tariff import OrkliTariffSpider
from src.providers.orkli.cleaners import clean_orkli_name


ORKLI_CATEGORY_URLS = [
    "https://www.orkli.com/es/web/confortysalud/hidraulica-calefaccion/-/cat/HID/2GF015/F027/SF031",
    "https://www.orkli.com/es/web/confortysalud/hidraulica-calefaccion/-/cat/HID/2GF015/F027/SF032",
    "https://www.orkli.com/es/web/confortysalud/hidraulica-calefaccion/-/cat/HID/2GF015/F029/SF034",
    "https://www.orkli.com/es/web/confortysalud/hidraulica-calefaccion/-/cat/HID/2GF015/F029/SF035",
]


class OrkliProvider:
    config = ProviderConfig(
        key="orkli",
        index_filename="orkli_products.csv",
        lookup_filename="lookup_orkli.xlsx",
        lookup_media_filename="lookup_orkli_with_media.xlsx",
        brand_labels=["orkli"],
    )

    def build_spiders(self):
        return [
            OrkliSpider(ORKLI_CATEGORY_URLS),
            OrkliCatalogSpider(),
            OrkliTariffSpider(),
        ]

    def clean_name(self, text: str) -> str:
        return clean_orkli_name(text)