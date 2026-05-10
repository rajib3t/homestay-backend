from app.core.exceptions import AppException
from app.repositories.base_repository import BaseRepository
from app.repositories.builders.country_query_builder import CountryQueryBuilder
from app.repositories.builders.country_pipeline_builder import CountryPipelineBuilder
from app.serializers.country_serializer import CountrySerializer
from pymongo.errors import DuplicateKeyError

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

    async def find_country_by_id(
        self,
        country_id,
        session=None,
    ):
        return await self.countries.find_one(
            {"_id": self.to_object_id(country_id)},
            session=session,
        )

    async def find_country_conflict(
        self,
        name: str,
        code: str,
        exclude_id=None,
        session=None,
    ):

        query = {
            "$or": [
                {"name": name},
                {"code": code},
            ]
        }

        if exclude_id:
            query["_id"] = {
                "$ne": self.to_object_id(exclude_id)
            }

        return await self.countries.find_one(
            query,
            {
                "name": 1,
                "code": 1,
            },
            session=session,
        )

    async def insert_country(self, country_data: dict, session=None):
        return await self.countries.insert_one(country_data, session=session)

    async def update_country(
        self,
        country_id,
        update_data: dict,
        session=None,
    ):

        try:

            await self.countries.update_one(
                {"_id": self.to_object_id(country_id)},
                {"$set": update_data},
                session=session,
            )

        except DuplicateKeyError as e:

            if "name" in str(e):
                raise AppException(
                    status_code=409,
                    message="Country with this name already exists",
                    error_code="COUNTRY_NAME_EXISTS",
                    field="name",
                )

            if "code" in str(e):
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

    async def find_city_by_id(self, city_id, session=None):
        return await self.cities.find_one({"_id": self.to_object_id(city_id)}, session=session)

    async def find_city_conflict(self, name: str, country_id, exclude_id=None, session=None):
        query = {
            "name": name,
            "country": self.to_object_id(country_id),
        }
        if exclude_id is not None:
            query["_id"] = {"$ne": self.to_object_id(exclude_id)}
        return await self.cities.find_one(query, session=session)

    async def insert_city(self, city_data: dict, session=None):
        return await self.cities.insert_one(city_data, session=session)

    async def update_city(self, city_id, update_data: dict, session=None):
        return await self.cities.update_one(
            {"_id": self.to_object_id(city_id)},
            {"$set": update_data},
            session=session
        )

    def find_cities(self, query: dict, session=None):
        return self.cities.find(query, session=session)

    def aggregate_cities(self, pipeline, session=None):
        return self.cities.aggregate(pipeline, session=session)

    async def count_cities(self, query: dict, session=None):
        return await self.cities.count_documents(query, session=session)

    async def find_countries_by_name(self, name: str, session=None):
        return await self.countries.find({"name": {"$regex": name, "$options": "i"}}, session=session).to_list(None)

    async def find_locations_by_city_name(self, name: str, session=None):
        return await self.cities.find({"name": {"$regex": name, "$options": "i"}}, session=session).to_list(None)

    async def find_location_by_id(self, location_id, session=None):
        return await self.locations.find_one({"_id": self.to_object_id(location_id)}, session=session)

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
            session=session
        )

    def aggregate_locations(self, pipeline, session=None):
        return self.locations.aggregate(pipeline, session=session)

    async def count_locations(self, query: dict, session=None):
        return await self.locations.count_documents(query, session=session)
    

    async def list_countries(
        self,
        query,
        session=None,
    ):

        self._validate_pagination(
            page=query.page,
            size=query.size,
        )

        mongo_query = CountryQueryBuilder.build(query.filters)

        pipeline = CountryPipelineBuilder.build(
            query=mongo_query,
            page=query.page,
            size=query.size,
            sort_by=query.sort_by,
            sort_order=query.sort_order,
        )

        cursor = self.countries.aggregate(
            pipeline,
            session=session,
        )

        items = []

        async for doc in cursor:
            items.append(
                CountrySerializer.serialize(doc)
            )

        total = await self.countries.count_documents(
            mongo_query,
            session=session,
        )

        return {
            "items": items,
            "total": total,
            "page": query.page,
            "size": query.size,
        }
    
    @staticmethod
    def _validate_pagination(page: int, size: int):

        try:
            page = int(page)
            size = int(size)

        except Exception:

            raise AppException(
                status_code=400,
                message="Invalid pagination parameters",
                error_code="INVALID_PAGINATION",
                field="pagination",
            )

        if page < 1 or size < 1:

            raise AppException(
                status_code=400,
                message="page and size must be positive integers",
                error_code="INVALID_PAGINATION",
                field="pagination",
            )