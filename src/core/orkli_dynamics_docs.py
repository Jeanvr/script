from __future__ import annotations

import re
from html import unescape
from urllib.parse import urljoin

from playwright.sync_api import sync_playwright


_DOC_MAP_CACHE: dict[str, dict[str, str]] = {}


def _extract_ref_from_href(href: str) -> str:
    match = re.search(
        r"_orklicatalogo_WAR_orkliportlet_referencia=(\d{4,10})",
        href,
        flags=re.IGNORECASE,
    )
    if match:
        return match.group(1)
    return ""


def _scan_candidates(candidates: list[str], base_url: str) -> dict[str, str]:
    found: dict[str, str] = {}

    for href in candidates:
        href = unescape((href or "").strip())
        if not href:
            continue

        full = urljoin(base_url, href)
        low = full.lower()

        if "p_p_resource_id=documentos" in low:
            continue

        if "p_p_resource_id=documento" not in low and ".pdf" not in low:
            continue

        ref = _extract_ref_from_href(full)
        if not ref:
            continue

        if ref not in found:
            found[ref] = full

    return found


def _scan_html_for_doc_links(html: str, base_url: str) -> dict[str, str]:
    raw = unescape(html or "")

    candidates: list[str] = []
    candidates.extend(re.findall(r'href=["\']([^"\']+)["\']', raw, flags=re.IGNORECASE))
    candidates.extend(re.findall(r'https?://[^\s"\'>]+', raw, flags=re.IGNORECASE))
    candidates.extend(
        re.findall(
            r'/[^\s"\'>]*(?:p_p_resource_id=documento|p_p_resource_id=documentos)[^\s"\'>]*',
            raw,
            flags=re.IGNORECASE,
        )
    )

    seen = set()
    unique_candidates = []
    for item in candidates:
        if item not in seen:
            seen.add(item)
            unique_candidates.append(item)

    return _scan_candidates(unique_candidates, base_url)


def get_orkli_dynamic_pdf_map(page_url: str) -> dict[str, str]:
    if page_url in _DOC_MAP_CACHE:
        return _DOC_MAP_CACHE[page_url]

    found: dict[str, str] = {}

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()

        def handle_response(response):
            try:
                url = response.url
                low = url.lower()
                if "p_p_resource_id=documento" in low and "p_p_resource_id=documentos" not in low:
                    found.update(_scan_candidates([url], page_url))
            except Exception:
                pass

        page.on("response", handle_response)

        page.goto(page_url, wait_until="networkidle", timeout=45000)
        page.wait_for_timeout(1500)

        found.update(_scan_html_for_doc_links(page.content(), page_url))

        icons = page.locator('img[alt*="Descargar"]')
        total = min(icons.count(), 80)

        for i in range(total):
            try:
                icon = icons.nth(i)
                anchor = icon.locator("xpath=ancestor::a[1]")

                current_url = page.url

                if anchor.count() > 0:
                    anchor.click(force=True, timeout=2000)
                else:
                    icon.click(force=True, timeout=2000)

                page.wait_for_timeout(400)
                found.update(_scan_html_for_doc_links(page.content(), page_url))

                if page.url != current_url and page.url != page_url:
                    page.go_back(wait_until="networkidle", timeout=10000)
                    page.wait_for_timeout(400)

            except Exception:
                continue

        browser.close()

    _DOC_MAP_CACHE[page_url] = found
    return found