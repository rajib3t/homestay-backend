from pydantic import BaseModel, EmailStr, Field
from typing import Optional

class CountryCreate(BaseModel):
    name: str
    code: str = Field(..., min_length=2, max_length=3, uppercase=True)
    dial_code: int = Field(..., ge=1, le=999)
    status: bool = True

class CityCreate(BaseModel):
    name: str
    country: str

class LocationCreate(BaseModel):
    name: str
    city: str
    country: str

class CountryUpdate(BaseModel):
    name: Optional[str] = None
    code: Optional[str] = Field(None, min_length=2, max_length=3, uppercase=True)
    dial_code: Optional[int] = Field(None, ge=1, le=999)
    status: Optional[bool] = None
class CityUpdate(BaseModel):
    name: Optional[str] = None
    country: Optional[str] = None

class LocationUpdate(BaseModel):
    name: Optional[str] = None
    city: Optional[str] = None
    country: Optional[str] = None

