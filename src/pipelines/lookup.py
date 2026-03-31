import pandas as pd
from src.core.matcher import build_index_maps, match_row
from src.core.excel import add_result_columns


def run_lookup(input_df: pd.DataFrame, index_df: pd.DataFrame) -> pd.DataFrame:
    df = add_result_columns(input_df)
    by_ref, by_name = build_index_maps(index_df)

    for idx, row in df.iterrows():
        match, match_type = match_row(row["referencia"], row["nombre"], by_ref, by_name)

        if not match:
            df.at[idx, "estado"] = "no_encontrado"
            df.at[idx, "match_type"] = str(match_type)
            continue

        df.at[idx, "brand"] = str(match.get("brand", ""))
        df.at[idx, "matched_ref"] = str(match.get("supplier_ref", ""))
        df.at[idx, "matched_name"] = str(match.get("name", ""))
        df.at[idx, "image_url"] = str(match.get("image_url", ""))
        df.at[idx, "pdf_url"] = str(match.get("pdf_url", ""))
        df.at[idx, "source_url"] = str(match.get("source_url", ""))
        df.at[idx, "match_type"] = str(match_type)
        df.at[idx, "estado"] = "encontrado"

    return df
