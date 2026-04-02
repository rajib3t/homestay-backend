import pytest

from app.core.create_indexes import IndexCreator


class FakeCollection:
    def __init__(self, name, existing_indexes=None):
        self.name = name
        self.existing_indexes = existing_indexes or {
            "_id_": {"key": [("_id", 1)]}
        }
        self.create_calls = []

    async def index_information(self):
        return self.existing_indexes

    async def create_index(self, keys, name=None, **options):
        index_name = name or "_".join(f"{field}_{direction}" for field, direction in keys)
        self.create_calls.append({"keys": list(keys), "name": index_name, "options": options})
        self.existing_indexes[index_name] = {"key": list(keys), **options}
        return index_name


class FakeDB:
    def __init__(self):
        self.users = FakeCollection(
            "users",
            existing_indexes={
                "_id_": {"key": [("_id", 1)]},
                "email_1": {
                    "key": [("email", 1)],
                    "unique": True,
                    "background": True,
                    "collation": {"locale": "en", "strength": 2},
                },
            },
        )
        self.countries = FakeCollection("countries")
        self.cities = FakeCollection("cities")
        self.locations = FakeCollection("locations")
        self.amenities = FakeCollection("amenities")
        self.facilities = FakeCollection("facilities")
        self.room_types = FakeCollection("room_types")


@pytest.mark.asyncio
async def test_ensure_indexes_skips_conflicting_existing_named_index():
    db = FakeDB()

    await IndexCreator.ensure_indexes(db)

    assert all(call["name"] != "email_1" for call in db.users.create_calls)
    assert any(call["name"] == "username_1" for call in db.users.create_calls)
    assert any(call["name"] == "mobile_1" for call in db.users.create_calls)


@pytest.mark.asyncio
async def test_ensure_indexes_creates_email_index_when_missing():
    db = FakeDB()
    db.users = FakeCollection("users")

    await IndexCreator.ensure_indexes(db)

    email_index_call = next(call for call in db.users.create_calls if call["name"] == "email_1")
    assert email_index_call["keys"] == [("email", 1)]
    assert email_index_call["options"]["unique"] is True
    assert email_index_call["options"]["sparse"] is True