from app.repositories.base_repository import BaseRepository


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

    async def find_country_by_id(self, country_id):
        return await self.countries.find_one({"_id": self.to_object_id(country_id)})

    async def find_country_conflict(self, name: str, code: str, exclude_id=None):
        query = {"$or": [{"name": name}, {"code": code}]}
        if exclude_id is not None:
            query["_id"] = {"$ne": self.to_object_id(exclude_id)}
        return await self.countries.find_one(query, {"name": 1, "code": 1})

    async def insert_country(self, country_data: dict):
        return await self.countries.insert_one(country_data)

    async def update_country(self, country_id, update_data: dict):
        return await self.countries.update_one(
            {"_id": self.to_object_id(country_id)},
            {"$set": update_data},
        )

    def aggregate_countries(self, pipeline):
        return self.countries.aggregate(pipeline)

    async def count_countries(self, query: dict):
        return await self.countries.count_documents(query)

    async def find_city_by_id(self, city_id):
        return await self.cities.find_one({"_id": self.to_object_id(city_id)})

    async def find_city_conflict(self, name: str, country_id, exclude_id=None):
        query = {
            "name": name,
            "country": self.to_object_id(country_id),
        }
        if exclude_id is not None:
            query["_id"] = {"$ne": self.to_object_id(exclude_id)}
        return await self.cities.find_one(query)

    async def insert_city(self, city_data: dict):
        return await self.cities.insert_one(city_data)

    async def update_city(self, city_id, update_data: dict):
        return await self.cities.update_one(
            {"_id": self.to_object_id(city_id)},
            {"$set": update_data},
        )

    def find_cities(self, query: dict):
        return self.cities.find(query)

    def aggregate_cities(self, pipeline):
        return self.cities.aggregate(pipeline)

    async def count_cities(self, query: dict):
        return await self.cities.count_documents(query)

    async def find_countries_by_name(self, name: str):
        return await self.countries.find({"name": {"$regex": name, "$options": "i"}}).to_list(None)

    async def find_locations_by_city_name(self, name: str):
        return await self.cities.find({"name": {"$regex": name, "$options": "i"}}).to_list(None)

    async def find_location_by_id(self, location_id):
        return await self.locations.find_one({"_id": self.to_object_id(location_id)})

    async def find_location_conflict(self, name: str, city_id, country_id, exclude_id=None):
        query = {
            "name": name,
            "city": self.to_object_id(city_id),
            "country": self.to_object_id(country_id),
        }
        if exclude_id is not None:
            query["_id"] = {"$ne": self.to_object_id(exclude_id)}
        return await self.locations.find_one(query)

    async def insert_location(self, location_data: dict):
        return await self.locations.insert_one(location_data)

    async def update_location(self, location_id, update_data: dict):
        return await self.locations.update_one(
            {"_id": self.to_object_id(location_id)},
            {"$set": update_data},
        )

    def aggregate_locations(self, pipeline):
        return self.locations.aggregate(pipeline)

    async def count_locations(self, query: dict):
        return await self.locations.count_documents(query)