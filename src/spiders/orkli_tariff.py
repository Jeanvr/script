import re
from io import BytesIO

import pandas as pd
from pypdf import PdfReader

from src.core.http import get
from src.core.normalize import normalize_ref, normalize_text


PDF_SOURCES = [
    {
        "label": "tarifa_repuestos_2021",
        "category": "repuestos",
        "pdf_url": "https://www.orkli.com/documents/26715/33991/Orkli%2Btarifa%2Brepuestos%2B2021%2Biraila/deb3b515-a3c0-4fbb-8015-a812a463dc95",
        "source_url": "https://www.orkli.com/documents/26715/33991/Orkli%2Btarifa%2Brepuestos%2B2021%2Biraila/deb3b515-a3c0-4fbb-8015-a812a463dc95",
    },
    {
        "label": "tarifa_2025",
        "category": "radiador",
        "pdf_url": "https://www.orkli.com/documents/26715/76863/ORKLI%2BTARIFA%2B2025/eb336f3b-6f15-48c4-a766-4333dc7d33a7",
        "source_url": "https://www.orkli.com/documents/26715/76863/ORKLI%2BTARIFA%2B2025/eb336f3b-6f15-48c4-a766-4333dc7d33a7",
    },
]


class OrkliTariffSpider:
    brand = "orkli"

    def __init__(self, pdf_sources=None):
        self.pdf_sources = pdf_sources or PDF_SOURCES

    def fetch_pdf_text(self, url: str) -> str:
        print(f"Descargando PDF: {url}")
        response = get(url, timeout=120)

        reader = PdfReader(BytesIO(response.content))
        parts = []

        for page in reader.pages:
            text = page.extract_text() or ""
            if text.strip():
                parts.append(text)

        return "\n".join(parts)

    def parse_text(self, text: str, category: str, pdf_url: str, source_url: str):
        items = []

        text = text.replace("\r", "\n")
        text = re.sub(r"[ \t]+", " ", text)
        lines = [ln.strip() for ln in text.split("\n") if ln.strip()]

        seen_refs = set()

        for line in lines:
            # Busca refs tipo E-23758-00, E-5135, V-05369 en cualquier parte de la línea
            m = re.search(r"\b([A-Z]-\d+(?:-\d+)?)\b", line)
            if not m:
                continue

            supplier_ref = m.group(1).strip()
            normalized_ref = normalize_ref(supplier_ref)

            # Evita duplicados
            if normalized_ref in seen_refs:
                continue

            # Coge lo que queda después de la referencia
            rest = line[m.end():].strip()

            # Quita EAN + pack + precio
            rest = re.split(r"\s+\d{12,14}\s+\d+\s+\d+[.,]\d+\s*€?", rest)[0].strip()

            # Quita pack + precio sin EAN
            rest = re.split(r"\s+\d+\s+\d+[.,]\d+\s*€?$", rest)[0].strip()

            # Limpieza extra
            rest = rest.strip(" -|;:")

            # Descarta líneas sin descripción útil
            if not rest or len(rest) < 3:
                continue

            items.append(
                {
                    "brand": self.brand,
                    "supplier_ref": supplier_ref,
                    "normalized_ref": normalized_ref,
                    "name": rest,
                    "normalized_name": normalize_text(rest),
                    "category": category,
                    "image_url": "",
                    "pdf_url": pdf_url,
                    "source_url": source_url,
                }
            )

            seen_refs.add(normalized_ref)

        return items

    def scrape(self):
        all_items = []

        for source in self.pdf_sources:
            print(f"Leyendo PDF: {source['label']}")
            text = self.fetch_pdf_text(source["pdf_url"])

            items = self.parse_text(
                text=text,
                category=source["category"],
                pdf_url=source["pdf_url"],
                source_url=source["source_url"],
            )

            print(f"Items detectados en {source['label']}: {len(items)}")
            all_items.extend(items)

        return all_items

    def save_to_csv(self, output_path):
        items = self.scrape()
        df = pd.DataFrame(items)

        if df.empty:
            df = pd.DataFrame(
                columns=[
                    "brand",
                    "supplier_ref",
                    "normalized_ref",
                    "name",
                    "normalized_name",
                    "category",
                    "image_url",
                    "pdf_url",
                    "source_url",
                ]
            )
        else:
            df = df.drop_duplicates(subset=["normalized_ref"], keep="first")

        df.to_csv(output_path, index=False, encoding="utf-8-sig")
        return output_path, len(df)