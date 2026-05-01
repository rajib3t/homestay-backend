from typing import Optional

from pydantic import BaseModel, EmailStr, Field
from pydantic import ConfigDict
from app.schemas.response import BaseResponse, PaginationResponse
from app.schemas.company_schema import CompanyResponse
class UserBase(BaseModel):
    username: str
    email: EmailStr
    user_type: str
    first_name: str
    last_name: str
    mobile: str
    image: Optional[str] = None
    company: Optional[CompanyResponse] = None
    created_at: Optional[str] = None
    updated_at: Optional[str] = None

class UserData(UserBase):
    id: str = Field(..., alias="_id")

    model_config = ConfigDict(populate_by_name=True)

class UserResponse(BaseResponse):
    data: UserData

class UsersResponse(PaginationResponse):
    data: list[UserData] = Field(default_factory=list)

class ProfileResponse(BaseResponse):
    data: UserData

class AuthData(BaseModel):
    access_token: str
    refresh_token: str
    user: UserData

class RegistrationResponse(BaseResponse):
    data: AuthData

class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserData

class LoginResponse(BaseResponse):
    data: AuthData

class RefreshData(BaseModel):
    access_token: str
    refresh_token: str

class RefreshResponse(BaseResponse):
    data: RefreshData

class LoginRequest(BaseModel):
    email: EmailStr
    password: str
