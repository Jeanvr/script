from bs4 import BeautifulSoup
from urllib.parse import urljoin
from html import unescape
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

                ref = self.extract_ref(row_text)
                if not ref:
                    continue

                name = self.extract_name(cell_texts, ref)

                try:
                    pdf_url = self.extract_pdf_url(soup, row, ref, category_url)
                except Exception as e:
                    print(f"[WARN] Error sacando PDF para ref {ref}: {e}")
                    pdf_url = ""

                try:
                    image_url = self.extract_image_url(row, category_url)
                except Exception as e:
                    print(f"[WARN] Error sacando imagen para ref {ref}: {e}")
                    image_url = ""

                if image_url and "icono+download" in image_url.lower():
                    image_url = ""

                if pdf_url and "icono+download" in pdf_url.lower():
                    pdf_url = ""

                results.append(
                    {
                        "brand": self.brand,
                        "supplier_ref": str(ref),
                        "normalized_ref": normalize_ref(ref),
                        "name": str(name),
                        "normalized_name": normalize_text(name),
                        "category": "orkli",
                        "image_url": image_url,
                        "pdf_url": pdf_url,
                        "source_url": category_url,
                    }
                )

        return results

    def extract_ref(self, text: str):
        text = str(text or "")
        match = re.search(r"\b\d{6,10}\b", text)
        if match:
            return match.group(0)
        return None

    def extract_name(self, cell_texts, ref: str):
        parts = []

        for txt in cell_texts:
            txt = str(txt or "").strip()
            if not txt:
                continue

            txt = txt.replace(ref, "").strip()
            low = txt.lower()

            if "descargar" in low:
                continue

            if re.fullmatch(r"\d+[.,]\d{2}\s*€?", txt):
                continue

            if re.fullmatch(r"\d{6,10}", txt):
                continue

            parts.append(txt)

        text = " ".join(parts)
        text = re.sub(r"\s+", " ", text).strip(" -|;,.")

        return text or ref

    def extract_pdf_url(self, soup, row, ref: str, base_url: str):
        ref_token = f"_orklicatalogo_WAR_orkliportlet_referencia={ref}"

        def scan(scope):
            if scope is None:
                return ""

            for a in scope.select("a[href]"):
                href = unescape((a.get("href") or "").strip())
                if not href:
                    continue

                low = href.lower()

                # Solo aceptar la ficha técnica individual real
                if (
                    "p_p_resource_id=documento" in low
                    and "p_p_resource_id=documentos" not in low
                    and ref_token in href
                ):
                    return urljoin(base_url, href)

                # Aceptar PDFs directos si existieran
                if ".pdf" in low and ref_token in href:
                    return urljoin(base_url, href)

            return ""

        # 1) fila
        url = scan(row)
        if url:
            return url

        # 2) popover específico, si viene ya en el DOM renderizado
        popover = soup.find(id=f"{ref}_popover")
        url = scan(popover)
        if url:
            return url

        # 3) último intento: toda la página
        url = scan(soup)
        if url:
            return url

        # NO fabricar endpoint "documentos":
        # estaba generando archivos falsos con extensión .pdf
        return ""

    def is_valid_product_image(self, img):
        src = (img.get("src") or img.get("data-src") or "").strip()
        if not src:
            return None

        low = src.lower()
        alt = (img.get("alt") or "").lower()
        title = (img.get("title") or "").lower()
        cls = " ".join(img.get("class", [])).lower()
        meta = f"{low} {alt} {title} {cls}"

        bad_terms = [
            "icono",
            "download",
            "descargar",
            "icon",
            "pdf",
            "doc",
            "sprite",
            "logo",
        ]
        if any(term in meta for term in bad_terms):
            return None

        if (
            "fotos_web" in low
            or any(ext in low for ext in [".jpg", ".jpeg", ".png", ".webp"])
        ):
            return src

        return None

    def extract_image_url(self, row, base_url: str):
        for img in row.select("img[src], img[data-src]"):
            valid_src = self.is_valid_product_image(img)
            if valid_src:
                return urljoin(base_url, valid_src)

        container = row
        for _ in range(6):
            container = getattr(container, "parent", None)
            if container is None:
                break

            for img in container.select("img[src], img[data-src]"):
                valid_src = self.is_valid_product_image(img)
                if valid_src:
                    return urljoin(base_url, valid_src)

        return ""

    def save_to_csv(self, output_name="orkli_products.csv"):
        items = self.scrape()
        df = pd.DataFrame(items)

        output_path = INDEX_DIR / output_name

        if df.empty:
            df.to_csv(output_path, index=False, encoding="utf-8-sig")
            return output_path, 0

        df["image_url"] = df["image_url"].fillna("").astype(str)
        df["pdf_url"] = df["pdf_url"].fillna("").astype(str)

        df.loc[
            df["image_url"].str.contains("icono\\+download", case=False, na=False),
            "image_url"
        ] = ""

        df.loc[
            df["pdf_url"].str.contains("icono\\+download", case=False, na=False),
            "pdf_url"
        ] = ""

        # Bloquear también endpoints "documentos" para no guardar falsos PDF
        df.loc[
            df["pdf_url"].str.contains("p_p_resource_id=documentos", case=False, na=False),
            "pdf_url"
        ] = ""

        df["has_image"] = df["image_url"].str.startswith("http").astype(int)
        df["has_pdf"] = df["pdf_url"].str.startswith("http").astype(int)
        df["media_score"] = df["has_image"] + df["has_pdf"]

        df = df.sort_values(
            by=["normalized_ref", "media_score"],
            ascending=[True, False],
        )

        df = df.drop_duplicates(subset=["normalized_ref"], keep="first")
        df = df.drop(columns=["has_image", "has_pdf", "media_score"], errors="ignore")

        df.to_csv(output_path, index=False, encoding="utf-8-sig")
        return output_path, len(df)