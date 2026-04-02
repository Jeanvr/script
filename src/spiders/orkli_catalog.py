from __future__ import annotations

import re
from html import unescape
from urllib.parse import urljoin

import pandas as pd
from bs4 import BeautifulSoup

from src.core.http import get
from src.core.normalize import normalize_ref, normalize_text
from src.core.paths import INDEX_DIR


CATALOG_URLS = [
    "https://www.orkli.com/web/confortysalud/hidraulica-calefaccion/-/cat/HID/2GF015/F027/SF032",
]


REF_RE = re.compile(r"\b([A-Z]-\d{4,6}(?:-\d{2})?|[A-Z]\d{4,6}(?:-\d{2})?|\d{4,6})\b")


def clean_text(value: str) -> str:
    text = str(value or "").strip()
    text = re.sub(r"\s+", " ", text)
    return text


def looks_like_price(text: str) -> bool:
    text = text.strip().lower()
    if "€" in text:
        return True
    if "pvp" in text:
        return True
    if "€/ud" in text:
        return True
    return False


class OrkliCatalogSpider:
    brand = "orkli"

    def __init__(self, urls: list[str] | None = None):
        self.urls = urls or CATALOG_URLS

    def scrape(self) -> list[dict]:
        all_items: list[dict] = []

        for url in self.urls:
            print(f"Scrapeando catálogo Orkli: {url}")
            html = get(url).text
            soup = BeautifulSoup(html, "lxml")
            items = self.parse_catalog_page(soup, url)
            print(f"Items encontrados en catálogo: {len(items)}")
            all_items.extend(items)

        return all_items

    def parse_catalog_page(self, soup: BeautifulSoup, source_url: str) -> list[dict]:
        items: list[dict] = []
        seen_refs: set[str] = set()

        rows = soup.select("tr")
        if rows:
            for row in rows:
                item = self.parse_row(row, source_url)
                if not item:
                    continue

                norm_ref = item["normalized_ref"]
                if norm_ref in seen_refs:
                    continue

                seen_refs.add(norm_ref)
                items.append(item)

        if items:
            return items

        cards = soup.select("div, li, article")
        for card in cards:
            item = self.parse_card(card, source_url)
            if not item:
                continue

            norm_ref = item["normalized_ref"]
            if norm_ref in seen_refs:
                continue

            seen_refs.add(norm_ref)
            items.append(item)

        return items

    def parse_row(self, row, source_url: str) -> dict | None:
        row_text = clean_text(row.get_text(" ", strip=True))
        if not row_text:
            return None

        if looks_like_price(row_text) and len(row_text) < 20:
            return None

        ref_match = REF_RE.search(row_text)
        if not ref_match:
            return None

        supplier_ref = clean_text(ref_match.group(1))
        normalized_ref = normalize_ref(supplier_ref)
        if not normalized_ref:
            return None

        image_url = self.extract_image_url(row, source_url)
        pdf_url = self.extract_pdf_url(row, source_url)

        name = self.build_name_from_text(row_text, supplier_ref)
        if not name:
            name = supplier_ref

        return {
            "brand": self.brand,
            "supplier_ref": supplier_ref,
            "normalized_ref": normalized_ref,
            "name": name,
            "normalized_name": normalize_text(name),
            "short_description": "",
            "category": "catalogo",
            "image_url": image_url,
            "pdf_url": pdf_url,
            "source_url": source_url,
            "doc_status": "tech_pdf_found" if pdf_url else "no_public_ficha",
            "source_type": "catalog",
        }

    def parse_card(self, card, source_url: str) -> dict | None:
        text = clean_text(card.get_text(" ", strip=True))
        if not text:
            return None

        ref_match = REF_RE.search(text)
        if not ref_match:
            return None

        supplier_ref = clean_text(ref_match.group(1))
        normalized_ref = normalize_ref(supplier_ref)
        if not normalized_ref:
            return None

        image_url = self.extract_image_url(card, source_url)
        pdf_url = self.extract_pdf_url(card, source_url)

        name = self.build_name_from_text(text, supplier_ref)
        if not name:
            name = supplier_ref

        return {
            "brand": self.brand,
            "supplier_ref": supplier_ref,
            "normalized_ref": normalized_ref,
            "name": name,
            "normalized_name": normalize_text(name),
            "short_description": "",
            "category": "catalogo",
            "image_url": image_url,
            "pdf_url": pdf_url,
            "source_url": source_url,
            "doc_status": "tech_pdf_found" if pdf_url else "no_public_ficha",
            "source_type": "catalog",
        }

    def extract_image_url(self, node, base_url: str) -> str:
        for img in node.select("img[src], img[data-src]"):
            src = (img.get("src") or img.get("data-src") or "").strip()
            if not src:
                continue

            full = urljoin(base_url, src)
            low = full.lower()

            if any(ext in low for ext in [".jpg", ".jpeg", ".png", ".webp"]):
                return full
            if "files.orkli.com" in low:
                return full

        return ""

    def extract_pdf_url(self, node, base_url: str) -> str:
        candidates: list[str] = []

        for a in node.select("a[href]"):
            href = unescape((a.get("href") or "").strip())
            if href:
                candidates.append(href)

        raw = unescape(str(node))
        candidates.extend(re.findall(r'href=["\']([^"\']+)["\']', raw, flags=re.IGNORECASE))
        candidates.extend(re.findall(r'https?://[^\s"\'>]+', raw, flags=re.IGNORECASE))
        candidates.extend(
            re.findall(
                r'/[^\s"\'>]*(?:p_p_resource_id=documento|p_p_resource_id=documentos|/documents/)[^\s"\'>]*',
                raw,
                flags=re.IGNORECASE,
            )
        )

        seen = set()
        unique_candidates = []
        for href in candidates:
            if href not in seen:
                seen.add(href)
                unique_candidates.append(href)

        for href in unique_candidates:
            full = urljoin(base_url, href)
            low = full.lower()

            if "p_p_resource_id=documentos" in low:
                continue

            if "p_p_resource_id=documento" in low:
                return full

            if ".pdf" in low or "/documents/" in low:
                return full

        return ""

    def build_name_from_text(self, text: str, supplier_ref: str) -> str:
        cleaned = text.replace(supplier_ref, " ")
        cleaned = re.sub(r"\b\d+[.,]\d+\s*€\b", " ", cleaned)
        cleaned = re.sub(r"\b\d+\s*€/ud\.?\*?\b", " ", cleaned, flags=re.IGNORECASE)
        cleaned = re.sub(r"\bPVP\b.*", " ", cleaned, flags=re.IGNORECASE)
        cleaned = re.sub(r"\buds/?caja\b.*", " ", cleaned, flags=re.IGNORECASE)
        cleaned = re.sub(r"\s+", " ", cleaned).strip(" -|;")

        if len(cleaned) < 3:
            return supplier_ref

        return cleaned

    def save_to_csv(self, output_name: str = "orkli_catalog_products.csv"):
        items = self.scrape()
        df = pd.DataFrame(items)

        expected_cols = [
            "brand",
            "supplier_ref",
            "normalized_ref",
            "name",
            "normalized_name",
            "short_description",
            "category",
            "image_url",
            "pdf_url",
            "source_url",
            "doc_status",
            "source_type",
        ]

        if df.empty:
            df = pd.DataFrame(columns=expected_cols)
        else:
            if "tech_pdf_url" in df.columns and "pdf_url" not in df.columns:
                df["pdf_url"] = df["tech_pdf_url"]

            if "tech_pdf_url" in df.columns:
                df = df.drop(columns=["tech_pdf_url"], errors="ignore")

            for col in expected_cols:
                if col not in df.columns:
                    df[col] = ""

            df = df[expected_cols]
            df = df.drop_duplicates(subset=["normalized_ref"], keep="first")

        output_path = INDEX_DIR / output_name
        df.to_csv(output_path, index=False, encoding="utf-8-sig")

        return output_path, len(df)