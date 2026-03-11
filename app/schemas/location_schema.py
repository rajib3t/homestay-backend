from pydantic import BaseModel, Field
from pydantic import ConfigDict
from app.schemas.response import BaseResponse
from app.schemas.response import PaginationResponse
class Location(BaseModel):
    name: str
    city: str
    country: str

class City(BaseModel):
    name: str
    country: str
    is_popular: bool = False
    locations: list[Location] = Field(default_factory=list)

class Country(BaseModel):
    name: str
    code: str = Field(..., min_length=2, max_length=3, uppercase=True)
    dial_code: int = Field(..., ge=1, le=999)
    cities: list[City] = Field(default_factory=list)
    status: bool = True

class CountryOut(Country):
    id: str = Field(..., alias="_id")

    model_config = ConfigDict(populate_by_name=True)


class CountryResponse(BaseResponse):
    data: CountryOut


class CountriesResponse(PaginationResponse):
    data: list[CountryOut] = Field(default_factory=list)


class CityResponse(BaseResponse):
    data: City
    