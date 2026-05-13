import logging

from app.application.dto.city_query import CityQuery
from app.application.dto.country_query import CountryQuery
from app.application.dto.location_query import LocationQuery
from app.serializers.city_serializer import CitySerializer
from app.services.base_service import BaseService
from app.core.exceptions import AppException
from app.utils.slug_utils import generate_slug, validate_slug
from app.repositories.location_repository import LocationRepository
from bson import ObjectId
from typing import Dict
from pymongo.errors import DuplicateKeyError

logger = logging.getLogger(__name__)


class LocationService(BaseService):
    def __init__(self, repository: LocationRepository):
        super().__init__(repository.db)
        self.repository = repository

    # -------------------------------------------------------------------------
    # Country
    # -------------------------------------------------------------------------

    async def create_country(self, country_data: Dict, session=None):
        country_data["name"] = country_data["name"].strip()
        country_data["code"] = country_data["code"].upper().strip()

        existing = await self.repository.find_country_conflict(
            country_data["name"],
            country_data["code"],
            session=session,
        )

        if existing:
            if existing.get("name") == country_data["name"]:
                raise AppException(
                    status_code=409,
                    message="Country with this name already exists",
                    error_code="COUNTRY_NAME_EXISTS",
                    field="name",
                )
            raise AppException(
                status_code=409,
                message="Country with this code already exists",
                error_code="COUNTRY_CODE_EXISTS",
                field="code",
            )

        try:
            self.timestamps(country_data, is_new=True)
            result = await self.repository.insert_country(country_data, session=session)
            return str(result.inserted_id)

        except DuplicateKeyError as e:
            error_msg = str(e)
            if "name" in error_msg:
                raise AppException(
                    status_code=409,
                    message="Country with this name already exists",
                    error_code="COUNTRY_NAME_EXISTS",
                    field="name",
                )
            if "code" in error_msg:
                raise AppException(
                    status_code=409,
                    message="Country with this code already exists",
                    error_code="COUNTRY_CODE_EXISTS",
                    field="code",
                )
            raise

    async def update_country(self, country_id: str, payload: dict, session=None):
        country_object_id = self._validate_country_id(country_id)

        existing = await self.repository.find_country_by_id(country_object_id, session=session)
        if not existing:
            raise AppException(
                status_code=404,
                message="Country not found",
                error_code="COUNTRY_NOT_FOUND",
                field="country",
            )

        normalized_payload = self._normalize_country_payload(payload)

        await self._ensure_country_unique(
            existing=existing,
            payload=normalized_payload,
            country_id=country_object_id,
            session=session,
        )

        self.timestamps(normalized_payload)

        await self.repository.update_country(
            country_id=country_object_id,
            update_data=normalized_payload,
            session=session,
        )

        updated = await self.repository.find_country_by_id(country_object_id, session=session)
        if updated:
            updated["id"] = str(updated.pop("_id"))
        return updated

    async def toggle_country_status(self, country_id: str, updated_by: str, session=None):
        country_object_id = self._validate_country_id(country_id)

        country = await self.repository.find_country_by_id(country_object_id, session=session)
        if not country:
            raise AppException(
                status_code=404,
                message="Country not found",
                error_code="COUNTRY_NOT_FOUND",
                field="country",
            )

        updated_data = {
            "status": not country.get("status", True),
            "updated_by": updated_by,
        }
        self.timestamps(updated_data)

        await self.repository.update_country(
            country_id=country_object_id,
            update_data=updated_data,
            session=session,
        )

        updated = await self.repository.find_country_by_id(country_object_id, session=session)
        if updated:
            updated["id"] = str(updated.pop("_id"))
        return updated

    async def get_country(self, country_id: str, session=None):
        country_object_id = self._validate_country_id(country_id)

        doc = await self.repository.find_country_by_id(country_object_id, session=session)
        if not doc:
            raise AppException(
                status_code=404,
                message="Country not found",
                error_code="COUNTRY_NOT_FOUND",
                field="country",
            )

        doc["id"] = str(doc.pop("_id"))
        doc.setdefault("dial_code", 1)
        return doc

    async def list_countries(self, query: CountryQuery, session=None):
        return await self.repository.list_countries(query=query, session=session)

    # -------------------------------------------------------------------------
    # Country helpers
    # -------------------------------------------------------------------------

    def _validate_country_id(self, country_id: str) -> ObjectId:
        if not ObjectId.is_valid(country_id):
            raise AppException(
                status_code=400,
                message="Invalid country id",
                error_code="INVALID_COUNTRY_ID",
                field="country",
            )
        return ObjectId(country_id)

    def _normalize_country_payload(self, payload: dict) -> dict:
        normalized = payload.copy()
        if "name" in normalized:
            normalized["name"] = normalized["name"].strip()
        if "code" in normalized:
            normalized["code"] = normalized["code"].strip().upper()
        return normalized

    async def _ensure_country_unique(
        self,
        existing: dict,
        payload: dict,
        country_id,
        session=None,
    ):
        name_changed = "name" in payload and payload["name"] != existing.get("name")
        code_changed = "code" in payload and payload["code"] != existing.get("code")

        if not name_changed and not code_changed:
            return

        duplicate = await self.repository.find_country_conflict(
            name=payload.get("name", existing.get("name")),
            code=payload.get("code", existing.get("code")),
            exclude_id=country_id,
            session=session,
        )

        if not duplicate:
            return

        if duplicate.get("name") == payload.get("name"):
            raise AppException(
                status_code=409,
                message="Country with this name already exists",
                error_code="COUNTRY_NAME_EXISTS",
                field="name",
            )
        raise AppException(
            status_code=409,
            message="Country with this code already exists",
            error_code="COUNTRY_CODE_EXISTS",
            field="code",
        )

    # -------------------------------------------------------------------------
    # City
    # -------------------------------------------------------------------------

    async def create_city(self, city_data: dict, session=None):
        city_data["name"] = city_data["name"].strip()

        if not ObjectId.is_valid(city_data["country"]):
            raise AppException(
                status_code=400,
                message="Invalid country id",
                error_code="INVALID_COUNTRY_ID",
                field="country",
            )

        country_id = ObjectId(city_data["country"])

        country = await self.repository.find_country_by_id(country_id, session=session)
        if not country:
            raise AppException(
                status_code=404,
                message="Country not found",
                error_code="COUNTRY_NOT_FOUND",
                field="country",
            )

        if not city_data.get("slug"):
            existing_cities = await self.repository.find_cities_by_country(country_id, session=session)
            existing_slugs = [c.get("slug", "") for c in existing_cities if c.get("slug")]
            city_data["slug"] = generate_slug(city_data["name"], existing_slugs)
        else:
            if not validate_slug(city_data["slug"]):
                raise AppException(
                    status_code=400,
                    message="Invalid slug format",
                    error_code="INVALID_SLUG",
                    field="slug",
                )
            existing_slug_city = await self.repository.find_city_by_slug_and_country(
                city_data["slug"], country_id, session=session
            )
            if existing_slug_city:
                raise AppException(
                    status_code=409,
                    message="City with this slug already exists in the specified country",
                    error_code="SLUG_ALREADY_EXISTS",
                    field="slug",
                )

        existing = await self.repository.find_city_conflict(
            city_data["name"], country_id, session=session
        )
        if existing:
            raise AppException(
                status_code=409,
                message="City already exists",
                error_code="CITY_ALREADY_EXISTS",
                field="name",
            )

        city_data["country"] = country_id
        self.timestamps(city_data, is_new=True)

        try:
            result = await self.repository.insert_city(city_data, session=session)
            return str(result.inserted_id)
        except DuplicateKeyError:
            raise AppException(
                status_code=409,
                message="City already exists",
                error_code="CITY_ALREADY_EXISTS",
                field="name",
            )

    async def update_city(self, city_id: str, payload: dict, session=None):
        city_object_id = self._validate_city_id(city_id)

        existing_city = await self._get_existing_city(city_object_id, session=session)

        normalized_payload = self._normalize_city_payload(
            payload=payload,
            existing_city=existing_city,
        )

        await self._validate_country(normalized_payload["country"], session=session)

        if "slug" in normalized_payload:
            if normalized_payload["slug"]:
                if not validate_slug(normalized_payload["slug"]):
                    raise AppException(
                        status_code=400,
                        message="Invalid slug format",
                        error_code="INVALID_SLUG",
                        field="slug",
                    )
                existing_slug_city = await self.repository.find_city_by_slug_and_country(
                    normalized_payload["slug"],
                    normalized_payload["country"],
                    exclude_id=city_object_id,
                    session=session,
                )
                if existing_slug_city:
                    raise AppException(
                        status_code=409,
                        message="City with this slug already exists in the specified country",
                        error_code="SLUG_ALREADY_EXISTS",
                        field="slug",
                    )
            else:
                existing_cities = await self.repository.find_cities_by_country(
                    normalized_payload["country"], session=session
                )
                existing_slugs = [
                    c.get("slug", "") for c in existing_cities
                    if c.get("slug") and str(c.get("_id")) != city_id
                ]
                normalized_payload["slug"] = generate_slug(normalized_payload["name"], existing_slugs)

        await self._ensure_city_unique(
            name=normalized_payload["name"],
            country_id=normalized_payload["country"],
            city_id=city_object_id,
            session=session,
        )

        self.timestamps(normalized_payload)

        await self.repository.update_city(
            city_id=city_object_id,
            update_data=normalized_payload,
            session=session,
        )

        updated_city = await self.repository.find_city_by_id(city_object_id, session=session)
        return CitySerializer.serialize(updated_city)

    async def get_city(self, city_id: str, session=None):
        city_object_id = self._validate_city_id(city_id)

        doc = await self.repository.find_city_by_id(city_object_id, session=session)
        if not doc:
            raise AppException(
                status_code=404,
                message="City not found",
                error_code="CITY_NOT_FOUND",
                field="city",
            )

        doc["id"] = str(doc.pop("_id"))
        if "country" in doc and not isinstance(doc["country"], str):
            doc["country"] = str(doc["country"])
        return doc

    async def get_city_by_slug(self, slug: str, session=None):
        if not slug:
            raise AppException(
                status_code=400,
                message="Slug is required",
                error_code="SLUG_REQUIRED",
                field="slug",
            )

        doc = await self.repository.find_city_by_slug(slug, session=session)
        if not doc:
            raise AppException(
                status_code=404,
                message="City not found",
                error_code="CITY_NOT_FOUND",
                field="city",
            )

        doc["id"] = str(doc.pop("_id"))
        if "country" in doc and not isinstance(doc["country"], str):
            doc["country"] = str(doc["country"])
        return doc

    async def get_raw_city(self, city_id: str, session=None):
        city_object_id = self._validate_city_id(city_id)

        city = await self.repository.find_city_by_id(city_object_id, session=session)
        if not city:
            raise AppException(
                status_code=404,
                message="City not found",
                error_code="CITY_NOT_FOUND",
                field="city",
            )
        return city

    async def list_cities(self, query: CityQuery, session=None):
        return await self.repository.list_cities(query=query, session=session)

    async def list_cities_by_country(self, country_id: str, session=None):
        country_object_id = self._validate_country_id(country_id)

        country = await self.repository.find_country_by_id(country_object_id, session=session)
        if not country:
            raise AppException(
                status_code=404,
                message="Country not found",
                error_code="COUNTRY_NOT_FOUND",
                field="country",
            )

        query = {
            "country": {
                "$in": [country["_id"], str(country["_id"]), country.get("name")]
            }
        }

        items = []
        async for doc in self.repository.find_cities(query):
            doc["id"] = str(doc.pop("_id"))
            if "country" in doc and not isinstance(doc["country"], str):
                doc["country"] = str(doc["country"])
            items.append(doc)
        return items

    # -------------------------------------------------------------------------
    # City helpers
    # -------------------------------------------------------------------------

    def _validate_city_id(self, city_id: str) -> ObjectId:
        if not ObjectId.is_valid(city_id):
            raise AppException(
                status_code=400,
                message="Invalid city id",
                error_code="INVALID_CITY_ID",
                field="city",
            )
        return ObjectId(city_id)

    async def _get_existing_city(self, city_id, session=None) -> dict:
        city = await self.repository.find_city_by_id(city_id, session=session)
        if not city:
            raise AppException(
                status_code=404,
                message="City not found",
                error_code="CITY_NOT_FOUND",
                field="city",
            )
        return city

    def _normalize_city_payload(self, payload: dict, existing_city: dict) -> dict:
        normalized = payload.copy()

        normalized["name"] = payload.get("name", existing_city["name"]).strip()

        country_id = payload.get("country", existing_city["country"])
        if isinstance(country_id, str):
            if not ObjectId.is_valid(country_id):
                raise AppException(
                    status_code=400,
                    message="Invalid country id",
                    error_code="INVALID_COUNTRY_ID",
                    field="country",
                )
            country_id = ObjectId(country_id)

        normalized["country"] = country_id
        return normalized

    async def _validate_country(self, country_id, session=None):
        country = await self.repository.find_country_by_id(country_id, session=session)
        if not country:
            raise AppException(
                status_code=404,
                message="Country not found",
                error_code="COUNTRY_NOT_FOUND",
                field="country",
            )

    async def _ensure_city_unique(self, name: str, country_id, city_id, session=None):
        duplicate = await self.repository.find_city_conflict(
            name=name,
            country_id=country_id,
            exclude_id=city_id,
            session=session,
        )
        if duplicate:
            raise AppException(
                status_code=409,
                message="City with this name already exists in the specified country",
                error_code="CITY_ALREADY_EXISTS",
                field="name",
            )

    # -------------------------------------------------------------------------
    # Location
    # -------------------------------------------------------------------------

    async def create_location(
        self,
        payload: dict,
        session=None,
    ):
        normalized = await self._normalize_location_payload(
            payload,
            session=session,
        )

        await self._ensure_location_unique(
            name=normalized["name"],
            city_id=normalized["city"],
            country_id=normalized["country"],
            session=session,
        )

        self.timestamps(normalized, is_new=True)

        result = await self.repository.insert_location(
            normalized,
            session=session,
        )

        created = await self.repository.find_location_by_id(
            result.inserted_id,
            session=session,
        )

        return self._serialize_location(created)

    async def get_location(
        self,
        location_id: str,
        session=None,
    ):
        location_object_id = self._validate_location_id(
            location_id
        )

        location = await self._get_existing_location(
            location_object_id,
            session=session,
        )

        return self._serialize_location(location)

    async def list_locations(
        self,
        query: LocationQuery,
        session=None,
    ):
        return await self.repository.list_locations(
            query=query,
            session=session,
        )

    async def update_location(
        self,
        location_id: str,
        payload: dict,
        session=None,
    ):

        location_object_id = self._validate_location_id(
            location_id
        )

        existing = await self._get_existing_location(
            location_object_id,
            session=session,
        )

        normalized_payload = await self._normalize_location_update_payload(
            payload=payload,
            existing=existing,
            session=session,
        )

        await self._ensure_location_unique(
            name=normalized_payload["name"],
            city_id=normalized_payload["city"],
            country_id=normalized_payload["country"],
            exclude_id=location_object_id,
            session=session,
        )

        self.timestamps(normalized_payload)

        await self.repository.update_location(
            location_id=location_object_id,
            update_data=normalized_payload,
            session=session,
        )

        updated = await self._get_existing_location(
            location_object_id,
            session=session,
        )

        return self._serialize_location(updated)
    
    async def _normalize_location_update_payload(
        self,
        payload: dict,
        existing: dict,
        session=None,
    ):

        normalized = payload.copy()

        normalized["name"] = payload.get(
            "name",
            existing["name"],
        ).strip()

        country_id = payload.get(
            "country",
            existing["country"],
        )

        city_id = payload.get(
            "city",
            existing["city"],
        )

        country_id = self._validate_country_id(
            str(country_id)
        )

        city_id = self._validate_city_id(
            str(city_id)
        )

        await self._validate_country_exists(
            country_id,
            session=session,
        )

        await self._validate_city_exists(
            city_id,
            session=session,
        )

        normalized["country"] = country_id
        normalized["city"] = city_id

        return normalized
    
    async def _normalize_location_payload(
        self,
        payload: dict,
        session=None,
    ):
        normalized = payload.copy()

        normalized["name"] = normalized["name"].strip()

        country_id = self._validate_country_id(
            payload["country"]
        )

        city_id = self._validate_city_id(
            payload["city"]
        )

        await self._validate_country_exists(
            country_id,
            session=session,
        )

        await self._validate_city_exists(
            city_id,
            session=session,
        )

        normalized["country"] = country_id
        normalized["city"] = city_id

        return normalized
    
    async def _validate_country_exists(
        self,
        country_id,
        session=None,
    ):
        country = await self.repository.find_country_by_id(
            country_id,
            session=session,
        )

        if not country:
            raise AppException(
                status_code=404,
                message="Country not found",
                error_code="COUNTRY_NOT_FOUND",
                field="country",
            )
        
    async def _validate_city_exists(
        self,
        city_id,
        session=None,
    ):
        city = await self.repository.find_city_by_id(
            city_id,
            session=session,
        )

        if not city:
            raise AppException(
                status_code=404,
                message="City not found",
                error_code="CITY_NOT_FOUND",
                field="city",
            )
        
    async def _ensure_location_unique(
        self,
        name: str,
        city_id,
        country_id,
        exclude_id=None,
        session=None,
    ):

        existing = await self.repository.find_location_conflict(
            name=name,
            city_id=city_id,
            country_id=country_id,
            exclude_id=exclude_id,
            session=session,
        )

        if existing:
            raise AppException(
                status_code=409,
                message="Location with this name already exists in the specified city and country",
                error_code="LOCATION_ALREADY_EXISTS",
                field="name",
            )
        
    def _serialize_location(self, doc: dict):

        if not doc:
            return None

        doc["id"] = str(doc.pop("_id"))

        if "country" in doc:
            doc["country"] = str(doc["country"])

        if "city" in doc:
            doc["city"] = str(doc["city"])

        return doc
    
    def _validate_location_id(
        self,
        location_id: str,
    ) -> ObjectId:

        if not ObjectId.is_valid(location_id):
            raise AppException(
                status_code=400,
                message="Invalid location id",
                error_code="INVALID_LOCATION_ID",
                field="location",
            )

        return ObjectId(location_id)
    
    async def _get_existing_location(
        self,
        location_id,
        session=None,
    ):

        location = await self.repository.find_location_by_id(
            location_id,
            session=session,
        )

        if not location:
            raise AppException(
                status_code=404,
                message="Location not found",
                error_code="LOCATION_NOT_FOUND",
                field="location",
            )

        return location