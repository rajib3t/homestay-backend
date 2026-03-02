from fastapi import APIRouter, Depends, HTTPException, status, Response, Request
from app.deps import get_location_service
from app.models.location_model import CountryCreate
from app.schemas.response import BaseResponse
from app.schemas.location_schema import CountryResponse, Location, City, Country
from app.services.location_service import LocationService

router = APIRouter(prefix="/api/v1/locations", tags=["Locations"])

@router.post(
    "/country", 
    response_model=CountryResponse, 
    status_code=status.HTTP_201_CREATED,
    response_model_by_alias=False,
)
async def create_location(
    country_data: CountryCreate,
    location_service: LocationService = Depends(get_location_service),
):
    try:
        # Basic validation
        if not country_data.name.isalpha():
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
        "message": "Location created successfully",
        "data": country
    }