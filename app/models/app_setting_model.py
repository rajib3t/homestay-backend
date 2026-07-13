from typing import Optional

from pydantic import BaseModel


class AppSetting(BaseModel):
    app_name: str
    app_logo: Optional[str] = None
    white_logo: Optional[str] = None
    app_favicon: Optional[str] = None
    app_timezone: str
    app_date_format: str
    app_time_format: str
