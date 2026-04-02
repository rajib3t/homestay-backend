from pydantic import BaseModel, EmailStr, Field, field_validator
from typing import Optional

from app.models.request import ListRequest

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


class ListUsers(ListRequest):
    sort_by: Optional[str] = Field("first_name", description="Field to sort by")
    username: Optional[str] = None
    email: Optional[EmailStr] = None
    user_type: Optional[str] = None
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    mobile: Optional[str] = None
    _allowed_sort_fields = ['username', 'email', 'user_type', 'first_name', 'last_name', 'mobile']

    @field_validator('sort_by', mode='before')
    @classmethod
    def _normalize_sort_by_alias(cls, value):
        if value == 'name':
            return 'first_name'
        return value