# app/common/schemas/list_request.py

from typing import ClassVar, Optional, Sequence
from pydantic import BaseModel, Field, field_validator


class ListRequest(BaseModel):

    page: int = Field(
        default=1,
        ge=1,
        description="Page number starting from 1",
    )

    size: int = Field(
        default=10,
        ge=1,
        le=100,
        description="Number of items per page",
    )

    sort_by: str = Field(
        default="created_at",
        description="Field to sort by",
    )

    sort_order: str = Field(
        default="desc",
        description="Sort order",
    )

    allowed_sort_fields: ClassVar[Sequence[str]] = (
        "created_at",
    )

    @field_validator("sort_by")
    @classmethod
    def validate_sort_by(cls, value: str):

        if value not in cls.allowed_sort_fields:

            raise ValueError(
                f"sort_by must be one of: {', '.join(cls.allowed_sort_fields)}"
            )

        return value

    @field_validator("sort_order")
    @classmethod
    def validate_sort_order(cls, value: str):

        value = value.lower()

        if value not in ("asc", "desc"):

            raise ValueError(
                "sort_order must be either 'asc' or 'desc'"
            )

        return value