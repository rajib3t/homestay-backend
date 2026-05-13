from dataclasses import dataclass, field
from typing import Dict


@dataclass
class LocationQuery:
    page: int = 1
    size: int = 10
    sort_by: str = "created_at"
    sort_order: str = "desc"
    filters: Dict = field(default_factory=dict)