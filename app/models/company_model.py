from pydantic import BaseModel, Field
from typing import Optional

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
    


class CompanyUpdate(CompanyBase):
    name: Optional[str] = Field(None, description="Company name")
    email: Optional[str] = Field(None, description="Company email")
    phone: Optional[str] = Field(None, description="Company phone")
    

