from pydantic.v1 import BaseModel
from starlette.datastructures import UploadFile


class ComingSoonSettingDTO(BaseModel):
    
    video_url: UploadFile | None = None
    background_image_url:UploadFile | None = None
    launch_date: str | None = None