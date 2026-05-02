from pydantic import BaseModel, EmailStr, Field, field_validator, ConfigDict
from typing import Optional, List
from enum import Enum
import re
from typing import ClassVar
from app.models.request import ListRequest
from app.models.company_model import CompanyUpdate


# ---------------------------
# ENUMS
# ---------------------------
class UserType(str, Enum):
    ADMIN = "admin"
    USER = "user"
    VENDOR = "vendor"


# ---------------------------
# BASE MODEL CONFIG
# ---------------------------
class BaseSchema(BaseModel):
    model_config = ConfigDict(
        str_strip_whitespace=True,
        validate_assignment=True,
        extra="forbid"
    )


# ---------------------------
# COMMON VALIDATORS
# ---------------------------
def validate_mobile(value: str) -> str:
    if not re.fullmatch(r"^[6-9]\d{9}$", value):
        raise ValueError("Invalid mobile number (must be Indian 10-digit number)")
    return value


def validate_password(value: str) -> str:
    if len(value) < 8:
        raise ValueError("Password must be at least 8 characters")
    if not re.search(r"[A-Z]", value):
        raise ValueError("Password must contain at least one uppercase letter")
    if not re.search(r"[a-z]", value):
        raise ValueError("Password must contain at least one lowercase letter")
    if not re.search(r"\d", value):
        raise ValueError("Password must contain at least one digit")
    return value


# ---------------------------
# USER CREATE
# ---------------------------
class UserCreate(BaseSchema):
    username: str = Field(..., min_length=3, max_length=50)
    email: EmailStr
    password: str
    user_type: UserType
    first_name: str = Field(..., min_length=1, max_length=50)
    last_name: str = Field(..., min_length=1, max_length=50)
    mobile: str
    image: Optional[str] = None

    @field_validator("mobile")
    @classmethod
    def validate_mobile_number(cls, v):
        return validate_mobile(v)

    @field_validator("password")
    @classmethod
    def validate_password_strength(cls, v):
        return validate_password(v)


# ---------------------------
# USER UPDATE
# ---------------------------
class UserUpdate(BaseSchema):
    email: Optional[EmailStr] = None
    first_name: Optional[str] = Field(None, min_length=1, max_length=50)
    last_name: Optional[str] = Field(None, min_length=1, max_length=50)
    mobile: Optional[str] = None
    image: Optional[str] = None
    company: Optional[CompanyUpdate] = None

    @field_validator("mobile")
    @classmethod
    def validate_mobile_number(cls, v):
        if v is None:
            return v
        return validate_mobile(v)


# ---------------------------
# USER IMAGE
# ---------------------------
class UserProfileImageUpdate(BaseSchema):
    image: str = Field(..., description="Profile image URL or base64 string")

class UserPasswordUpdate(BaseSchema):
    new_password: str

    @field_validator("new_password")
    @classmethod
    def validate_password_strength(cls, v):
        return validate_password(v)
    
# ---------------------------
# LIST USERS
# ---------------------------


class ListUsers(ListRequest):
    sort_by: Optional[str] = Field(default="first_name")

    username: Optional[str] = None
    email: Optional[EmailStr] = None
    user_type: Optional[str] = None
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    mobile: Optional[str] = None

    _allowed_sort_fields: ClassVar[List[str]] = [
        "username",
        "email",
        "user_type",
        "first_name",
        "last_name",
        "mobile",
    ]

    @field_validator("sort_by", mode="before")
    @classmethod
    def normalize_sort_by(cls, value):
        if value == "name":
            value = "first_name"

        if value not in cls._allowed_sort_fields:
            raise ValueError(
                f"Invalid sort field. Allowed: {cls._allowed_sort_fields}"
            )

        return value