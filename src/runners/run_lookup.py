import pandas as pd

from src.core.excel import load_input_excel
from src.core.paths import get_first_input_excel, INDEX_DIR, REPORTS_DIR
from src.pipelines.lookup import run_lookup


def main():
    input_excel = get_first_input_excel()
    input_df = load_input_excel(input_excel)

    print("Referencias Excel:")
    print(input_df["referencia"].tolist())

    orkli_index = pd.read_csv(
        INDEX_DIR / "orkli_products.csv",
        dtype=str,
        sep=None,
        engine="python",
        encoding="utf-8-sig"
    ).fillna("")

    orkli_index.columns = [str(c).replace("\ufeff", "").strip() for c in orkli_index.columns]

    print("Columnas índice:")
    print(orkli_index.columns.tolist())

    print("Primeras filas índice:")
    print(orkli_index.head().to_dict(orient="records"))

    print("Referencias índice:")
    print(orkli_index["supplier_ref"].tolist())

    result_df = run_lookup(input_df, orkli_index)

    output_file = REPORTS_DIR / "lookup_orkli.xlsx"
    result_df.to_excel(output_file, index=False)

    print(f"Resultado guardado en: {output_file}")
    print(result_df["estado"].value_counts(dropna=False))


if __name__ == "__main__":
    main()