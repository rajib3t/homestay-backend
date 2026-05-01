from typing import Optional

from pydantic import BaseModel, EmailStr, Field
from pydantic import ConfigDict
from app.models.address_model import AddressResponse


class CompanyResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: str
    user_id: str
    name: str = Field(..., description="Company name")
    email: str = Field(..., description="Company email")
    phone: str = Field(..., description="Company phone")
    address: Optional[dict] = Field(None, description="Company address")

    created_at: Optional[str] = None
    updated_at: Optional[str] = None