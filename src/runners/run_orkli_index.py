from src.spiders.orkli import OrkliSpider



ORKLI_CATEGORY_URLS = [
    "https://www.orkli.com/es/web/confortysalud/hidraulica-calefaccion/-/cat/HID/2GF015/F027/SF031",
    "https://www.orkli.com/es/web/confortysalud/hidraulica-calefaccion/-/cat/HID/2GF015/F027/SF032",
    "https://www.orkli.com/es/web/confortysalud/hidraulica-calefaccion/-/cat/HID/2GF015/F029/SF034",
    "https://www.orkli.com/es/web/confortysalud/hidraulica-calefaccion/-/cat/HID/2GF015/F029/SF035",
]


def main():
    spider = OrkliSpider(ORKLI_CATEGORY_URLS)
    output_path, total = spider.save_to_csv()

    print(f"Índice guardado en: {output_path}")
    print(f"Total productos: {total}")


if __name__ == "__main__":
    main()