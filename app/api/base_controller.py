from fastapi import Depends

class BaseController:

    def __init__(self, service, storage_service=None):
        self.service = service
        self.storage_service = storage_service

    def build_response(self, message, data=None, meta=None):
        return {
            "status": "success",
            "message": message,
            "meta": meta,
            "data": data,
        }

    def build_search(self, **kwargs):
        from app.utils.api_utils import build_search
        return build_search(**kwargs)