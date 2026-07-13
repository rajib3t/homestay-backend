from typing import List, Optional

from pydantic import ConfigDict
from pydantic.dataclasses import dataclass


@dataclass(config=ConfigDict(extra="forbid"))
class Amenity:
    
    name: str
    allow: bool = True

@dataclass(config=ConfigDict(extra="forbid"))
class Facility:
    
    name: str
    allow: bool = True

@dataclass(config=ConfigDict(extra="forbid"))
class Room:
    name: str
    type: str



@dataclass(config=ConfigDict(extra="forbid"))
class PropertyDTO:
    # Required identity and location fields
    name: str
    vendor: str
    location: str
    city: str
    country: str
    address: str
    longitude: float
    latitude: float

    # Details
    description: Optional[str] = None
    trade_license_number: Optional[str] = None

    # Info
    star_rating: Optional[float] = None
    listing_price: Optional[float] = None
    sale_price: Optional[float] = None
    check_in_time: Optional[str] = None
    checkout_time: Optional[str] = None

    # Files and Media
    cover_image: Optional[str] = None
    feature_image: Optional[str] = None
    trade_license: Optional[str] = None
    gallery_images: Optional[List[str]] = None

    # Attributes
    amenities: Optional[List[Amenity]] = None
    facilities: Optional[List[Facility]] = None
    rooms: Optional[List[Room]] = None

    # Tax
    tax_name: Optional[str] = None
    tax_percentage: Optional[float] = None