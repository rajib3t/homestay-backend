from dataclasses import dataclass, field
from typing import Dict

@dataclass
class Amenity:
    name: str
    icon: str = None
    status: bool = True
    created_by: str = None
    updated_by: str = None



@dataclass
class AmenityQuery:
    page: int = 1
    size: int = 10
    sort_by: str = "created_at"
    sort_order: str = "desc"
    filters: Dict = field(default_factory=dict)