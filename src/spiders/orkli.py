from bs4 import BeautifulSoup
from urllib.parse import urljoin
from html import unescape
import pandas as pd
import re

from src.core.http import get
from src.core.normalize import normalize_ref, normalize_text
from src.core.paths import INDEX_DIR


_ORKLI_DOC_MAP_CACHE: dict[str, dict[str, str]] = {}


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

                if pdf_url and "p_p_resource_id=documentos" in pdf_url.lower():
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

    def _is_valid_doc_candidate(self, url: str) -> bool:
        low = (url or "").lower().strip()
        if not low:
            return False

        if "icono+download" in low:
            return False

        if "p_p_resource_id=documentos" in low:
            return False

        if "p_p_resource_id=documento" in low:
            return True

        if ".pdf" in low:
            return True

        return False

    def _extract_candidates_from_raw(self, raw: str, base_url: str):
        raw = unescape(str(raw or ""))
        candidates = []

        candidates.extend(
            re.findall(r'href=["\']([^"\']+)["\']', raw, flags=re.IGNORECASE)
        )
        candidates.extend(
            re.findall(r'https?://[^\s"\'>]+', raw, flags=re.IGNORECASE)
        )
        candidates.extend(
            re.findall(
                r'/[^\s"\'>]*(?:p_p_resource_id=documento|p_p_resource_id=documentos)[^\s"\'>]*',
                raw,
                flags=re.IGNORECASE,
            )
        )

        unique = []
        seen = set()

        for item in candidates:
            item = unescape((item or "").strip())
            if not item:
                continue

            full = urljoin(base_url, item)
            if full in seen:
                continue

            seen.add(full)
            unique.append(full)

        return unique

    def _pick_pdf_candidate(self, candidates, ref: str, base_url: str, allow_single: bool = False):
        ref_token = f"_orklicatalogo_war_orkliportlet_referencia={ref}".lower()
        valid = []

        for href in candidates:
            href = unescape((href or "").strip())
            if not href:
                continue

            full = urljoin(base_url, href)
            low = full.lower()

            if not self._is_valid_doc_candidate(full):
                continue

            valid.append(full)

            if ref_token in low:
                return full

        if allow_single and len(valid) == 1:
            return valid[0]

        return ""

    def _scan_scope_for_pdf(self, scope, ref: str, base_url: str, allow_single: bool = False):
        if scope is None:
            return ""

        candidates = self._extract_candidates_from_raw(str(scope), base_url)
        return self._pick_pdf_candidate(candidates, ref, base_url, allow_single=allow_single)

    def _dynamic_extract_ref_from_href(self, href: str) -> str:
        match = re.search(
            r"_orklicatalogo_war_orkliportlet_referencia=(\d{4,10})",
            href,
            flags=re.IGNORECASE,
        )
        if match:
            return match.group(1)
        return ""

    def _dynamic_scan_candidates(self, candidates, base_url: str):
        found = {}

        for href in candidates:
            href = unescape((href or "").strip())
            if not href:
                continue

            full = urljoin(base_url, href)
            if not self._is_valid_doc_candidate(full):
                continue

            ref = self._dynamic_extract_ref_from_href(full)
            if not ref:
                continue

            if ref not in found:
                found[ref] = full

        return found

    def _dynamic_scan_html_for_doc_links(self, html: str, base_url: str):
        candidates = self._extract_candidates_from_raw(html, base_url)
        return self._dynamic_scan_candidates(candidates, base_url)

    def _accept_cookies_if_needed(self, page):
        selectors = [
            'button:has-text("Aceptar")',
            'button:has-text("Aceptar todo")',
            'button:has-text("Aceptar todas")',
            'button:has-text("Permitir todas")',
            'button:has-text("Allow all")',
            'button:has-text("Accept all")',
            '[id*="onetrust-accept"]',
        ]

        for selector in selectors:
            try:
                locator = page.locator(selector)
                if locator.count() > 0:
                    locator.first.click(timeout=1500)
                    page.wait_for_timeout(400)
                    return
            except Exception:
                continue

    def _restore_page_if_navigated(self, page, page_url: str):
        try:
            current = page.url
        except Exception:
            current = page_url

        if current != page_url:
            try:
                page.goto(page_url, wait_until="networkidle", timeout=20000)
                page.wait_for_timeout(800)
                self._accept_cookies_if_needed(page)
            except Exception:
                pass

    def _click_row_document_triggers(self, row):
        selectors = [
            'a[href*="documento"]',
            'a[href$=".pdf"]',
            'a:has-text("Documentos")',
            'a:has-text("Descargar")',
            'button:has-text("Documentos")',
            'button:has-text("Descargar")',
            '[role="button"]:has-text("Documentos")',
            '[role="button"]:has-text("Descargar")',
            '[title*="Descargar"]',
            '[aria-label*="Descargar"]',
            'img[alt*="Descargar"]',
            'img[title*="Descargar"]',
        ]

        for selector in selectors:
            try:
                locator = row.locator(selector)
                total = min(locator.count(), 4)

                for i in range(total):
                    try:
                        item = locator.nth(i)
                        item.scroll_into_view_if_needed(timeout=1000)
                        item.click(force=True, timeout=2000)
                        return True
                    except Exception:
                        continue
            except Exception:
                continue

        return False

    def _get_dynamic_pdf_map(self, page_url: str):
        if page_url in _ORKLI_DOC_MAP_CACHE:
            return _ORKLI_DOC_MAP_CACHE[page_url]

        found = {}
        net_doc_hits = []

        try:
            from playwright.sync_api import sync_playwright
        except Exception as e:
            print(f"[WARN] Playwright no disponible para Orkli: {e}")
            _ORKLI_DOC_MAP_CACHE[page_url] = found
            return found

        def remember_doc_url(raw_url: str):
            try:
                full = urljoin(page_url, raw_url or "")
                if self._is_valid_doc_candidate(full):
                    net_doc_hits.append(full)
            except Exception:
                pass

        print(f"[PW] Fallback dinámico Orkli: {page_url}")

        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            context = browser.new_context(ignore_https_errors=True)
            page = context.new_page()

            page.on("request", lambda request: remember_doc_url(request.url))
            page.on("response", lambda response: remember_doc_url(response.url))

            try:
                page.goto(page_url, wait_until="networkidle", timeout=45000)
                page.wait_for_timeout(1200)
                self._accept_cookies_if_needed(page)
                page.wait_for_timeout(500)

                found.update(self._dynamic_scan_html_for_doc_links(page.content(), page_url))

                rows = page.locator("tr")
                total_rows = min(rows.count(), 250)

                for row_idx in range(total_rows):
                    try:
                        row = rows.nth(row_idx)
                        row_text = row.inner_text(timeout=1500)
                    except Exception:
                        continue

                    ref = self.extract_ref(row_text)
                    if not ref:
                        continue

                    if ref in found and found[ref]:
                        continue

                    try:
                        row_html = row.inner_html(timeout=1500)
                    except Exception:
                        row_html = ""

                    direct_url = self._scan_scope_for_pdf(row_html, ref, page_url, allow_single=True)
                    if direct_url:
                        found[ref] = direct_url
                        print(f"[PW] PDF dinámico Orkli {ref} -> {direct_url}")
                        continue

                    try:
                        anchors = row.locator("a[href]")
                        hrefs = []
                        total_anchors = min(anchors.count(), 8)

                        for i in range(total_anchors):
                            href = anchors.nth(i).get_attribute("href")
                            if href:
                                hrefs.append(href)

                        direct_url = self._pick_pdf_candidate(hrefs, ref, page_url, allow_single=True)
                        if direct_url:
                            found[ref] = direct_url
                            print(f"[PW] PDF dinámico Orkli {ref} -> {direct_url}")
                            continue
                    except Exception:
                        pass

                    net_start = len(net_doc_hits)
                    pages_before = {pg.url for pg in context.pages}

                    clicked = self._click_row_document_triggers(row)
                    if not clicked:
                        continue

                    page.wait_for_timeout(800)

                    # 1) Releer el HTML de la fila tras el click
                    try:
                        row_html_after = row.inner_html(timeout=1500)
                    except Exception:
                        row_html_after = ""

                    direct_url = self._scan_scope_for_pdf(
                        row_html_after,
                        ref,
                        page_url,
                        allow_single=True,
                    )
                    if direct_url:
                        found[ref] = direct_url
                        print(f"[PW] PDF dinámico Orkli {ref} -> {direct_url}")
                        self._restore_page_if_navigated(page, page_url)
                        continue

                    # 2) Releer el HTML completo tras el click
                    try:
                        full_html_after = page.content()
                    except Exception:
                        full_html_after = ""

                    direct_url = self._scan_scope_for_pdf(
                        full_html_after,
                        ref,
                        page_url,
                        allow_single=False,
                    )
                    if direct_url:
                        found[ref] = direct_url
                        print(f"[PW] PDF dinámico Orkli {ref} -> {direct_url}")
                        self._restore_page_if_navigated(page, page_url)
                        continue

                    # 3) Mirar nuevas páginas / popups abiertas
                    new_pages = [pg for pg in context.pages if pg.url not in pages_before]
                    popup_candidates = []

                    for pg in new_pages:
                        try:
                            popup_candidates.append(pg.url)
                        except Exception:
                            pass

                        try:
                            popup_candidates.extend(
                                self._extract_candidates_from_raw(pg.content(), page_url)
                            )
                        except Exception:
                            pass

                    direct_url = self._pick_pdf_candidate(
                        popup_candidates,
                        ref,
                        page_url,
                        allow_single=True,
                    )
                    if direct_url:
                        found[ref] = direct_url
                        print(f"[PW] PDF dinámico Orkli {ref} -> {direct_url}")
                        for pg in new_pages:
                            try:
                                if pg != page:
                                    pg.close()
                            except Exception:
                                pass
                        self._restore_page_if_navigated(page, page_url)
                        continue

                    # 4) Mirar nuevas URLs de red disparadas por ese click
                    new_net_hits = net_doc_hits[net_start:]
                    unique_new_net_hits = []
                    seen_hits = set()

                    for hit in new_net_hits:
                        if hit not in seen_hits:
                            seen_hits.add(hit)
                            unique_new_net_hits.append(hit)

                    direct_url = self._pick_pdf_candidate(
                        unique_new_net_hits,
                        ref,
                        page_url,
                        allow_single=True,
                    )
                    if direct_url:
                        found[ref] = direct_url
                        print(f"[PW] PDF dinámico Orkli {ref} -> {direct_url}")
                        self._restore_page_if_navigated(page, page_url)
                        continue

                    # 5) Caso importante:
                    # si el click de esta fila dispara exactamente 1 doc válido,
                    # lo asociamos a esta referencia aunque la URL no lleve el ref.
                    if len(unique_new_net_hits) == 1:
                        found[ref] = unique_new_net_hits[0]
                        print(f"[PW] PDF dinámico Orkli {ref} -> {unique_new_net_hits[0]}")
                        self._restore_page_if_navigated(page, page_url)
                        continue

                    self._restore_page_if_navigated(page, page_url)

            finally:
                browser.close()

        _ORKLI_DOC_MAP_CACHE[page_url] = found
        return found

    def extract_pdf_url(self, soup, row, ref: str, base_url: str):
        # 1) HTML estático de la fila
        url = self._scan_scope_for_pdf(row, ref, base_url, allow_single=True)
        if url:
            return url

        # 2) popover específico si existe
        popover = soup.find(id=f"{ref}_popover")
        url = self._scan_scope_for_pdf(popover, ref, base_url, allow_single=True)
        if url:
            return url

        # 3) HTML general de la página
        url = self._scan_scope_for_pdf(soup, ref, base_url, allow_single=False)
        if url:
            return url

        # 4) Fallback dinámico con Playwright
        try:
            dynamic_map = self._get_dynamic_pdf_map(base_url)
            return dynamic_map.get(ref, "")
        except Exception as e:
            print(f"[WARN] Playwright fallback PDF para ref {ref}: {e}")
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