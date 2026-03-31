from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent.parent

DATA_DIR = BASE_DIR / "data"
INPUT_DIR = DATA_DIR / "input"
INDEX_DIR = DATA_DIR / "index"
OUTPUT_DIR = DATA_DIR / "output"

IMAGES_DIR = OUTPUT_DIR / "images"
PDFS_DIR = OUTPUT_DIR / "pdfs"
REPORTS_DIR = OUTPUT_DIR / "reports"

for path in [INPUT_DIR, INDEX_DIR, OUTPUT_DIR, IMAGES_DIR, PDFS_DIR, REPORTS_DIR]:
    path.mkdir(parents=True, exist_ok=True)


def get_first_input_excel():
    excel_files = list(INPUT_DIR.glob("*.xlsx")) + list(INPUT_DIR.glob("*.xls"))
    if not excel_files:
        raise FileNotFoundError(f"No hay ningún archivo Excel dentro de {INPUT_DIR}")
    return excel_files[0]