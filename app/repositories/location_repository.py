import logging

from app.application.dto.location_query import LocationQuery
from app.core.exceptions import AppException
from app.repositories.base_repository import BaseRepository
from app.repositories.builders.city_pipeline_builder import CityPipelineBuilder
from app.repositories.builders.city_query_builder import CityQueryBuilder
from app.repositories.builders.country_query_builder import CountryQueryBuilder
from app.repositories.builders.country_pipeline_builder import CountryPipelineBuilder
from app.repositories.builders.location_query_builder import LocationQueryBuilder
from app.repositories.builders.location_pipeline_builder import LocationPipelineBuilder
from app.serializers.city_serializer import CitySerializer
from app.serializers.country_serializer import CountrySerializer
from bson import ObjectId
from pymongo.errors import DuplicateKeyError

logger = logging.getLogger(__name__)


class LocationRepository(BaseRepository):


    @property
    def countries(self):
        return self.db.countries

    @property
    def cities(self):
        return self.db.cities

    @property
    def locations(self):
        return self.db.locations

    # -------------------------------------------------------------------------
    # Country
    # -------------------------------------------------------------------------

    async def find_country_by_id(self, country_id, session=None):
        return await self.countries.find_one(
            {"_id": self.to_object_id(country_id)},
            session=session,
        )

    async def find_country_conflict(self, name: str, code: str, exclude_id=None, session=None):
        query = {"$or": [{"name": name}, {"code": code}]}
        if exclude_id:
            query["_id"] = {"$ne": self.to_object_id(exclude_id)}
        return await self.countries.find_one(query, {"name": 1, "code": 1}, session=session)

    async def find_countries_by_name(self, name: str, session=None):
        return await self.countries.find(
            {"name": {"$regex": name, "$options": "i"}},
            session=session,
        ).to_list(None)

    async def insert_country(self, country_data: dict, session=None):
        return await self.countries.insert_one(country_data, session=session)

    async def update_country(self, country_id, update_data: dict, session=None):
        try:
            await self.countries.update_one(
                {"_id": self.to_object_id(country_id)},
                {"$set": update_data},
                session=session,
            )
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

    def aggregate_countries(self, pipeline, session=None):
        return self.countries.aggregate(pipeline, session=session)

    async def count_countries(self, query: dict, session=None):
        return await self.countries.count_documents(query, session=session)

    async def list_countries(self, query, session=None):
        self.validate_pagination(page=query.page, size=query.size)

        mongo_query = CountryQueryBuilder.build(query.filters)
        pipeline = CountryPipelineBuilder.build(
            query=mongo_query,
            page=query.page,
            size=query.size,
            sort_by=query.sort_by,
            sort_order=query.sort_order,
        )

        cursor = self.countries.aggregate(pipeline, session=session)
        items = [CountrySerializer.serialize(doc) async for doc in cursor]
        total = await self.countries.count_documents(mongo_query, session=session)

        return {"items": items, "total": total, "page": query.page, "size": query.size}

    # -------------------------------------------------------------------------
    # City
    # -------------------------------------------------------------------------

    async def find_city_by_id(self, city_id, session=None):
        return await self.cities.find_one(
            {"_id": self.to_object_id(city_id)},
            session=session,
        )

    async def find_city_by_slug(self, slug: str, session=None):
        return await self.cities.find_one({"slug": slug}, session=session)

    async def find_city_by_slug_and_country(self, slug: str, country_id, exclude_id=None, session=None):
        query = {"slug": slug, "country": self.to_object_id(country_id)}
        if exclude_id is not None:
            query["_id"] = {"$ne": self.to_object_id(exclude_id)}
        return await self.cities.find_one(query, session=session)

    async def find_city_conflict(self, name: str, country_id, exclude_id=None, session=None):
        query = {"name": name, "country": self.to_object_id(country_id)}
        if exclude_id is not None:
            query["_id"] = {"$ne": self.to_object_id(exclude_id)}
        return await self.cities.find_one(query, session=session)

    async def find_cities_by_country(self, country_id, session=None):
        return await self.cities.find(
            {"country": self.to_object_id(country_id)},
            {"slug": 1},
            session=session,
        ).to_list(None)

    async def find_locations_by_city_name(self, name: str, session=None):
        return await self.cities.find(
            {"name": {"$regex": name, "$options": "i"}},
            session=session,
        ).to_list(None)

    async def insert_city(self, city_data: dict, session=None):
        return await self.cities.insert_one(city_data, session=session)

    async def update_city(self, city_id, update_data: dict, session=None):
        return await self.cities.update_one(
            {"_id": self.to_object_id(city_id)},
            {"$set": update_data},
            session=session,
        )

    def find_cities(self, query: dict, session=None):
        return self.cities.find(query, session=session)

    def aggregate_cities(self, pipeline, session=None):
        return self.cities.aggregate(pipeline, session=session)

    async def count_cities(self, query: dict, session=None):
        return await self.cities.count_documents(query, session=session)

    async def list_cities(self, query, session=None):
        logger.info(f"City query: {query}")
        self.validate_pagination(page=query.page, size=query.size)

        mongo_query = await CityQueryBuilder.build(filters=query.filters, repository=self)
        pipeline = CityPipelineBuilder.build(
            query=mongo_query,
            page=query.page,
            size=query.size,
            sort_by=query.sort_by,
            sort_order=query.sort_order,
        )

        cursor = self.aggregate_cities(pipeline, session=session)
        items = [CitySerializer.serialize(doc) async for doc in cursor]
        total = await self.count_cities(mongo_query, session=session)

        return {"items": items, "total": total, "page": query.page, "size": query.size}

    # -------------------------------------------------------------------------
    # Location
    # -------------------------------------------------------------------------

    async def find_location_by_id(self, location_id, session=None):
        return await self.locations.find_one(
            {"_id": self.to_object_id(location_id)},
            session=session,
        )

    async def find_location_conflict(self, name: str, city_id, country_id, exclude_id=None, session=None):
        query = {
            "name": name,
            "city": self.to_object_id(city_id),
            "country": self.to_object_id(country_id),
        }
        if exclude_id is not None:
            query["_id"] = {"$ne": self.to_object_id(exclude_id)}
        return await self.locations.find_one(query, session=session)

    async def insert_location(self, location_data: dict, session=None):
        return await self.locations.insert_one(location_data, session=session)

    async def update_location(self, location_id, update_data: dict, session=None):
        return await self.locations.update_one(
            {"_id": self.to_object_id(location_id)},
            {"$set": update_data},
            session=session,
        )

    def aggregate_locations(self, pipeline, session=None):
        return self.locations.aggregate(pipeline, session=session)

    async def count_locations(self, query: dict, session=None):
        return await self.locations.count_documents(query, session=session)

    async def list_locations(
        self,
        query: LocationQuery,
        session=None,
    ):
        self.validate_pagination(
            page=query.page,
            size=query.size,
        )

        mongo_query = await LocationQueryBuilder.build(
            filters=query.filters,
            repository=self,
        )

        pipeline = LocationPipelineBuilder.build(
            query=mongo_query,
            page=query.page,
            size=query.size,
            sort_by=query.sort_by,
            sort_order=query.sort_order,
        )

        cursor = self.aggregate_locations(
            pipeline,
            session=session,
        )

        items = []

        async for doc in cursor:
            doc["id"] = str(doc.pop("_id"))
            items.append(doc)

        total = await self.count_locations(
            mongo_query,
            session=session,
        )

        return {
            "items": items,
            "total": total,
            "page": query.page,
            "size": query.size,
        }

    # -------------------------------------------------------------------------
    # Shared helpers
    # -------------------------------------------------------------------------

    