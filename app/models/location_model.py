from pydantic import AfterValidator, BaseModel, EmailStr, Field
from typing import Annotated, Optional

UppercaseStr = Annotated[str, AfterValidator(lambda v: v.upper())]
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


class LocationCreate(BaseModel):
    name: str
    city: str
    country: str

class CountryUpdate(BaseModel):
    name: Optional[str] = None
    code: Optional[UppercaseStr] = Field(None, min_length=2, max_length=3)
    dial_code: Optional[int] = Field(None, ge=1, le=999)
    
class CityUpdate(BaseModel):

    name: Optional[str] = None
    country: Optional[str] = None
    is_popular: Optional[bool] = None
    image: Optional[str] = None
class LocationUpdate(BaseModel):
    name: Optional[str] = None
    city: Optional[str] = None
    country: Optional[str] = None
    image: Optional[str] = None

