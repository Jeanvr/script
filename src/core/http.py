from pathlib import Path
import requests

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/122.0.0.0 Safari/537.36"
    )
}

SESSION = requests.Session()
SESSION.headers.update(HEADERS)


def get(url: str, timeout: int = 60) -> requests.Response:
    response = SESSION.get(url, timeout=timeout, allow_redirects=True)
    response.raise_for_status()
    return response


def is_real_pdf_content(content: bytes) -> bool:
    return bool(content) and content.startswith(b"%PDF-")


def download_file(url: str, destination: Path, timeout: int = 60) -> Path:
    destination.parent.mkdir(parents=True, exist_ok=True)
    response = get(url, timeout=timeout)
    destination.write_bytes(response.content)
    return destination


def download_pdf_file(url: str, destination: Path, timeout: int = 60) -> Path:
    destination.parent.mkdir(parents=True, exist_ok=True)
    response = get(url, timeout=timeout)
    content = response.content

    if not is_real_pdf_content(content):
        raise ValueError(f"El contenido descargado no es un PDF real: {url}")

    destination.write_bytes(content)
    return destination


def get_extension_from_url(url: str, default: str = ".jpg") -> str:
    clean_url = url.split("?")[0].lower()
    for ext in [".png", ".webp", ".jpeg", ".jpg", ".pdf"]:
        if clean_url.endswith(ext):
            return ext
    return default