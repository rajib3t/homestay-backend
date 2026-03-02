from pydantic import BaseModel, EmailStr
from typing import Optional

class UserCreate(BaseModel):

    username: str
    email: EmailStr
    password: str
    user_type: str
    first_name: str
    last_name: str
    mobile: str

class UserUpdate(BaseModel):
    email: Optional[EmailStr] = None
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    mobile: Optional[str] = None
