import pytest

from app.seeds.admin_user_seeder import AdminUserSeeder


class FakeInsertResult:
    def __init__(self, inserted_id="admin-id"):
        self.inserted_id = inserted_id


class FakeUserRepository:
    def __init__(self, existing=None):
        self.existing = existing
        self.inserted = []

    async def find_by_email(self, email: str, session=None):
        return self.existing

    async def insert(self, user_data: dict, session=None):
        self.inserted.append(user_data)
        return FakeInsertResult()


@pytest.mark.asyncio
async def test_admin_user_seeder_creates_admin_once(monkeypatch):
    from app.core import config as config_module

    monkeypatch.setattr(config_module.settings, "ADMIN_USER_USERNAME", "admin")
    monkeypatch.setattr(config_module.settings, "ADMIN_USER_EMAIL", "admin@example.com")
    monkeypatch.setattr(config_module.settings, "ADMIN_USER_PASSWORD", "Secret123")
    monkeypatch.setattr(config_module.settings, "ADMIN_USER_FIRST_NAME", "Admin")
    monkeypatch.setattr(config_module.settings, "ADMIN_USER_LAST_NAME", "User")
    monkeypatch.setattr(config_module.settings, "ADMIN_USER_MOBILE", "9876543210")

    repo = FakeUserRepository()
    seeder = AdminUserSeeder(repo)

    result = await seeder.seed()

    assert result["created"] is True
    assert repo.inserted[0]["user_type"] == "admin"
    assert repo.inserted[0]["email"] == "admin@example.com"
    assert repo.inserted[0]["username"] == "admin"
    assert repo.inserted[0]["password"] != "Secret123"


@pytest.mark.asyncio
async def test_admin_user_seeder_is_idempotent(monkeypatch):
    from app.core import config as config_module

    monkeypatch.setattr(config_module.settings, "ADMIN_USER_USERNAME", "admin")
    monkeypatch.setattr(config_module.settings, "ADMIN_USER_EMAIL", "admin@example.com")
    monkeypatch.setattr(config_module.settings, "ADMIN_USER_PASSWORD", "Secret123")
    monkeypatch.setattr(config_module.settings, "ADMIN_USER_FIRST_NAME", "Admin")
    monkeypatch.setattr(config_module.settings, "ADMIN_USER_LAST_NAME", "User")
    monkeypatch.setattr(config_module.settings, "ADMIN_USER_MOBILE", "9876543210")

    repo = FakeUserRepository(existing={"_id": "existing"})
    seeder = AdminUserSeeder(repo)

    result = await seeder.seed()

    assert result["created"] is False
    assert repo.inserted == []
