import re

import pandas as pd

from src.core.http import download_file, download_pdf_file, get_extension_from_url
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
    return bool(re.fullmatch(r"\d+[.,]\d+\s*(?:€|â‚¬)?(?:\s+\d+)?", text))


def is_catalog_or_tariff_pdf_url(pdf_url: str, source_url: str = "") -> bool:
    pdf_url = clean_text(pdf_url)
    if not pdf_url:
        return False

    low = pdf_url.lower()

    # URL dinámica real de ficha técnica por producto de Orkli
    if "p_p_resource_id=documento" in low and "p_p_resource_id=documentos" not in low:
        return False

    if "_orklicatalogo_war_orkliportlet_referencia=" in low:
        return False

    # PDFs tipo tarifa / catálogo
    if "/documents/" in low:
        keywords = [
            "tarifa",
            "repuestos",
            "catalog",
            "catalogo",
            "catálogo",
            "pvp",
            "price-list",
            "price list",
        ]
        return any(k in low for k in keywords)

    return False


def infer_doc_kind(pdf_url: str, source_url: str = "") -> str:
    pdf_url = clean_text(pdf_url)

    if not pdf_url:
        return "none"

    low = pdf_url.lower()

    # Ficha técnica real por producto
    if "p_p_resource_id=documento" in low and "p_p_resource_id=documentos" not in low:
        return "tech_sheet"

    if "_orklicatalogo_war_orkliportlet_referencia=" in low:
        return "tech_sheet"

    # Catálogo / tarifa
    if is_catalog_or_tariff_pdf_url(pdf_url, source_url):
        return "catalog_pdf"

    # Cualquier otro PDF público no identificado como tarifa
    if pdf_url.startswith("http"):
        return "tech_sheet"

    return "none"


def finalize_media_fields(row: dict) -> dict:
    pdf_url = clean_text(row.get("pdf_url"))
    local_pdf = clean_text(row.get("local_pdf"))
    local_image = clean_text(row.get("local_image"))
    current_doc_status = clean_text(row.get("doc_status"))
    source_url = clean_text(row.get("source_url"))

    has_pdf_url = bool(pdf_url)
    has_local_pdf = bool(local_pdf)
    has_local_image = bool(local_image)
    is_catalog_pdf = has_pdf_url and is_catalog_or_tariff_pdf_url(pdf_url, source_url)

    if has_local_pdf:
        row["doc_kind"] = "tech_sheet"
        row["doc_status"] = "public_tech_doc_found"
    elif current_doc_status == "invalid_pdf_blocked":
        row["doc_kind"] = "none"
        row["doc_status"] = "invalid_pdf_blocked"
    elif is_catalog_pdf:
        row["doc_kind"] = "catalog_pdf"
        row["doc_status"] = "catalog_pdf_only"
    else:
        row["doc_kind"] = "none"
        row["doc_status"] = "no_public_tech_doc"

    if has_local_image and has_local_pdf:
        row["media_status"] = "pdf_e_imagen"
    elif has_local_pdf:
        row["media_status"] = "solo_pdf"
    elif has_local_image:
        row["media_status"] = "solo_imagen"
    elif is_catalog_pdf:
        row["media_status"] = "catalogo_sin_descarga"
    else:
        row["media_status"] = "sin_media"

    row["final_pdf_url"] = pdf_url if has_local_pdf else ""
    return row


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

        df.loc[idx, "local_image"] = ""
        df.loc[idx, "local_pdf"] = ""
        df.loc[idx, "final_image_url"] = image_url if image_url.startswith("http") else ""
        df.loc[idx, "final_pdf_url"] = ""

        if estado != "encontrado":
            df.loc[idx, "media_status"] = "no_encontrado"
            df.loc[idx, "doc_kind"] = "none"
            df.loc[idx, "doc_status"] = "not_matched"
            df.loc[idx, "final_image_url"] = ""
            df.loc[idx, "final_pdf_url"] = ""
            df.loc[idx, "local_pdf"] = ""
            continue

        doc_kind = clean_text(row.get("doc_kind")) or infer_doc_kind(pdf_url, source_url)
        df.loc[idx, "doc_kind"] = doc_kind

        if doc_kind == "tech_sheet":
            df.loc[idx, "doc_status"] = "public_tech_doc_found"
            df.loc[idx, "final_pdf_url"] = pdf_url if pdf_url.startswith("http") else ""
        elif doc_kind == "catalog_pdf":
            df.loc[idx, "doc_status"] = "catalog_pdf_only"
            df.loc[idx, "final_pdf_url"] = ""
        else:
            df.loc[idx, "doc_status"] = "no_public_tech_doc"
            df.loc[idx, "final_pdf_url"] = ""

        base_name = safe_name(f"{brand}_{matched_ref}" if brand else matched_ref)

        pdf_path = PDFS_DIR / f"{base_name}.pdf"

        try:
            if image_url.startswith("http"):
                ext = get_extension_from_url(image_url, default=".jpg")
                img_path = IMAGES_DIR / f"{base_name}{ext}"
                download_file(image_url, img_path)
                df.loc[idx, "local_image"] = str(img_path)
        except Exception as exc:
            print(f"[IMG ERROR] {matched_ref}: {exc}")

        try:
            if doc_kind == "tech_sheet" and pdf_url.startswith("http"):
                if pdf_path.exists():
                    pdf_path.unlink()

                download_pdf_file(pdf_url, pdf_path)
                df.loc[idx, "local_pdf"] = str(pdf_path)
        except Exception as exc:
            if pdf_path.exists():
                pdf_path.unlink()

            df.loc[idx, "pdf_url"] = ""
            df.loc[idx, "final_pdf_url"] = ""
            df.loc[idx, "local_pdf"] = ""
            df.loc[idx, "doc_status"] = "invalid_pdf_blocked"

            print(f"[PDF ERROR] {matched_ref}: {exc}")

        row_result = df.loc[idx].to_dict()
        row_result = finalize_media_fields(row_result)

        for key, value in row_result.items():
            if key in df.columns:
                df.loc[idx, key] = value

    return df