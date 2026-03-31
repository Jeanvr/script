from src.core.paths import INDEX_DIR
from src.spiders.orkli_tariff import OrkliTariffSpider


def main():
    print("Entrando en run_orkli_tariff_index...")

    output_path = INDEX_DIR / "orkli_products.csv"
    spider = OrkliTariffSpider()
    path, total = spider.save_to_csv(output_path)

    print(f"Índice guardado en: {path}")
    print(f"Total productos: {total}")


if __name__ == "__main__":
    main()