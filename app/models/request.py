from pydantic import BaseModel, Field, field_validator
from typing import Optional, ClassVar, List


class ListRequest(BaseModel):
    page: int = Field(1, ge=1, description="Page number, starting from 1")
    size: int = Field(10, ge=1, le=100, description="Number of items per page")
    sort_by: Optional[str] = Field('name', description="Field to sort by")
    sort_order: Optional[str] = Field('asc', description="Sort order: asc or desc")

    # Child classes can override this to provide their own allowed sort fields
    _allowed_sort_fields: ClassVar[List[str]] = ['name', 'code', 'dial_code']

    @field_validator('sort_by')
    @classmethod
    def _validate_sort_by(cls, v):
        if v is None:
            return v
        if v not in cls._allowed_sort_fields:
            raise ValueError(f"sort_by must be one of: {cls._allowed_sort_fields}")
        return v

    @field_validator('sort_order')
    @classmethod
    def _validate_sort_order(cls, v):
        if v not in ('asc', 'desc'):
            raise ValueError("sort_order must be 'asc' or 'desc'")
        return v
    