from pydantic import BaseModel, Field
from typing import Optional
from app.models.address_model import AddressCreate, AddressUpdate

class CompanyBase(BaseModel):
    user_id: str = Field(..., description="User ID")
    name: str = Field(..., description="Company name")
    email: str = Field(..., description="Company email")
    phone: str = Field(..., description="Company phone")


class CompanyCreate(CompanyBase):
    user_id: str = Field(..., description="User ID")
    name: str = Field(..., description="Company name")
    email: str = Field(..., description="Company email")
    phone: str = Field(..., description="Company phone")
    address: Optional[AddressCreate] = Field(None, description="Company address")


class CompanyUpdate(CompanyBase):
    user_id: Optional[str] = Field(None, description="User ID")
    name: Optional[str] = Field(None, description="Company name")
    email: Optional[str] = Field(None, description="Company email")
    phone: Optional[str] = Field(None, description="Company phone")
    address: Optional[AddressUpdate] = Field(None, description="Company address")

