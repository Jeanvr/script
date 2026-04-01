import re

import pandas as pd

from src.core.http import download_file, get_extension_from_url
from src.core.paths import IMAGES_DIR, PDFS_DIR


def clean_text(value) -> str:
    if value is None:
        return ""
    if pd.isna(value):
        return ""
    text = str(value).strip()
    if text.lower() == "nan":
        return ""
    return text


def safe_name(value: str) -> str:
    value = clean_text(value)
    return "".join(ch if ch.isalnum() or ch in ("_", "-") else "_" for ch in value)


def looks_like_price_only(text: str) -> bool:
    text = clean_text(text)
    if not text:
        return True
    return bool(re.fullmatch(r"\d+[.,]\d+\s*€(?:\s+\d+)?", text))


def infer_doc_kind(pdf_url: str, source_url: str = "") -> str:
    pdf_url = clean_text(pdf_url)
    source_url = clean_text(source_url)

    if not pdf_url:
        return "none"

    low = f"{pdf_url} {source_url}".lower()

    if "tarifa" in low or "pvp" in low or "price-list" in low or "price list" in low:
        return "tariff"

    if pdf_url.startswith("http"):
        return "tech_sheet"

    return "none"


def run_media_download(df_matches: pd.DataFrame, provider) -> pd.DataFrame:
    df = df_matches.copy()

    for col in [
        "local_image",
        "local_pdf",
        "media_status",
        "doc_kind",
        "doc_status",
        "matched_name_clean",
        "ecommerce_name",
        "name_source",
        "final_image_url",
        "final_pdf_url",
    ]:
        if col not in df.columns:
            df[col] = ""
        df[col] = df[col].astype(str)

    for idx, row in df.iterrows():
        estado = clean_text(row.get("estado"))
        brand = clean_text(row.get("brand"))
        matched_ref = clean_text(row.get("matched_ref")) or clean_text(row.get("referencia")) or str(idx)
        image_url = clean_text(row.get("image_url"))
        pdf_url = clean_text(row.get("pdf_url"))
        source_url = clean_text(row.get("source_url"))

        input_name = clean_text(row.get("nombre"))
        matched_name = clean_text(row.get("matched_name"))

        matched_name_clean = provider.clean_name(matched_name)
        matched_name_clean = clean_text(matched_name_clean)
        if looks_like_price_only(matched_name_clean):
            matched_name_clean = ""

        if input_name:
            ecommerce_name = input_name
            name_source = "input_name"
        elif matched_name_clean:
            ecommerce_name = matched_name_clean
            name_source = "matched_name"
        else:
            ecommerce_name = matched_ref
            name_source = "matched_ref"

        df.loc[idx, "matched_name_clean"] = matched_name_clean
        df.loc[idx, "ecommerce_name"] = ecommerce_name
        df.loc[idx, "name_source"] = name_source

        if estado != "encontrado":
            df.loc[idx, "media_status"] = "no_encontrado"
            df.loc[idx, "doc_kind"] = "none"
            df.loc[idx, "doc_status"] = "not_matched"
            df.loc[idx, "final_image_url"] = ""
            df.loc[idx, "final_pdf_url"] = ""
            continue

        doc_kind = clean_text(row.get("doc_kind")) or infer_doc_kind(pdf_url, source_url)

        if doc_kind == "tariff":
            doc_status = "no_public_tech_doc"
        elif doc_kind == "tech_sheet":
            doc_status = "public_tech_doc_found"
        else:
            doc_status = "no_public_tech_doc"

        df.loc[idx, "doc_kind"] = doc_kind
        df.loc[idx, "doc_status"] = doc_status
        df.loc[idx, "final_image_url"] = image_url if image_url.startswith("http") else ""
        df.loc[idx, "final_pdf_url"] = pdf_url if doc_kind == "tech_sheet" else ""

        base_name = safe_name(f"{brand}_{matched_ref}" if brand else matched_ref)

        image_ok = False
        pdf_ok = False

        try:
            if image_url.startswith("http"):
                ext = get_extension_from_url(image_url, default=".jpg")
                img_path = IMAGES_DIR / f"{base_name}{ext}"
                download_file(image_url, img_path)
                df.loc[idx, "local_image"] = str(img_path)
                image_ok = True
        except Exception as exc:
            print(f"[IMG ERROR] {matched_ref}: {exc}")

        try:
            if doc_kind == "tech_sheet" and pdf_url.startswith("http"):
                pdf_path = PDFS_DIR / f"{base_name}.pdf"
                download_file(pdf_url, pdf_path)
                df.loc[idx, "local_pdf"] = str(pdf_path)
                pdf_ok = True
        except Exception as exc:
            print(f"[PDF ERROR] {matched_ref}: {exc}")

        if pdf_ok and image_ok:
            df.loc[idx, "media_status"] = "pdf_e_imagen"
        elif pdf_ok:
            df.loc[idx, "media_status"] = "solo_pdf"
        elif image_ok and doc_kind == "tariff":
            df.loc[idx, "media_status"] = "solo_imagen_tarifa_descartada"
        elif image_ok:
            df.loc[idx, "media_status"] = "solo_imagen"
        elif doc_kind == "tariff":
            df.loc[idx, "media_status"] = "tarifa_descartada"
        else:
            df.loc[idx, "media_status"] = "sin_media_publica"

    return df