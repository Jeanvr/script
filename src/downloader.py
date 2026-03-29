from pathlib import Path
import requests

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/122.0.0.0 Safari/537.36"
    )
}


def download_file(url: str, destination: Path, timeout: int = 60):
    destination.parent.mkdir(parents=True, exist_ok=True)

    response = requests.get(url, headers=HEADERS, timeout=timeout, allow_redirects=True)
    response.raise_for_status()

    destination.write_bytes(response.content)
    return destination


def get_extension_from_url(url: str, default: str = ".jpg") -> str:
    clean_url = url.split("?")[0].lower()

    if clean_url.endswith(".png"):
        return ".png"
    if clean_url.endswith(".webp"):
        return ".webp"
    if clean_url.endswith(".jpeg"):
        return ".jpeg"
    if clean_url.endswith(".jpg"):
        return ".jpg"
    if clean_url.endswith(".pdf"):
        return ".pdf"

    return default