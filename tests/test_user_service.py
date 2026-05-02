import pytest
from datetime import datetime
from types import SimpleNamespace

from app.services.user_service import UserService
from app.core.exceptions import AppException
from app.repositories.user_repository import UserRepository


class FakeCollection:
    def __init__(self):
        self.storage = {}

    class FakeCursor:
        def __init__(self, documents):
            self.documents = list(documents)

        def sort(self, field, direction):
            reverse = direction == -1
            self.documents.sort(key=lambda doc: doc.get(field), reverse=reverse)
            return self

        def skip(self, count):
            self.documents = self.documents[count:]
            return self

        def limit(self, count):
            self.documents = self.documents[:count]
            return self

        def __aiter__(self):
            self._iterator = iter(self.documents)
            return self

        async def __anext__(self):
            try:
                return next(self._iterator)
            except StopIteration as exc:
                raise StopAsyncIteration from exc

    async def find_one(self, query, projection=None):
        # simplistic matching by email, _id, or $or clauses used by the repository
        if "$or" in query:
            for doc in self.storage.values():
                for condition in query["$or"]:
                    field, value = next(iter(condition.items()))
                    if doc.get(field) == value:
                        return doc
            return None
        if "email" in query:
            for doc in self.storage.values():
                if doc.get("email") == query["email"]:
                    return doc
            return None
        if "_id" in query:
            return self.storage.get(str(query["_id"]))
        return None

    async def insert_one(self, doc):
        # emulate inserted_id
        from types import SimpleNamespace
        _id = str(len(self.storage) + 1)
        doc_copy = doc.copy()
        doc_copy["_id"] = _id
        self.storage[_id] = doc_copy
        return SimpleNamespace(inserted_id=_id)

    async def update_one(self, filter_q, update_q):
        _id = str(filter_q.get("_id") if filter_q.get("_id") else filter_q.get("_id"))
        if _id in self.storage:
            for k, v in update_q.get("$set", {}).items():
                self.storage[_id][k] = v
            return SimpleNamespace(matched_count=1)
        return SimpleNamespace(matched_count=0)

    def find(self, query):
        documents = list(self.storage.values())
        return self.FakeCursor(documents)

    async def count_documents(self, query):
        return len(self.storage)


class FakeDB:
    def __init__(self):
        self.users = FakeCollection()


@pytest.mark.asyncio
async def test_create_get_update_user():
    db = FakeDB()
    svc = UserService(UserRepository(db))

    # create user
    user_data = {
        "email": "test@example.com",
        "username": "tester",
        "password": "secret",
        "user_type": "normal",
        "first_name": "T",
        "last_name": "User",
        "mobile": "123",
    }

    user_id = await svc.create_user(user_data.copy())
    assert isinstance(user_id, str)

    user = await svc.get_user(user_id)
    assert user["email"] == "test@example.com"
    assert "password" not in user

    # update user
    updated = await svc.update_user(user_id, {"first_name": "Updated"})
    assert updated["first_name"] == "Updated"
    assert "password" not in updated

    authenticated = await svc.authenticate_user("test@example.com", "secret")
    assert authenticated["email"] == "test@example.com"
    assert "password" not in authenticated


@pytest.mark.asyncio
async def test_duplicate_email():
    db = FakeDB()
    svc = UserService(UserRepository(db))

    user_data = {
        "email": "dup@example.com",
        "username": "a",
        "password": "p",
        "user_type": "normal",
        "first_name": "A",
        "last_name": "B",
        "mobile": "1",
    }

    await svc.create_user(user_data.copy())

    with pytest.raises(AppException):
        await svc.create_user(user_data.copy())


@pytest.mark.asyncio
async def test_get_users_serializes_datetime_fields_and_omits_password():
    db = FakeDB()
    svc = UserService(UserRepository(db))
    created_at = datetime(2026, 3, 14, 20, 28, 4, 563000)
    updated_at = datetime(2026, 3, 26, 14, 55, 40, 717000)
    db.users.storage = {
        "1": {
            "_id": "1",
            "email": "user@example.com",
            "username": "tester",
            "password": "hashed-password",
            "user_type": "normal",
            "first_name": "Test",
            "last_name": "User",
            "mobile": "123",
            "created_at": created_at,
            "updated_at": updated_at,
        }
    }

    result = await svc.get_users()

    assert result["total"] == 1
    assert result["items"][0]["created_at"] == created_at.isoformat()
    assert result["items"][0]["updated_at"] == updated_at.isoformat()
    assert "password" not in result["items"][0]
