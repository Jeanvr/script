import pandas as pd

REQUIRED_COLUMNS = {"nombre", "referencia"}


def load_input_excel(path):
    df = pd.read_excel(path)
    df.columns = [str(c).strip().lower() for c in df.columns]

    missing = REQUIRED_COLUMNS - set(df.columns)
    if missing:
        raise ValueError(f"Faltan columnas en el Excel: {missing}")

    df = df.copy()
    df = df[df["referencia"].notna()]
    df["referencia"] = (
        df["referencia"]
        .astype(str)
        .str.strip()
        .str.replace(r"\.0$", "", regex=True)
    )
    df["nombre"] = df["nombre"].astype(str).str.strip()

    return df


def add_result_columns(df):
    df = df.copy()
    df["brand"] = ""
    df["matched_ref"] = ""
    df["matched_name"] = ""
    df["image_url"] = ""
    df["pdf_url"] = ""
    df["source_url"] = ""
    df["match_type"] = ""
    df["estado"] = "pendiente"
    return df