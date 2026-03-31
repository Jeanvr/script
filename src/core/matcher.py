import pandas as pd
from src.core.normalize import normalize_ref, normalize_text


def build_index_maps(df_index: pd.DataFrame):
    df = df_index.copy()

    by_ref = {}
    by_name = {}

    for _, row in df.iterrows():
        ref = normalize_ref(row.get("supplier_ref", ""))
        name = normalize_text(row.get("name", ""))

        if ref and ref not in by_ref:
            by_ref[ref] = row.to_dict()

        if name and name not in by_name:
            by_name[name] = row.to_dict()

    return by_ref, by_name


def match_row(ref_value: str, name_value: str, by_ref: dict, by_name: dict):
    norm_ref = normalize_ref(ref_value)
    norm_name = normalize_text(name_value)

    if norm_ref in by_ref:
        return by_ref[norm_ref], "ref_exact"

    if norm_name in by_name:
        return by_name[norm_name], "name_exact"

    return None, "no_match"