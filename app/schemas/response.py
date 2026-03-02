from pydantic import BaseModel

class BaseResponse(BaseModel):
    status: str
    message: str


class PaginationResponse(BaseResponse):
    total: int
    page: int
    size: int
