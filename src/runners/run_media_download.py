import pandas as pd

from src.core.paths import REPORTS_DIR
from src.pipelines.media_download import run_media_download


def main():
    print("RUNNING MEDIA FILE:", __file__)

    input_file = REPORTS_DIR / "lookup_orkli.xlsx"
    output_file = REPORTS_DIR / "lookup_orkli_with_media.xlsx"

    df = pd.read_excel(input_file, dtype=object, engine="openpyxl")
    df = df.fillna("")

    print("DTYPES ANTES:")
    print(df.dtypes)

    df = run_media_download(df)

    print("DTYPES DESPUÉS:")
    print(df.dtypes)

    df.to_excel(output_file, index=False)

    print(f"Reporte con media guardado en: {output_file}")
    print(df["media_status"].value_counts(dropna=False))


if __name__ == "__main__":
    main()