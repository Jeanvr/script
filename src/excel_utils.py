import pandas as pd


def load_excel(path):
    df = pd.read_excel(path)
    df.columns = [str(c).strip().lower() for c in df.columns]

    expected = {"nombre", "referencia"}
    missing = expected - set(df.columns)
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

    return df


def add_demo_columns(df):
    df = df.copy()
    df["imagen_demo"] = ""
    df["ficha_demo"] = ""
    df["estado_demo"] = "pendiente"
    return df