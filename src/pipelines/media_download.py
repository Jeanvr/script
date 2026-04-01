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


def run_media_download(df_matches: pd.DataFrame) -> pd.DataFrame:
    df = df_matches.copy()

    # asegurar columnas y forzar tipo texto
    for col in ["local_image", "local_pdf", "media_status"]:
        if col not in df.columns:
            df[col] = ""
        df[col] = df[col].astype(str)

    for idx, row in df.iterrows():
        estado = clean_text(row.get("estado"))
        brand = clean_text(row.get("brand"))
        matched_ref = clean_text(row.get("matched_ref")) or clean_text(row.get("referencia")) or str(idx)
        image_url = clean_text(row.get("image_url"))
        pdf_url = clean_text(row.get("pdf_url"))

        if estado != "encontrado":
            df.loc[idx, "media_status"] = "no_encontrado"
            continue

        base_name = safe_name(f"{brand}_{matched_ref}" if brand else matched_ref)

        image_ok = False
        pdf_ok = False

        try:
            if pdf_url.startswith("http"):
                pdf_path = PDFS_DIR / f"{base_name}.pdf"
                download_file(pdf_url, pdf_path)
                df.loc[idx, "local_pdf"] = str(pdf_path)
                pdf_ok = True
        except Exception as exc:
            print(f"[PDF ERROR] {matched_ref}: {exc}")

        try:
            if image_url.startswith("http"):
                ext = get_extension_from_url(image_url, default=".jpg")
                img_path = IMAGES_DIR / f"{base_name}{ext}"
                download_file(image_url, img_path)
                df.loc[idx, "local_image"] = str(img_path)
                image_ok = True
        except Exception as exc:
            print(f"[IMG ERROR] {matched_ref}: {exc}")

        if pdf_ok and image_ok:
            df.loc[idx, "media_status"] = "pdf_e_imagen"
        elif pdf_ok:
            df.loc[idx, "media_status"] = "solo_pdf"
        elif image_ok:
            df.loc[idx, "media_status"] = "solo_imagen"
        else:
            df.loc[idx, "media_status"] = "sin_media"

    return df