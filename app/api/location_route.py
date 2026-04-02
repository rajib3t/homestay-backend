import logging
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Request, UploadFile, File, Form, status

from app.deps import get_location_service, get_storage_service
from app.middleware.idempotency_route import IdempotencyRoute
from app.services.location_service import LocationService
from app.services.storage_service import StorageService

from app.models.location_model import (
    CityCreate, CityList,
    CountryCreate, CountryUpdate, CountryList,
    LocationCreate, LocationList, LocationUpdate
)

from app.schemas.location_schema import (
    CityResponse, CitiesResponse, CitiesOnlyResponse,
    CountryResponse, CountriesResponse,
    LocationResponse, LocationsResponse
)

from app.utils.api_utils import (
    parse_request_payload,
    parse_optional_request_payload,
    parse_image_input,
)
from app.utils.exception_decorate import handle_api_exceptions

from .base_controller import BaseController

logger = logging.getLogger(__name__)

_PAGINATION_META = lambda r: {"total": r["total"], "page": r["page"], "size": r["size"]}


class LocationController(BaseController):

    def __init__(self):
        super().__init__(service=None, storage_service=None)

        self.router = APIRouter(
            prefix="/locations",
            tags=["Locations"],
            route_class=IdempotencyRoute,
        )

        self.register_routes()

    # ---------------- ROUTE REGISTRATION ---------------- #

    def register_routes(self):
        routes = [
            # Country
            ("post",  "/country",                       self.create_country,         {"response_model": CountryResponse,    "response_model_by_alias": False, "status_code": 201}),
            ("get",   "/country/{country_id}",          self.get_country,            {"response_model": CountryResponse,    "response_model_by_alias": False}),
            ("patch", "/country/{country_id}",          self.update_country,         {"response_model": CountryResponse,    "response_model_by_alias": False}),
            ("patch", "/country/{country_id}/status",   self.toggle_country_status,  {"response_model": CountryResponse,    "response_model_by_alias": False}),
            ("get",   "/countries",                     self.list_countries,         {"response_model": CountriesResponse,  "response_model_by_alias": False}),

            # City
            ("post",  "/city",                          self.create_city,            {"response_model": CityResponse,       "response_model_by_alias": False, "status_code": 201}),
            ("get",   "/cities",                        self.list_cities,            {"response_model": CitiesResponse,     "response_model_by_alias": False}),
            ("get",   "/city/{city_id}",                self.get_city,               {"response_model": CityResponse,       "response_model_by_alias": False}),
            ("patch", "/city/{city_id}",                self.update_city,            {"response_model": CityResponse,       "response_model_by_alias": False}),
            ("get",   "/country/{country_id}/cities",   self.list_country_cities,    {"response_model": CitiesOnlyResponse, "response_model_by_alias": False}),

            # Location
            ("post",  "/create",                        self.create_location,        {"response_model": LocationResponse,   "response_model_by_alias": False, "status_code": 201}),
            ("get",   "/locations",                     self.list_locations,         {"response_model": LocationsResponse,  "response_model_by_alias": False}),
            ("get",   "/location/{location_id}",        self.get_location,           {"response_model": LocationResponse,   "response_model_by_alias": False}),
            ("patch", "/location/{location_id}",        self.update_location,        {"response_model": LocationResponse,   "response_model_by_alias": False}),
        ]

        for method, path, handler, route_kwargs in routes:
            getattr(self.router, method)(path, **route_kwargs)(handler)

    # ---------------- COUNTRY ---------------- #

    @handle_api_exceptions
    async def create_country(
        self,
        data: CountryCreate,
        service: LocationService = Depends(get_location_service),
    ):
        country_id = await service.create_country(data.model_dump())
        country = await service.get_country(country_id)
        return self.build_response("Country created successfully", country)

    @handle_api_exceptions
    async def get_country(
        self,
        country_id: str,
        service: LocationService = Depends(get_location_service),
    ):
        country = await service.get_country(country_id)
        if not country:
            raise HTTPException(status_code=404, detail="Country not found")
        return self.build_response("Country retrieved successfully", country)

    @handle_api_exceptions
    async def update_country(
        self,
        country_id: str,
        data: CountryUpdate,
        service: LocationService = Depends(get_location_service),
    ):
        updated = await service.update_country(country_id, data.model_dump())
        if not updated:
            raise HTTPException(status_code=404, detail="Country not found")
        country = await service.get_country(country_id)
        return self.build_response("Country updated successfully", country)

    @handle_api_exceptions
    async def toggle_country_status(
        self,
        country_id: str,
        service: LocationService = Depends(get_location_service),
    ):
        updated = await service.toggle_country_status(country_id)
        if not updated:
            raise HTTPException(status_code=404, detail="Country not found")
        country = await service.get_country(country_id)
        return self.build_response("Country status toggled successfully", country)

    @handle_api_exceptions
    async def list_countries(
        self,
        params: CountryList = Depends(),
        service: LocationService = Depends(get_location_service),
    ):
        search = self.build_search(name=params.name, code=params.code, status=params.status)
        result = await service.list_countries(
            page=params.page,
            size=params.size,
            sort_by=params.sort_by,
            sort_order=params.sort_order,
            search=search,
        )
        return self.build_response("Countries retrieved successfully", data=result["items"], meta=_PAGINATION_META(result))

    # ---------------- CITY ---------------- #

    @handle_api_exceptions
    async def create_city(
        self,
        request: Request,
        city_data: Optional[str] = Form(None),
        image_file: Optional[UploadFile] = File(None),
        service: LocationService = Depends(get_location_service),
        storage_service: StorageService = Depends(get_storage_service),
    ):
        payload = await parse_request_payload(request, city_data)
        image_field = payload.pop("image", None)
        image_bytes, content_type = await parse_image_input(image_file, image_field)

        city_model = CityCreate.model_validate(payload)
        city_id = await service.create_city(
            city_model.model_dump(),
            image_bytes=image_bytes,
            content_type=content_type,
            storage=storage_service,
        )
        city = await service.get_city(city_id, storage=storage_service)
        return self.build_response("City created successfully", city)

    @handle_api_exceptions
    async def list_cities(
        self,
        params: CityList = Depends(),
        service: LocationService = Depends(get_location_service),
        storage_service: StorageService = Depends(get_storage_service),
    ):
        search = self.build_search(name=params.name, country=params.country, is_popular=params.is_popular)
        result = await service.list_cities(
            page=params.page,
            size=params.size,
            sort_by=params.sort_by,
            sort_order=params.sort_order,
            search=search,
            storage=storage_service,
        )
        return self.build_response("Cities retrieved successfully", data=result["items"], meta=_PAGINATION_META(result))

    @handle_api_exceptions
    async def get_city(
        self,
        city_id: str,
        service: LocationService = Depends(get_location_service),
        storage_service: StorageService = Depends(get_storage_service),
    ):
        city = await service.get_city(city_id, storage=storage_service)
        if not city:
            raise HTTPException(status_code=404, detail="City not found")
        return self.build_response("City retrieved successfully", city)

    @handle_api_exceptions
    async def update_city(
        self,
        city_id: str,
        request: Request,
        city_data: Optional[str] = Form(None),
        image_file: Optional[UploadFile] = File(None),
        service: LocationService = Depends(get_location_service),
        storage_service: StorageService = Depends(get_storage_service),
    ):
        payload = await parse_optional_request_payload(
            request,
            city_data,
            form_field_name="city_data",
            body_key="city_data",
        )
        image_field = payload.pop("image", None)
        image_bytes, content_type = await parse_image_input(image_file, image_field)

        updated = await service.update_city(
            city_id=city_id,
            update_data=payload,
            image_bytes=image_bytes,
            content_type=content_type,
            storage=storage_service,
        )
        if not updated:
            raise HTTPException(status_code=404, detail="City not found")

        city = await service.get_city(city_id, storage=storage_service)
        return self.build_response("City updated successfully", city)

    @handle_api_exceptions
    async def list_country_cities(
        self,
        country_id: str,
        service: LocationService = Depends(get_location_service),
        storage_service: StorageService = Depends(get_storage_service),
    ):
        cities = await service.list_cities_by_country(country_id)
        for city in cities:
            if storage_service and isinstance(city, dict):
                key = city.get("image")
                if key:
                    try:
                        city["image_url"] = storage_service.generate_presigned_url(key)
                    except Exception:
                        pass
        return self.build_response("Cities retrieved successfully", cities)

    # ---------------- LOCATION ---------------- #

    @handle_api_exceptions
    async def create_location(
        self,
        data: LocationCreate,
        service: LocationService = Depends(get_location_service),
    ):
        location_id = await service.create_location(data.model_dump())
        location = await service.get_location(location_id)
        return self.build_response("Location created successfully", location)

    @handle_api_exceptions
    async def list_locations(
        self,
        params: LocationList = Depends(),
        service: LocationService = Depends(get_location_service),
    ):
        search = self.build_search(name=params.name, city=params.city, country=params.country)
        result = await service.list_locations(
            page=params.page,
            size=params.size,
            sort_by=params.sort_by,
            sort_order=params.sort_order,
            search=search,
        )
        return self.build_response("Locations retrieved successfully", data=result["items"], meta=_PAGINATION_META(result))

    @handle_api_exceptions
    async def get_location(
        self,
        location_id: str,
        service: LocationService = Depends(get_location_service),
    ):
        location = await service.get_location(location_id)
        if not location:
            raise HTTPException(status_code=404, detail="Location not found")
        return self.build_response("Location retrieved successfully", location)

    @handle_api_exceptions
    async def update_location(
        self,
        location_id: str,
        data: LocationUpdate,
        service: LocationService = Depends(get_location_service),
    ):
        updated = await service.update_location(location_id, data.model_dump(exclude_none=True))
        if not updated:
            raise HTTPException(status_code=404, detail="Location not found")
        location = await service.get_location(location_id)
        return self.build_response("Location updated successfully", location)


controller = LocationController()
router = controller.router