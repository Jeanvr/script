from src.providers.base import ProviderConfig


class BoschHomeComfortProvider:
    config = ProviderConfig(
        key="bosch_homecomfort",
        index_filename="bosch_homecomfort_products.csv",
        lookup_filename="lookup_bosch_homecomfort.xlsx",
        lookup_media_filename="lookup_bosch_homecomfort_with_media.xlsx",
        brand_labels=["bosch", "junkers", "junkers bosch"],
    )

    def build_spiders(self):
        return []

    def clean_name(self, text: str) -> str:
        return str(text or "").strip()
    