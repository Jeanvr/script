from src.spiders.orkli_catalog import OrkliCatalogSpider


def main():
    spider = OrkliCatalogSpider()
    output_path, total = spider.save_to_csv()

    print(f"Índice catálogo Orkli guardado en: {output_path}")
    print(f"Total items catálogo Orkli: {total}")


if __name__ == "__main__":
    main()