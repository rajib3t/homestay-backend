from pydantic import BaseModel, EmailStr, Field
from pydantic import ConfigDict
from app.schemas.response import BaseResponse

class UserBase(BaseModel):
    username: str
    email: EmailStr
    user_type: str
    first_name: str
    last_name: str
    mobile: str

class UserResponse(UserBase):
    id: str = Field(..., alias="_id")

    model_config = ConfigDict(populate_by_name=True)

class ProfileResponse(BaseResponse):
    data: UserResponse

class AuthData(BaseModel):
    access_token: str
    refresh_token: str
    user: UserResponse

class RegistrationResponse(BaseResponse):
    data: AuthData

class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserResponse

class LoginResponse(BaseResponse):
    data: AuthData

class RefreshData(BaseModel):
    access_token: str

class RefreshResponse(BaseResponse):
    data: RefreshData

class LoginRequest(BaseModel):
    email: EmailStr
    password: str
