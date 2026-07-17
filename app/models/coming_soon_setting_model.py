from pydantic import BaseModel, Field, field_validator, ConfigDict
from typing import Optional


class ComingSoonSettingBase(BaseModel):
    model_config = ConfigDict(
        str_strip_whitespace=True,
        validate_assignment=True,
        extra="forbid"
    )

    video_url: Optional[str] = Field(None, description="URL of the video to be displayed on the coming soon page")
    background_image_url: Optional[str] = Field(None, description="URL of the background image for the coming soon page")
    lunch_date: Optional[str] = Field(None, description="Launch date for the coming soon page in YYYY-MM-DD format")