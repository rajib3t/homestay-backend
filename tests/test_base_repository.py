from app.repositories.base_repository import BaseRepository
from bson import ObjectId


class DummyDB:
    pass


def test_to_object_id_converts_valid_hex_string_to_objectid():
    repo = BaseRepository(DummyDB())
    object_id = repo.to_object_id("507f1f77bcf86cd799439011")

    assert isinstance(object_id, ObjectId)
    assert str(object_id) == "507f1f77bcf86cd799439011"


def test_to_object_id_returns_non_object_string_as_is():
    repo = BaseRepository(DummyDB())
    value = repo.to_object_id("not-a-valid-id")

    assert value == "not-a-valid-id"
