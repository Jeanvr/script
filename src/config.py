from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
INPUT_DIR = BASE_DIR / "data" / "input"

excel_files = list(INPUT_DIR.glob("*.xlsx")) + list(INPUT_DIR.glob("*.xls"))
if not excel_files:
    raise FileNotFoundError(
        f"No hay ningún archivo Excel dentro de {INPUT_DIR}"
    )

INPUT_FILE = excel_files[0]

OUTPUT_DIR = BASE_DIR / "data" / "output"
IMAGES_DIR = OUTPUT_DIR / "images"
PDFS_DIR = OUTPUT_DIR / "pdfs"
OUTPUT_EXCEL = OUTPUT_DIR / "demo_resultado.xlsx"

OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
IMAGES_DIR.mkdir(parents=True, exist_ok=True)
PDFS_DIR.mkdir(parents=True, exist_ok=True)