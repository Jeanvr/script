import re
import unicodedata


def normalize_text(value: str) -> str:
    value = str(value or "").strip().lower()
    value = unicodedata.normalize("NFKD", value)
    value = "".join(ch for ch in value if not unicodedata.combining(ch))
    value = re.sub(r"\s+", " ", value)
    return value.strip()


def normalize_ref(value: str) -> str:
    value = str(value or "").strip().upper()
    value = value.replace(" ", "")
    value = re.sub(r"[^A-Z0-9]", "", value)

    if re.match(r"^[A-Z]\d+00$", value):
        value = value[:-2]

    return value