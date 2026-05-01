from typing import Optional

from pydantic import BaseModel, EmailStr, Field
from pydantic import ConfigDict


class CompanyResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: str
    user_id: str
    name: str = Field(..., description="Company name")
    email: str = Field(..., description="Company email")
    phone: str = Field(..., description="Company phone")
    
    created_at: Optional[str] = None
    updated_at: Optional[str] = None