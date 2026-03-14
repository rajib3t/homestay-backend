from pydantic import BaseModel, Field
from pydantic import ConfigDict
from typing import Optional
from app.schemas.response import BaseResponse
from app.schemas.response import PaginationResponse
class Location(BaseModel):
    id: str = Field(..., alias="_id")
    name: str
    city: str
    country: str


class LocationOut(BaseModel):
    id: str = Field(..., alias="_id")
    name: str
    city: Optional[str] = None
    country: Optional[str] = None

    model_config = ConfigDict(populate_by_name=True)

class LocationResponse(BaseResponse):
    data: LocationOut

class LocationsResponse(PaginationResponse):
    data: list[LocationOut] = Field(default_factory=list)

class City(BaseModel):
    name: str
    country: str
    image: Optional[str] = None
    is_popular: bool = False
    locations: list[Location] = Field(default_factory=list)

class Country(BaseModel):
    name: str
    code: str = Field(..., min_length=2, max_length=3, uppercase=True)
    dial_code: int = Field(..., ge=1, le=999)
    cities: list[City] = Field(default_factory=list)
    status: bool = True

class CountryOut(BaseModel):
    id: str = Field(..., alias="_id")
    name: str
    code: str = Field(..., min_length=2, max_length=3, uppercase=True)
    dial_code: int = Field(..., ge=1, le=999)
    status: bool = True
    city_count: int = 0

    model_config = ConfigDict(populate_by_name=True)

class CityOut(BaseModel):
    id: str = Field(..., alias="_id")
    name: str
    country: str
    image: Optional[str] = None
    is_popular: bool = False
    location_count: int = 0
    locations: list[LocationOut] = Field(default_factory=list)

    model_config = ConfigDict(populate_by_name=True)

class CountryResponse(BaseResponse):
    data: CountryOut


class CountriesResponse(PaginationResponse):
    data: list[CountryOut] = Field(default_factory=list)


class CityResponse(BaseResponse):
    data: CityOut
    

class CitiesOnlyResponse(BaseResponse):
    data: list[CityOut] = Field(default_factory=list)


class CitiesResponse(PaginationResponse):
    data: list[CityOut] = Field(default_factory=list)
    