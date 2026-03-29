import sys
from pathlib import Path

from excel_utils import load_excel, add_demo_columns
from config import INPUT_FILE, OUTPUT_EXCEL, IMAGES_DIR, PDFS_DIR
from ariston_demo_data import ARISTON_DEMO_DATA
from downloader import download_file, get_extension_from_url


def build_image_name(ref: str, image_url: str) -> str:
    ext = get_extension_from_url(image_url, ".jpg")
    return f"SS12_ARISTON_{ref}_IMG{ext}"


def build_pdf_name(ref: str) -> str:
    return f"SS12_ARISTON_{ref}_FT.pdf"


def main():
    print("=== INICIO DEMO ===")
    print(f"Python en uso: {sys.executable}")
    print(f"Excel detectado: {INPUT_FILE}")

    df = load_excel(INPUT_FILE)
    df = add_demo_columns(df)

    print(f"Filas detectadas: {len(df)}")

    for idx, row in df.iterrows():
        ref = str(row["referencia"]).strip()
        nombre = str(row["nombre"]).strip()

        print(f"\nProcesando {ref} | {nombre}")

        product_data = ARISTON_DEMO_DATA.get(ref)
        if not product_data:
            df.at[idx, "estado_demo"] = "no_mapeado"
            print("  - No hay mapeo para esta referencia")
            continue

        image_ok = False
        pdf_ok = False

        try:
            image_name = build_image_name(ref, product_data["image_url"])
            image_path = IMAGES_DIR / image_name
            download_file(product_data["image_url"], image_path)
            df.at[idx, "imagen_demo"] = str(image_path)
            image_ok = True
            print(f"  - Imagen OK: {image_name}")
        except Exception as e:
            print(f"  - Error imagen: {e}")

        try:
            pdf_name = build_pdf_name(ref)
            pdf_path = PDFS_DIR / pdf_name
            download_file(product_data["pdf_url"], pdf_path)
            df.at[idx, "ficha_demo"] = str(pdf_path)
            pdf_ok = True
            print(f"  - Ficha OK: {pdf_name}")
        except Exception as e:
            print(f"  - Error ficha: {e}")

        if image_ok and pdf_ok:
            df.at[idx, "estado_demo"] = "OK"
        elif image_ok or pdf_ok:
            df.at[idx, "estado_demo"] = "parcial"
        else:
            df.at[idx, "estado_demo"] = "error"

    df.to_excel(OUTPUT_EXCEL, index=False)
    print(f"\nExcel demo guardado en: {OUTPUT_EXCEL}")
    print("=== FIN DEMO ===")


if __name__ == "__main__":
    main()