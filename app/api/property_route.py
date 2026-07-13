from fastapi import APIRouter, Depends
from uvicorn import logging

from app.api.base_controller import BaseController
from app.application.dto.property import PropertyDTO
from app.application.use_cases.property.create_property_use_case import CreatePropertyUseCase
from app.deps.property import get_property_create_use_case
from app.middleware.idempotency_route import IdempotencyRoute
from app.utils.exception_decorate import handle_api_exceptions

import logging
logger = logging.getLogger(__name__)


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
                self.create_property,
                {
                    "response_model": dict,
                    "response_model_by_alias": False,
                    "status_code": 201,
                },
            ),
        ]

        for method, path, handler, route_kwargs in routes:
            getattr(self.router, method)(path, **route_kwargs)(handler)

    @handle_api_exceptions
    async def create_property(
        self,
        data: PropertyDTO,
        use_case: CreatePropertyUseCase = Depends(get_property_create_use_case),
    ):
        property_id = await use_case.execute(data)

        return self.build_response(
            "Property created successfully",
            data={"id": property_id},
        )


controller = PropertyController()

router = controller.router
