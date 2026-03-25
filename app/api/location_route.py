import logging
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, status, Request, UploadFile, File, Form

from app.deps import get_location_service, get_storage_service
from app.services.location_service import LocationService

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
    handle_exception,
    parse_request_payload,
    parse_optional_request_payload,
    parse_image_input,
    build_search
)

router = APIRouter(prefix="/locations", tags=["Locations"])

logger = logging.getLogger(__name__)


def _attach_image_url(item: dict, storage) -> None:
    """Attach a presigned `image_url` to `item` if it has an `image` key and storage is available."""
    if not storage or not item or not isinstance(item, dict):
        return
    key = item.get("image")
    if key:
        try:
            url = storage.generate_presigned_url(key)
            item["image_url"] = url
        except Exception:
            # silently ignore presign failures
            pass

@router.post("/country", response_model=CountryResponse, status_code=201)
async def create_country(
    country_data: CountryCreate,
    service: LocationService = Depends(get_location_service),
):
    try:
        country_id = await service.create_country(country_data.model_dump())
        country = await service.get_country(country_id)

        return {
            "status": "success",
            "message": "Country created successfully",
            "data": country
        }

    except Exception as e:
        handle_exception(e)



@router.get(
    "/country/{country_id}",
    response_model=CountryResponse,
    status_code=status.HTTP_200_OK,
    response_model_by_alias=False,
)
async def get_country(
    country_id: str,
    service: LocationService = Depends(get_location_service),
):
    try:
        country = await service.get_country(country_id)

        if not country:
            raise HTTPException(404, "Country not found")

        return {
            "status": "success",
            "message": "Country retrieved successfully",
            "data": country
        }

    except Exception as e:
        handle_exception(e)

@router.patch(
    "/country/{country_id}",
    response_model=CountryResponse,
    status_code=status.HTTP_200_OK,
    response_model_by_alias=False,
)
async def update_country(
    country_id: str,
    country_data: CountryUpdate,
    location_service: LocationService = Depends(get_location_service),
):
    try:
        # Update country and return updated document
        updated = await location_service.update_country(country_id, country_data.model_dump())
        if not updated:
            raise HTTPException(status_code=404, detail="Country not found")
        country = await location_service.get_country(country_id)

        return {
            "status": "success",
            "message": "Country updated successfully",
            "data": country
        }
    except Exception as e:
        handle_exception(e)

@router.patch(
    "/country/{country_id}/status",
    response_model=CountryResponse,
    status_code=status.HTTP_200_OK,
    response_model_by_alias=False,
)
async def toggle_country_status(
    country_id: str,
    location_service: LocationService = Depends(get_location_service),
):
    try:
        # Toggle status and return updated document
        updated = await location_service.toggle_country_status(country_id)
        if not updated:
            raise HTTPException(status_code=404, detail="Country not found")
        country = await location_service.get_country(country_id)

        return {
            "status": "success",
            "message": "Country status toggled successfully",
            "data": country
        }

    except Exception as e:
        handle_exception(e)

@router.get("/countries", response_model=CountriesResponse,response_model_by_alias=False,)
async def list_countries(
    params: CountryList = Depends(),
    service: LocationService = Depends(get_location_service),
):
    try:
        search = build_search(
            name=params.name,
            code=params.code,
            status=params.status
        )

        result = await service.list_countries(
            page=params.page,
            size=params.size,
            sort_by=params.sort_by,
            sort_order=params.sort_order,
            search=search
        )

        return {
            "status": "success",
            "message": "Countries retrieved successfully",
            "meta": {
                "total": result["total"],
                "page": result["page"],
                "size": result["size"],
            },
            "data": result["items"]
        }

    except Exception as e:
        handle_exception(e)


# List all cities for a country
@router.get(
    "/country/{country_id}/cities",
    response_model=CitiesOnlyResponse,
    status_code=status.HTTP_200_OK,
    response_model_by_alias=False,
)
async def list_country_cities(
    country_id: str,
    location_service: LocationService = Depends(get_location_service),
    storage: object = Depends(get_storage_service),
):
    try:
        cities = await location_service.list_cities_by_country(country_id)
    except Exception as e:
        handle_exception(e)

    # attach presigned urls for each city
    try:
        for c in cities:
            _attach_image_url(c, storage)
    except Exception as e:
        handle_exception(e)

    return {
        "status": "success",
        "message": "Cities retrieved successfully",
        "data": cities,
    }
# City Endpoints
@router.post("/city", response_model=CityResponse, status_code=201,  response_model_by_alias=False,)
async def create_city(
    request: Request,
    city_data: Optional[str] = Form(None),
    image_file: Optional[UploadFile] = File(None),
    service: LocationService = Depends(get_location_service),
    storage=Depends(get_storage_service),
):
    try:
        payload = await parse_request_payload(request, city_data)

        image_field = payload.pop("image", None)
        image_bytes, content_type = await parse_image_input(image_file, image_field)

        city_model = CityCreate.model_validate(payload)

        city = await service.create_city(
            city_model.model_dump(),
            image_bytes=image_bytes,
            content_type=content_type,
            storage=storage
        )

        city = await service.get_city(city, storage=storage)

        return {
            "status": "success",
            "message": "City created successfully",
            "data": city
        }

    except Exception as e:
        handle_exception(e)

@router.get("/cities", response_model=CitiesResponse,response_model_by_alias=False,)
async def list_cities(
    params: CityList = Depends(),
    service: LocationService = Depends(get_location_service),
    storage=Depends(get_storage_service),
):
    try:
        search = build_search(
            name=params.name,
            country=params.country,
            is_popular=params.is_popular
        )

        result = await service.list_cities(
            page=params.page,
            size=params.size,
            sort_by=params.sort_by,
            sort_order=params.sort_order,
            search=search,
            storage=storage
        )

        return {
            "status": "success",
            "message": "Cities retrieved successfully",
            "meta": {
                "total": result["total"],
                "page": result["page"],
                "size": result["size"],
            },
            "data": result["items"]
        }

    except Exception as e:
        handle_exception(e)


@router.get(
    "/city/{city_id}",
    response_model=CityResponse,
    status_code=status.HTTP_200_OK,
    response_model_by_alias=False,
)
async def get_city(
    city_id: str,
    location_service: LocationService = Depends(get_location_service),
    storage: object = Depends(get_storage_service),
):
    try:
        city = await location_service.get_city(city_id, storage=storage)
        if not city:
            raise HTTPException(status_code=404, detail="City not found")

        return {
            "status": "success",
            "message": "City retrieved successfully",
            "data": city
        }
    except Exception as e:
        handle_exception(e)

@router.patch(
    "/city/{city_id}",
    response_model=CityResponse,
    status_code=status.HTTP_200_OK,
    response_model_by_alias=False,
)
async def update_city(
    city_id: str,
    request: Request,
    city_data: Optional[str] = Form(None),
    image_file: Optional[UploadFile] = File(None),
    location_service: LocationService = Depends(get_location_service),
    storage: object = Depends(get_storage_service),
    
):
    try:
        payload = await parse_optional_request_payload(
            request,
            city_data,
            form_field_name="city_data",
            body_key="city_data",
        )

        image_field = payload.pop("image", None)
        image_bytes, content_type = await parse_image_input(image_file, image_field)

        updated = await location_service.update_city(
            city_id=city_id,
            update_data=payload,
            image_bytes=image_bytes,
            content_type=content_type,
            storage=storage,
        )

        if not updated:
            raise HTTPException(status_code=404, detail="City not found")

        city = await location_service.get_city(city_id, storage=storage)

        return {
            "status": "success",
            "message": "City updated successfully",
            "data": city,
        }

    except Exception as e:
        handle_exception(e)
    



@router.post("/create", response_model=LocationResponse, status_code=201)
async def create_location(
    location_data: LocationCreate,
    service: LocationService = Depends(get_location_service),
):
    try:
        location = await service.create_location(location_data.model_dump())
        db_location = await service.get_location(location)
        return {
            "status": "success",
            "message": "Location created successfully",
            "data": db_location
        }

    except Exception as e:
        handle_exception(e)

@router.get("/locations", response_model=LocationsResponse, response_model_by_alias=False, status_code=status.HTTP_200_OK)
async def list_locations(
    params: LocationList = Depends(),
    service: LocationService = Depends(get_location_service),
):
    try:
        search = build_search(
            name=params.name,
            city=params.city,
            country=params.country
        )

        result = await service.list_locations(
            page=params.page,
            size=params.size,
            sort_by=params.sort_by,
            sort_order=params.sort_order,
            search=search
        )

        return {
            "status": "success",
            "message": "Locations retrieved successfully",
            "meta": {
                "total": result["total"],
                "page": result["page"],
                "size": result["size"],
            },
            "data": result["items"]
        }

    except Exception as e:
        handle_exception(e)


@router.get(
    "/location/{location_id}",
    response_model=LocationResponse,
    status_code=status.HTTP_200_OK,
    response_model_by_alias=False,
)
async def get_location(
    location_id: str,
    location_service: LocationService = Depends(get_location_service),
):
    try:
        location = await location_service.get_location(location_id)
        if not location:
            raise HTTPException(status_code=404, detail="Location not found")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    
    return {
        "status": "success",
        "message": "Location retrieved successfully",
        "data": location
    }

@router.patch(
    "/location/{location_id}",
    response_model=LocationResponse,
    status_code=status.HTTP_200_OK,
    response_model_by_alias=False,
)
async def update_location(
    location_id: str,
    location_data: LocationUpdate,
    location_service: LocationService = Depends(get_location_service),
):
    try:
        # Update location and return updated document
        updated = await location_service.update_location(
            location_id,
            location_data.model_dump(exclude_none=True)
        )
        if not updated:
            raise HTTPException(status_code=404, detail="Location not found")
        location = await location_service.get_location(location_id)

        return {
            "status": "success",
            "message": "Location updated successfully",
            "data": location
        }

    except Exception as e:
        handle_exception(e)

