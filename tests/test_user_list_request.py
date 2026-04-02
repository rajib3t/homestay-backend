import pytest
from pydantic import ValidationError

from app.models.user_model import ListUsers


def test_list_users_uses_first_name_as_default_sort_field():
    params = ListUsers()

    assert params.sort_by == "first_name"


def test_list_users_accepts_name_sort_alias():
    params = ListUsers(sort_by="name")

    assert params.sort_by == "first_name"


def test_list_users_rejects_unknown_sort_field():
    with pytest.raises(ValidationError):
        ListUsers(sort_by="created_at")
