import argparse
import pandas as pd

from src.core.excel import load_input_excel
from src.core.paths import get_first_input_excel, INDEX_DIR, REPORTS_DIR
from src.pipelines.lookup import run_lookup
from src.pipelines.media_download import run_media_download
from src.providers.registry import get_provider


def build_index(provider_key: str):
    provider = get_provider(provider_key)
    all_items = []

    for spider in provider.build_spiders():
        all_items.extend(spider.scrape())

    df = pd.DataFrame(all_items)
    if not df.empty:
        if "normalized_ref" in df.columns:
            df = df.drop_duplicates(subset=["normalized_ref"], keep="first")

    output = INDEX_DIR / provider.config.index_filename
    df.to_csv(output, index=False, encoding="utf-8-sig")
    print(f"Índice guardado en: {output}")
    print(f"Total: {len(df)}")


def lookup(provider_key: str):
    provider = get_provider(provider_key)

    input_excel = get_first_input_excel()
    input_df = load_input_excel(input_excel)

    index_df = pd.read_csv(
        INDEX_DIR / provider.config.index_filename,
        dtype=str,
        sep=None,
        engine="python",
        encoding="utf-8-sig",
    ).fillna("")
    index_df.columns = [str(c).replace("\ufeff", "").strip() for c in index_df.columns]

    result_df = run_lookup(input_df, index_df)
    output = REPORTS_DIR / provider.config.lookup_filename
    result_df.to_excel(output, index=False)
    print(f"Resultado guardado en: {output}")


def download_media(provider_key: str):
    provider = get_provider(provider_key)

    input_file = REPORTS_DIR / provider.config.lookup_filename
    output_file = REPORTS_DIR / provider.config.lookup_media_filename

    df = pd.read_excel(input_file, dtype=object, engine="openpyxl").fillna("")
    df = run_media_download(df, provider)
    df.to_excel(output_file, index=False)

    print(f"Reporte con media guardado en: {output_file}")


def main():
    parser = argparse.ArgumentParser()
    sub = parser.add_subparsers(dest="command", required=True)

    p1 = sub.add_parser("build-index")
    p1.add_argument("provider")

    p2 = sub.add_parser("lookup")
    p2.add_argument("provider")

    p3 = sub.add_parser("download-media")
    p3.add_argument("provider")

    args = parser.parse_args()

    if args.command == "build-index":
        build_index(args.provider)
    elif args.command == "lookup":
        lookup(args.provider)
    elif args.command == "download-media":
        download_media(args.provider)


if __name__ == "__main__":
    main()