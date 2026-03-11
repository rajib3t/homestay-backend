import logging

from fastapi import APIRouter, Depends, HTTPException, status, Response, Request
from app.deps import get_location_service
from app.models.location_model import CityCreate, CountryCreate, CountryUpdate
from app.schemas.response import BaseResponse
from app.schemas.location_schema import CityResponse, CountryResponse, Location, City, Country, CountriesResponse
from app.services import location_service
from app.services.location_service import LocationService
import re

router = APIRouter(prefix="/api/v1/locations", tags=["Locations"])

@router.post(
    "/country", 
    response_model=CountryResponse, 
    status_code=status.HTTP_201_CREATED,
    response_model_by_alias=False,
)
async def create_country(
    country_data: CountryCreate,
    location_service: LocationService = Depends(get_location_service),
):
    try:
        # Basic validation
        name = country_data.name.strip()

        
        # Create country and return created document
        country_id = await location_service.create_country(country_data.model_dump())
        country = await location_service.get_country(country_id)

    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

    return {
        "status": "success",
        "message": "Country created successfully",
        "data": country
    }



@router.get(
    "/country/{country_id}",
    response_model=CountryResponse,
    status_code=status.HTTP_200_OK,
    response_model_by_alias=False,
)
async def get_country(
    country_id: str,
    location_service: LocationService = Depends(get_location_service),
):
    try:
        country = await location_service.get_country(country_id)
        if not country:
            raise HTTPException(status_code=404, detail="Country not found")
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

    return {
        "status": "success",
        "message": "Country retrieved successfully",
        "data": country
    }

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
        # Basic validation
        name = country_data.name.strip()

        # Update country and return updated document
        updated = await location_service.update_country(country_id, country_data.model_dump())
        if not updated:
            raise HTTPException(status_code=404, detail="Country not found")
        country = await location_service.get_country(country_id)

    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

    return {
        "status": "success",
        "message": "Country updated successfully",
        "data": country
    }

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

    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

    return {
        "status": "success",
        "message": "Country status toggled successfully",
        "data": country
    }

@router.get(
    "/countries",
    response_model=CountriesResponse,
    status_code=status.HTTP_200_OK,
    response_model_by_alias=False,
)
async def list_countries(
    page: int = 1,
    size: int = 10,
    sort_by: str = "name",
    sort_order: str = "asc",
    search_field: str = None,
    search_value: str = None,
    location_service: LocationService = Depends(get_location_service),
):
    try:
        search = None
        if search_field and search_value:
            search = {search_field: search_value}
        result = await location_service.list_countries(page=page, size=size, sort_by=sort_by, sort_order=sort_order, search=search)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

    return {
        "status": "success",
        "message": "Countries retrieved successfully",
        "meta": {
            "total": result["total"],
            "page": result["page"],
            "size": result["size"],
        },
        "data": result["items"],
    }
# City Endpoints
@router.post(
    "/city",
    response_model=CityResponse,
    status_code=status.HTTP_201_CREATED,
)  

async def create_city(
    city_data: CityCreate,
    location_service: LocationService = Depends(get_location_service),
):
    try:
        # Basic validation
        name = city_data.name.strip()
        country_name = city_data.country.strip()
        logging.info(f"Creating city with name: {name} in country: {country_name}")
        # Create city and return created document
        city_id = await location_service.create_city(city_data.model_dump())
        city = await location_service.get_city(city_id)

    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

    return {
        "status": "success",
        "message": "City created successfully",
        "data": city
    }
