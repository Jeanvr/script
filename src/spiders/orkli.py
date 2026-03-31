from bs4 import BeautifulSoup
from urllib.parse import urljoin
import pandas as pd
import re

from src.core.http import get
from src.core.normalize import normalize_ref, normalize_text
from src.core.paths import INDEX_DIR


class OrkliSpider:
    brand = "orkli"

    def __init__(self, category_urls: list[str]):
        self.category_urls = category_urls

    def scrape(self):
        results = []

        for category_url in self.category_urls:
            print(f"Scrapeando: {category_url}")
            response = get(category_url)
            soup = BeautifulSoup(response.text, "lxml")

            rows = soup.select("tr")
            print("TR encontrados:", len(rows))

            for row in rows:
                cells = row.select("td")
                if len(cells) < 2:
                    continue

                cell_texts = [td.get_text(" ", strip=True) for td in cells]
                row_text = " | ".join(cell_texts)

                ref = self.extract_ref(cell_texts[0] if cell_texts else row.get_text(" ", strip=True))
                if not ref:
                    continue

                name = self.extract_name(cell_texts, ref)
                pdf_url = self.extract_pdf_url(row, category_url)

                results.append({
                    "brand": self.brand,
                    "supplier_ref": str(ref),
                    "normalized_ref": normalize_ref(ref),
                    "name": str(name),
                    "normalized_name": normalize_text(name),
                    "category": "orkli",
                    "image_url": "",
                    "pdf_url": pdf_url,
                    "source_url": category_url,
                })

        return results

    def extract_ref(self, text: str):
        match = re.search(r"\b\d{6,10}\b", text)
        if match:
            return match.group(0)
        return None

    def extract_name(self, cell_texts, ref: str):
        text = " ".join(cell_texts)

        text = text.replace(ref, "", 1).strip()

        text = re.sub(r"\b\d+[.,]\d{2}\b\s*$", "", text).strip()

        text = re.sub(r"\s+", " ", text).strip(" -|")
        return text

    def extract_pdf_url(self, row, base_url: str):
        for a in row.select("a[href]"):
            href = a.get("href", "").strip()
            if not href:
                continue

            full_url = urljoin(base_url, href)

            if "download" in href.lower() or "document" in href.lower() or ".pdf" in href.lower():
                return full_url

        return ""

    def save_to_csv(self, output_name="orkli_products.csv"):
        items = self.scrape()

        df = pd.DataFrame(items)
        if df.empty:
            output_path = INDEX_DIR / output_name
            df.to_csv(output_path, index=False, encoding="utf-8-sig")
            return output_path, 0

        df = df.drop_duplicates(subset=["normalized_ref"])
        output_path = INDEX_DIR / output_name
        df.to_csv(output_path, index=False, encoding="utf-8-sig")
        return output_path, len(df)