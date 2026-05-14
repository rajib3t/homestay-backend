from pydantic import BaseModel, Field
from typing import Optional
from app.schemas.response import BaseResponse, PaginationResponse

class Amenity(BaseModel):
    id: str
    name: str
    icon: Optional[str] = None
    status: bool = Field(default=True, description="Status of the amenity, e.g., true for active or false for inactive")

class AmenityResponse(BaseResponse):
    data: Amenity

class AmenitiesResponse(PaginationResponse):
    data: list[Amenity] = Field(default_factory=list)


class Facility(BaseModel):
    id: str 
    name: str
    icon: Optional[str] = None
    status: bool = Field(default=True, description="Status of the facility, e.g., true for active or false for inactive")

class FacilityResponse(BaseResponse):
    data: Facility

class FacilitiesResponse(PaginationResponse):
    data: list[Facility] = Field(default_factory=list)

class RoomType(BaseModel):
    id: str = Field(..., alias="_id")
    name: str
    capacity: int
    status: bool = Field(default=True, description="Status of the room type, e.g., true for active or false for inactive")

class RoomTypeResponse(BaseResponse):
    data: RoomType

class RoomTypesResponse(PaginationResponse):
    data: list[RoomType] = Field(default_factory=list)
