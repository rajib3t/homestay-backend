from fastapi import APIRouter, Depends, HTTPException, status, Response, Request
from app.deps import get_location_service
from app.models.location_model import CountryCreate
from app.schemas.response import BaseResponse
from app.schemas.location_schema import CountryResponse, Location, City, Country, CountriesResponse
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

        if not re.match(r'^[A-Za-z ]+$', name):
            raise HTTPException(status_code=400, detail="Invalid country name")

        if not str(country_data.dial_code).isdigit():
            raise HTTPException(status_code=400, detail="Invalid dial_code")

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

@router.get(
    "/countries",
    response_model=CountriesResponse,
    status_code=status.HTTP_200_OK,
    response_model_by_alias=False,
)
async def list_countries(
    page: int = 1,
    size: int = 10,
    location_service: LocationService = Depends(get_location_service),
):
    try:
        result = await location_service.list_countries(page=page, size=size)
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