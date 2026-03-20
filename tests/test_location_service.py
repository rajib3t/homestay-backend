import pytest
from types import SimpleNamespace

from bson import ObjectId

from app.core.exceptions import AppException
from app.repositories.location_repository import LocationRepository
from app.services.location_service import LocationService


class FakeCursor:
    def __init__(self, items):
        self.items = list(items)
        self.index = 0

    def __aiter__(self):
        return self

    async def __anext__(self):
        if self.index >= len(self.items):
            raise StopAsyncIteration
        item = self.items[self.index]
        self.index += 1
        return item


class FakeCountriesCollection:
    def __init__(self):
        self.storage = {}

    async def find_one(self, query, projection=None):
        if "_id" in query and not isinstance(query["_id"], dict):
            return self.storage.get(query["_id"])

        if "$or" in query:
            excluded = query.get("_id", {}).get("$ne")
            for doc in self.storage.values():
                if excluded is not None and doc["_id"] == excluded:
                    continue
                if any(all(doc.get(key) == value for key, value in clause.items()) for clause in query["$or"]):
                    return doc
            return None

        return None

    async def insert_one(self, doc):
        object_id = ObjectId()
        stored = doc.copy()
        stored["_id"] = object_id
        self.storage[object_id] = stored
        return SimpleNamespace(inserted_id=object_id)

    async def update_one(self, filter_q, update_q):
        object_id = filter_q["_id"]
        if object_id not in self.storage:
            return SimpleNamespace(matched_count=0)
        self.storage[object_id].update(update_q.get("$set", {}))
        return SimpleNamespace(matched_count=1)

    def aggregate(self, pipeline):
        return FakeCursor([])

    async def count_documents(self, query):
        return len(self.storage)


class FakeDB:
    def __init__(self):
        self.countries = FakeCountriesCollection()


@pytest.mark.asyncio
async def test_create_and_get_country_uses_repository_backed_service():
    db = FakeDB()
    service = LocationService(LocationRepository(db))

    country_id = await service.create_country(
        {
            "name": " bangladesh ",
            "code": "bd",
            "dial_code": 880,
            "status": True,
        }
    )

    country = await service.get_country(country_id)

    assert country["_id"] == country_id
    assert country["name"] == "bangladesh"
    assert country["code"] == "BD"
    assert country["dial_code"] == 880


@pytest.mark.asyncio
async def test_update_country_rejects_duplicate_code():
    db = FakeDB()
    service = LocationService(LocationRepository(db))

    first_country_id = await service.create_country(
        {
            "name": "Bangladesh",
            "code": "BD",
            "dial_code": 880,
            "status": True,
        }
    )
    second_country_id = await service.create_country(
        {
            "name": "India",
            "code": "IN",
            "dial_code": 91,
            "status": True,
        }
    )

    with pytest.raises(AppException) as exc_info:
        await service.update_country(second_country_id, {"code": "BD"})

    assert first_country_id != second_country_id
    assert exc_info.value.status_code == 409