import code
import logging
from os import name
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, status, Response, Request, File, UploadFile, Form
from app.core.exceptions import AppException
from app.deps import get_location_service, get_storage_service
from app.models.location_model import CityCreate, CityList, CountryCreate, CountryUpdate, CountryList, LocationCreate, LocationList
from app.schemas.response import BaseResponse
from app.schemas.location_schema import CityResponse, CountryResponse, CountriesResponse, CitiesOnlyResponse, CitiesResponse, LocationResponse, LocationsResponse
from app.services import location_service
from app.services.location_service import LocationService
import re
import json
import base64
from bson import ObjectId

router = APIRouter(prefix="/api/v1/locations", tags=["Locations"])


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

    except AppException:
        raise
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

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
    storage: object = Depends(get_storage_service),
):
    try:
        country = await location_service.get_country(country_id)
        if not country:
            raise HTTPException(status_code=404, detail="Country not found")
    except AppException:
        raise
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

    # attach presigned urls for any city images in the country object
    try:
        if country and isinstance(country, dict):
            for c in country.get("cities", []):
                _attach_image_url(c, storage)
    except AppException:
        raise
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

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
    except AppException:
            raise
    except HTTPException:
            raise
    except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))

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

    except AppException:
        raise
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

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
    country_list: CountryList = Depends(),
    location_service: LocationService = Depends(get_location_service),
):
    try:
        search = {}
        if country_list.name:
            search["name"] = country_list.name
        if country_list.code:
            search["code"] = country_list.code
        if country_list.status is not None:
            search["status"] = country_list.status
        result = await location_service.list_countries(
            page=country_list.page,
            size=country_list.size,
            sort_by=country_list.sort_by,
            sort_order=country_list.sort_order,
            search=search
        )
    except AppException:
        raise
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


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
    except AppException:
        raise
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

    # attach presigned urls for each city
    try:
        for c in cities:
            _attach_image_url(c, storage)
    except AppException:
        raise
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

    return {
        "status": "success",
        "message": "Cities retrieved successfully",
        "data": cities,
    }
# City Endpoints
@router.post(
    "/city",
    response_model=CityResponse,
    status_code=status.HTTP_201_CREATED,
)  

async def create_city(
    city_data: Optional[str] = Form(None),
    image_file: Optional[UploadFile] = File(None),
    location_service: LocationService = Depends(get_location_service),
    storage: object = Depends(get_storage_service),
    request: Request = None,
):
    try:
        # Accept city data either as a JSON-form field (multipart/form-data)
        # or as a raw JSON body. Parse accordingly and validate with model.
        payload = None
        if city_data:
            try:
                payload = json.loads(city_data)
            except Exception:
                raise HTTPException(status_code=400, detail="Invalid JSON in city_data form field")
        else:
            try:
                body = await request.json()
            except Exception:
                body = None
            if body is None:
                raise HTTPException(status_code=400, detail="city_data is required")
            if isinstance(body, dict) and "city_data" in body:
                payload = body["city_data"]
            else:
                payload = body

        # If payload contains an image data URL, extract it before validation
        image_field = None
        if isinstance(payload, dict) and "image" in payload:
            image_field = payload.pop("image")

        # Validate into CityCreate model
        city_model = CityCreate.model_validate(payload)
        # Basic validation
        name = city_model.name.strip()
        country_name = city_model.country.strip()
        logging.info(f"Creating city with name: {name} in country: {country_name}")
        # Read image bytes if provided (either file upload or base64 in payload)
        image_bytes = None
        content_type = None
        # Prefer file upload if present
        if image_file:
            image_bytes = await image_file.read()
            content_type = image_file.content_type
        else:
            # check for base64 image string extracted from payload earlier
            img_field = image_field
            if isinstance(img_field, str) and img_field.startswith("data:"):
                m = re.match(r"data:(?P<mime>[\w/+-\.]+);base64,(?P<data>.+)", img_field)
                if not m:
                    raise HTTPException(status_code=400, detail="Invalid data URL for image")
                content_type = m.group("mime")
                try:
                    image_bytes = base64.b64decode(m.group("data"))
                except Exception:
                    raise HTTPException(status_code=400, detail="Invalid base64 image data")

        # Create city and return created document (uploads image if provided)
        city_id = await location_service.create_city(city_model.model_dump(), image_bytes=image_bytes, content_type=content_type, storage=storage)
        city = await location_service.get_city(city_id, storage=storage)

    except AppException:
        raise
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

    return {
        "status": "success",
        "message": "City created successfully",
        "data": city
    }

@router.get(
    "/cities",
    response_model=CitiesResponse,
    status_code=status.HTTP_200_OK,
    response_model_by_alias=False,
)
async def list_cities(
    city_list: CityList = Depends(),
    location_service: LocationService = Depends(get_location_service),
    storage: object = Depends(get_storage_service),
):
    try:
        search = {}
        if city_list.name:
            search["name"] = city_list.name
        if city_list.country:
            # country = await location_service.db.countries.find_one({"name": city_list.country}, {"_id": 1})
            # if country:
            search["country"] = city_list.country
        if city_list.is_popular is not None:
            search["is_popular"] = city_list.is_popular
        cities = await location_service.list_cities(page=city_list.page, size=city_list.size, sort_by=city_list.sort_by, sort_order=city_list.sort_order, search=search, storage=storage)
    except AppException:
        raise
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

    return {
        "status": "success",
        "message": "Cities retrieved successfully",
        "meta": {
            "total": cities["total"],
            "page": cities["page"],
            "size": cities["size"],
        },
        "data": cities["items"],
    }


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
    except AppException:
        raise
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

    return {
        "status": "success",
        "message": "City retrieved successfully",
        "data": city
    }   

@router.patch(
    "/city/{city_id}",
    response_model=CityResponse,
    status_code=status.HTTP_200_OK,
)
async def update_city(
    city_id: str,
    city_data: Optional[str] = Form(None),
    image_file: Optional[UploadFile] = File(None),
    location_service: LocationService = Depends(get_location_service),
    storage: object = Depends(get_storage_service),
    request: Request = None,
):
    try:
        payload = {}
        if city_data:
            try:
                payload = json.loads(city_data)
            except Exception:
                raise HTTPException(status_code=400, detail="Invalid JSON in city_data form field")
        else:
            try:
                body = await request.json()
                if isinstance(body, dict) and "city_data" in body:
                    payload = body["city_data"]
                else:
                    payload = body
            except Exception:
                pass

        # If payload contains an image data URL, extract it
        image_field = None
        if isinstance(payload, dict) and "image" in payload:
            image_field = payload.pop("image")

        # Read image bytes if provided
        image_bytes = None
        content_type = None
        if image_file:
            image_bytes = await image_file.read()
            content_type = image_file.content_type
        elif image_field and isinstance(image_field, str) and image_field.startswith("data:"):
            m = re.match(r"data:(?P<mime>[\w/+-\.]+);base64,(?P<data>.+)", image_field)
            if m:
                content_type = m.group("mime")
                try:
                    image_bytes = base64.b64decode(m.group("data"))
                except Exception:
                    raise HTTPException(status_code=400, detail="Invalid base64 image data")

        # Update city
        updated = await location_service.update_city(
            city_id, 
            payload, 
            image_bytes=image_bytes, 
            content_type=content_type, 
            storage=storage
        )
        
        if not updated:
            raise HTTPException(status_code=404, detail="City not found")
            
        city = await location_service.get_city(city_id, storage=storage)

    except Exception as e:
        if isinstance(e, HTTPException):
            raise e
        raise HTTPException(status_code=400, detail=str(e))

    return {
        "status": "success",
        "message": "City updated successfully",
        "data": city
    }
    

@router.post(
    "/create",
    response_model=LocationResponse,
    status_code=status.HTTP_201_CREATED,
)

async def create_location(
    location_data: LocationCreate,
    location_service: LocationService = Depends(get_location_service),
):
    try:
        # Basic validation
        name = location_data.name.strip()
        city = location_data.city.strip()
        country = location_data.country.strip()

        # Create location and return created document
        location_id = await location_service.create_location(location_data.model_dump())
        location = await location_service.get_location(location_id)

    except AppException:
        raise
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

    return {
        "status": "success",
        "message": "Location created successfully",
        "data": location
    }

@router.get(
    "/locations",
    response_model=LocationsResponse,
    status_code=status.HTTP_200_OK,
    response_model_by_alias=False,
)
async def get_locations(
    location_list: LocationList = Depends(),
    
    location_service: LocationService = Depends(get_location_service),
    
):
    try:
        search = {}
        if location_list.name:
            search["name"] = location_list.name
        if location_list.city:
            search["city"] = location_list.city
        if location_list.country:
            search["country"] = location_list.country
            
        result = await location_service.list_locations(
            page=location_list.page,
            size=location_list.size,
            sort_by=location_list.sort_by,
            sort_order=location_list.sort_order,
            search=search
        )
    except AppException:
        raise
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

    return {
        "status": "success",
        "message": "Locations retrieved successfully",
        "meta": {
            "total": result["total"],
            "page": result["page"],
            "size": result["size"],
        },
        "data": result["items"],
    }


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
    except AppException:
        raise
    except HTTPException:
        raise
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
    location_data: LocationCreate,
    location_service: LocationService = Depends(get_location_service),
):
    try:
        # Basic validation
        name = location_data.name.strip()
        city = location_data.city.strip()
        country = location_data.country.strip()

        # Update location and return updated document
        updated = await location_service.update_location(location_id, location_data.model_dump())
        if not updated:
            raise HTTPException(status_code=404, detail="Location not found")
        location = await location_service.get_location(location_id)

    except AppException:
        raise
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

    return {
        "status": "success",
        "message": "Location updated successfully",
        "data": location
    }