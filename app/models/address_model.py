from pydantic import BaseModel, Field, field_validator, ConfigDict
from typing import Optional
from enum import Enum


# ---------------------------
# ENUMS
# ---------------------------
class AddressType(str, Enum):
    HOME = "home"
    WORK = "work"
    BILLING = "billing"
    SHIPPING = "shipping"
    OTHER = "other"


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
# ADDRESS BASE
# ---------------------------
class AddressBase(BaseSchema):
    street: str = Field(..., min_length=1, max_length=255, description="Street address")
    city: str = Field(..., min_length=1, max_length=100, description="City name")
    state: str = Field(..., min_length=1, max_length=100, description="State/Province")
    zip_code: str = Field(..., min_length=3, max_length=20, description="ZIP/Postal code")
    country: str = Field(..., min_length=1, max_length=100, description="Country name")
    address_type: AddressType = Field(default=AddressType.OTHER, description="Type of address")
    is_primary: bool = Field(default=False, description="Whether this is the primary address")


# ---------------------------
# ADDRESS CREATE
# ---------------------------
class AddressCreate(AddressBase):
    user_id: Optional[str] = Field(None, description="User ID (if address belongs to user)")
    company_id: Optional[str] = Field(None, description="Company ID (if address belongs to company)")

    @field_validator("user_id", "company_id", mode="after")
    @classmethod
    def validate_owner(cls, v, info):
        values = info.data
        has_user = values.get("user_id") is not None
        has_company = values.get("company_id") is not None

        # Check if at least one owner is specified when validating the second field
        if info.field_name == "company_id" and not has_user and v is None:
            raise ValueError("Either user_id or company_id must be provided")
        return v


# ---------------------------
# ADDRESS UPDATE
# ---------------------------
class AddressUpdate(BaseSchema):
    street: Optional[str] = Field(None, min_length=1, max_length=255)
    city: Optional[str] = Field(None, min_length=1, max_length=100)
    state: Optional[str] = Field(None, min_length=1, max_length=100)
    zip_code: Optional[str] = Field(None, min_length=3, max_length=20)
    country: Optional[str] = Field(None, min_length=1, max_length=100)
    address_type: Optional[AddressType] = None
    is_primary: Optional[bool] = None


# ---------------------------
# ADDRESS RESPONSE
# ---------------------------
class AddressResponse(AddressBase):
    id: str = Field(..., description="Address ID")
    user_id: Optional[str] = Field(None, description="User ID")
    company_id: Optional[str] = Field(None, description="Company ID")


# ---------------------------
# ADDRESS IN USER/COMPANY
# ---------------------------
class AddressInUser(AddressBase):
    """Address embedded in User response"""
    id: str = Field(..., description="Address ID")


class AddressInCompany(AddressBase):
    """Address embedded in Company response"""
    id: str = Field(..., description="Address ID")
