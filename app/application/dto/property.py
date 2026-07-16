from typing import Dict, List, Optional

from attrs import field
from pydantic import BaseModel, ConfigDict, Field, field_validator



class PropertyQuery(BaseModel):
    model_config = ConfigDict(extra="forbid")
    page: int = 1
    size: int = 10
    sort_by: str = "created_at"
    sort_order: str = "desc"
    filters: Dict = {}

class Amenity(BaseModel):
    model_config = ConfigDict(extra="forbid")
    
    name: str
    allow: bool = True

class Facility(BaseModel):
    model_config = ConfigDict(extra="forbid")
    
    name: str
    allow: bool = True

class Room(BaseModel):
    model_config = ConfigDict(extra="forbid")
    name: str
    type: str

class FoodOption(BaseModel):
    model_config = ConfigDict(extra="forbid")
    name: str
    allow: bool = True

class PropertyDTO(BaseModel):
    model_config = ConfigDict(extra="allow", populate_by_name=True)
    # Required identity and location fields
    name: str
    vendor: str
    location: str
    city: str
    country: str
    address: str
    longitude: float
    latitude: float
    is_published: bool = False
    is_featured: bool = False
    # Details
    description: Optional[str] = None
    trade_license_number: Optional[str] = Field(None, validation_alias="trade_licence_number")

    # Info
    star_rating: Optional[float] = None
    listing_price: Optional[float] = None
    sale_price: Optional[float] = None
    check_in_time: Optional[str] = None
    checkout_time: Optional[str] = None
    food_options: Optional[List[FoodOption]] = None
    # Files and Media
    cover_image: Optional[str] = None
    feature_image: Optional[str] = None
    trade_license: Optional[str] = Field(None, validation_alias="trade_licence")
    gallery_images: Optional[List[str]] = None

    # Attributes
    amenities: Optional[List[Amenity]] = None
    facilities: Optional[List[Facility]] = None
    rooms: Optional[List[Room]] = None

    # Tax
    tax_name: Optional[str] = None
    tax_percentage: Optional[float] = None
    
    @field_validator('*', mode='before')
    @classmethod
    def handle_extra_fields(cls, v):
        return v