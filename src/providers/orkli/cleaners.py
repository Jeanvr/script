import re


def clean_orkli_name(text: str) -> str:
    text = str(text or "").strip()
    if not text:
        return ""

    junk_parts = [
        "Componentes de radiador ACC - Accesorios de unión",
        "ACC - Accesorios de unión",
        "Componentes de radiador",
    ]

    for part in junk_parts:
        text = text.replace(part, "")

    text = re.sub(r"\s+", " ", text).strip(" -|;,.")
    return text
