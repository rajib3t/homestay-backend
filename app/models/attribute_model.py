from pydantic import BaseModel, Field
from typing import Optional, ClassVar, Sequence

from app.models.request import ListRequest

class CreateAmenity(BaseModel):
    name: str
    icon: Optional[str] = None
    status: Optional[bool] = Field(default=True, description="Status of the amenity, e.g., true for active or false for inactive")


class ListAmenities(ListRequest):
    name: Optional[str] = None
    status: Optional[bool] = None
    allowed_sort_fields: ClassVar[Sequence[str]] = ['name', 'status', 'created_at']
    

class UpdateAmenity(BaseModel):
    name: Optional[str] = None
    icon: Optional[str] = None
    status: Optional[bool] = Field(None, description="Status of the amenity, e.g., true for active or false for inactive")

class UpdateAmenityStatus(BaseModel):
    status: bool = Field(..., description="Status of the amenity, e.g., true for active or false for inactive")

class CreateFacility(BaseModel):
    name: str
    icon: Optional[str] = None
    status: Optional[bool] = Field(default=True, description="Status of the facility, e.g., true for active or false for inactive")

class ListFacilities(ListRequest):
    name: Optional[str] = None
    status: Optional[bool] = None
    allowed_sort_fields: ClassVar[Sequence[str]] = ['name', 'status', 'created_at']

class UpdateFacility(BaseModel):
    name: Optional[str] = None
    icon: Optional[str] = None
    status: Optional[bool] = Field(None, description="Status of the facility, e.g., true for active or false for inactive")

class UpdateFacilityStatus(BaseModel):
    status: bool = Field(..., description="Status of the facility, e.g., true for active or false for inactive")

class CreateRoomType(BaseModel):
    name: str
    capacity: int
    status: Optional[bool] = Field(default=True, description="Status of the room type, e.g., true for active or false for inactive")

class ListRoomTypes(ListRequest):
    name: Optional[str] = None
    capacity: Optional[int] = None
    status: Optional[bool] = None
    allowed_sort_fields: ClassVar[Sequence[str]] = ['name', 'capacity', 'status', 'created_at']

class UpdateRoomType(BaseModel):
    name: Optional[str] = None
    capacity: Optional[int] = None
    status: Optional[bool] = Field(None, description="Status of the room type, e.g., true for active or false for inactive")

class UpdateRoomTypeStatus(BaseModel):
    status: bool = Field(..., description="Status of the room type, e.g., true for active or false for inactive")