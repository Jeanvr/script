from src.providers.orkli.config import OrkliProvider
from src.providers.bosch_homecomfort.config import BoschHomeComfortProvider


PROVIDERS = {
    "orkli": OrkliProvider(),
    "bosch_homecomfort": BoschHomeComfortProvider(),
}


def get_provider(key: str):
    if key not in PROVIDERS:
        raise ValueError(f"Proveedor no soportado: {key}. Disponibles: {', '.join(PROVIDERS)}")
    return PROVIDERS[key]