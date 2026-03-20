import pytest
from fastapi import HTTPException

from app.utils.api_utils import parse_image_input, parse_optional_request_payload


class FakeRequest:
    def __init__(self, json_data=None, raise_on_json=False):
        self._json_data = json_data
        self._raise_on_json = raise_on_json

    async def json(self):
        if self._raise_on_json:
            raise ValueError("no json")
        return self._json_data


class FakeUploadFile:
    def __init__(self, data: bytes, content_type: str):
        self._data = data
        self.content_type = content_type

    async def read(self):
        return self._data


@pytest.mark.asyncio
async def test_parse_optional_request_payload_reads_form_json():
    payload = await parse_optional_request_payload(
        FakeRequest(),
        '{"name": "Dhaka"}',
        form_field_name="city_data",
        body_key="city_data",
    )

    assert payload == {"name": "Dhaka"}


@pytest.mark.asyncio
async def test_parse_optional_request_payload_reads_named_body_field():
    payload = await parse_optional_request_payload(
        FakeRequest({"city_data": {"name": "Dhaka"}}),
        None,
        form_field_name="city_data",
        body_key="city_data",
    )

    assert payload == {"name": "Dhaka"}


@pytest.mark.asyncio
async def test_parse_optional_request_payload_returns_empty_dict_for_missing_json():
    payload = await parse_optional_request_payload(
        FakeRequest(raise_on_json=True),
        None,
        form_field_name="city_data",
        body_key="city_data",
    )

    assert payload == {}


@pytest.mark.asyncio
async def test_parse_optional_request_payload_rejects_non_object_payload():
    with pytest.raises(HTTPException) as exc_info:
        await parse_optional_request_payload(
            FakeRequest(),
            '["invalid"]',
            form_field_name="city_data",
            body_key="city_data",
        )

    assert exc_info.value.status_code == 400
    assert exc_info.value.detail == "Invalid payload format"


@pytest.mark.asyncio
async def test_parse_image_input_prefers_uploaded_file():
    image_bytes, content_type = await parse_image_input(
        FakeUploadFile(b"file-bytes", "image/png"),
        "data:image/png;base64,aWdub3JlZA==",
    )

    assert image_bytes == b"file-bytes"
    assert content_type == "image/png"


@pytest.mark.asyncio
async def test_parse_image_input_reads_base64_data_url():
    image_bytes, content_type = await parse_image_input(
        None,
        "data:image/png;base64,aGVsbG8=",
    )

    assert image_bytes == b"hello"
    assert content_type == "image/png"