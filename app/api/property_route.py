from unittest import result

from fastapi import APIRouter, Depends
from uvicorn import logging

from app.api.base_controller import BaseController
from app.application.dto.property import ( 
    PropertyDTO, 
    PropertyQuery
)
from app.application.use_cases.property.create_property_use_case import CreatePropertyUseCase
from app.application.use_cases.property.get_properties_use_case import GetPropertiesUseCase
from app.application.use_cases.property.get_property_use_case import GetPropertyUseCase
from app.deps.property import get_property_create_use_case, get_property_list_use_case, get_property_use_case
from app.middleware.idempotency_route import IdempotencyRoute
from app.schemas.property_schema import CreatePropertyResponseSchema, PropertyListResponseSchema, PropertySchema
from app.utils.exception_decorate import handle_api_exceptions

import logging
logger = logging.getLogger(__name__)

def _pagination_meta(r):
    return {"total": r["total"], "page": r["page"], "size": r.get("page_size", r.get("size", 10))}
class PropertyController(BaseController):
    def __init__(self):
        super().__init__(service=None, storage_service=None)

        self.router = APIRouter(
            prefix="/properties",
            tags=["Properties"],
            route_class=IdempotencyRoute,
        )

        self.register_routes()

    def register_routes(self):
        routes = [
            (
                "post",
                "",
                self._create_property,
                {
                    "response_model": CreatePropertyResponseSchema,
                    "response_model_by_alias": False,
                    "status_code": 201,
                },
            ),
            (
                "get",
                "",
                self._get_properties,
                {
                    "response_model": PropertyListResponseSchema,
                    "response_model_by_alias": False,
                    "status_code": 200,
                },
            ),
            (
                "get",
                "/{property_id}",
                self._get_property,
                {
                    "response_model": dict,
                    "response_model_by_alias": False,
                    "status_code": 200,
                },
            ),
        ]

        for method, path, handler, route_kwargs in routes:
            getattr(self.router, method)(path, **route_kwargs)(handler)

    @handle_api_exceptions
    async def _create_property(
        self,
        data: PropertyDTO,
        use_case: CreatePropertyUseCase = Depends(get_property_create_use_case),
    ):
        property_id = await use_case.execute(data)

        return self.build_response(
            "Property created successfully",
            data={"id": property_id},
        )

    @handle_api_exceptions
    async def _get_property(
        self,
        property_id: str,
        use_case: GetPropertyUseCase = Depends(get_property_use_case),
    ):
        property_data = await use_case.execute(property_id)

        return self.build_response(
            "Property retrieved successfully",
            data=property_data,
        )
    
    async def _get_properties(
        self,
        params: PropertyQuery = Depends(),
        use_case: GetPropertiesUseCase = Depends(get_property_list_use_case),
    ):
        properties_data = await use_case.execute(params)

        return self.build_response(
            "Properties retrieved successfully",
            data=properties_data["items"],
            meta=_pagination_meta(properties_data),
        )

controller = PropertyController()

router = controller.router
