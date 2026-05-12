from pydantic import AfterValidator, BaseModel, Field
from typing import Annotated, Optional, Sequence, ClassVar
from app.models.request import ListRequest
UppercaseStr = Annotated[str, AfterValidator(lambda v: v.upper())]

class CountryList(ListRequest):

    name: Optional[str] = None
    code: Optional[str] = None
    status: Optional[bool] = None

    allowed_sort_fields: ClassVar[Sequence[str]] = (
        "name",
        "code",
        "created_at",
        "updated_at",
    )


class CityList(ListRequest):
    name: Optional[str] = None 
    country: Optional[str] = None
    is_popular: Optional[bool] = None
    _allowed_sort_fields = ['name', 'country']

class LocationList(ListRequest):
    name: Optional[str] = None 
    city: Optional[str] = None
    country: Optional[str] = None
    _allowed_sort_fields = ['name', 'city', 'country']

class CountryCreate(BaseModel):
    name: str
    code: UppercaseStr = Field(..., min_length=2, max_length=3)
    dial_code: int = Field(..., ge=1, le=999)
    status: bool = True

class CityCreate(BaseModel):
    name: str
    country: str
    is_popular: bool = False
    image: Optional[str] = None
    is_active: bool = True
    


class LocationCreate(BaseModel):
    name: str
    city: str
    country: str

class CountryUpdate(BaseModel):
    name: Optional[str] = None
    code: Optional[UppercaseStr] = Field(None, min_length=2, max_length=3)
    dial_code: Optional[int] = Field(None, ge=1, le=999)
    status: Optional[bool] = None
class CityUpdate(BaseModel):

    name: Optional[str] = None
    country: Optional[str] = None
    image: Optional[str] = None
    is_popular: Optional[bool] = None
    is_active: Optional[bool] = None

class LocationUpdate(BaseModel):
    name: Optional[str] = None
    city: Optional[str] = None
    country: Optional[str] = None
    

