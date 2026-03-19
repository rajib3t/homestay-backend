import pytest
from types import SimpleNamespace

from bson import ObjectId

from app.services.attribute_service import AttributeService


class FakeCollection:
    def __init__(self):
        self.storage = {}

    async def insert_one(self, doc):
        object_id = ObjectId()
        doc_copy = doc.copy()
        doc_copy["_id"] = object_id
        self.storage[object_id] = doc_copy
        return SimpleNamespace(inserted_id=object_id)

    async def find_one(self, query):
        object_id = query.get("_id")
        return self.storage.get(object_id)

    async def update_one(self, filter_q, update_q):
        object_id = filter_q.get("_id")
        if object_id not in self.storage:
            return SimpleNamespace(matched_count=0)

        self.storage[object_id].update(update_q.get("$set", {}))
        return SimpleNamespace(matched_count=1)


class FakeDB:
    def __init__(self):
        self.facilities = FakeCollection()


@pytest.mark.asyncio
async def test_update_facility_updates_icon_and_name():
    db = FakeDB()
    service = AttributeService(db)

    facility_id = await service.create_facility(
        {"name": "Pool", "icon": "facilities/pool-old.png", "status": True}
    )

    updated = await service.update_facility(
        facility_id,
        {"name": "Infinity Pool", "icon": "facilities/pool-new.png"}
    )

    assert updated["name"] == "Infinity Pool"
    assert updated["icon"] == "facilities/pool-new.png"
    assert updated["status"] is True


@pytest.mark.asyncio
async def test_update_facility_requires_update_fields():
    db = FakeDB()
    service = AttributeService(db)

    facility_id = await service.create_facility(
        {"name": "Gym", "icon": None, "status": True}
    )

    with pytest.raises(Exception):
        await service.update_facility(facility_id, {})