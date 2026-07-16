from typing import Optional
from pydantic import BaseModel, ConfigDict, Field

from app.models.property_model import PropertySchema as Property
from app.schemas.response import BaseResponse, PaginationMeta


class PropertySchema(Property):
    model_config = ConfigDict(populate_by_name=True)

    id: str = Field(..., alias="_id")

class CreatePropertyCreatedData(BaseModel):
    model_config = ConfigDict(populate_by_name=True)
    id: str 


class CreatePropertyResponseSchema(BaseResponse):
    model_config = ConfigDict(populate_by_name=True)
    data: CreatePropertyCreatedData

class Amenities(BaseModel):
    model_config = ConfigDict(populate_by_name=True)
    name: str
    allowed: bool

class Facilities(BaseModel):
    model_config = ConfigDict(populate_by_name=True)
    name: str
    allowed: bool

class PropertyListItem(BaseModel):
    model_config = ConfigDict(populate_by_name=True)
    id: str
    name: str
    price: float
    sale_price: Optional[float] = None
    facilities: list[Facilities]
    amenities: list[Amenities]
    city_name: str
    country_name: str
    location_name: str
    feature_image: str

class PropertyListResponseSchema(BaseResponse):
    model_config = ConfigDict(populate_by_name=True)
    data: list[PropertyListItem]
    meta: PaginationMeta
