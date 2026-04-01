from dataclasses import dataclass, field


@dataclass
class ProviderConfig:
    key: str
    index_filename: str
    lookup_filename: str
    lookup_media_filename: str
    brand_labels: list[str] = field(default_factory=list)