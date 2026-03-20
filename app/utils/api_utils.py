import json
import mimetypes
import re
import base64
from typing import Optional
from uuid import uuid4

from fastapi import HTTPException, Request, UploadFile

def handle_exception(e: Exception):
    if isinstance(e, HTTPException):
        raise e
    raise HTTPException(status_code=500, detail=str(e))


async def parse_request_payload(request: Request, form_data: Optional[str]):
    """
    Accept payload from JSON body or multipart form field.
    """
    if form_data:
        try:
            return json.loads(form_data)
        except Exception:
            raise HTTPException(status_code=400, detail="Invalid JSON form data")

    try:
        return await request.json()
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid JSON body")


async def parse_optional_request_payload(
    request: Request,
    form_data: Optional[str],
    *,
    form_field_name: str,
    body_key: Optional[str] = None,
):
    """Accept optional payload from a form field or JSON body.

    Returns an empty dict when the body is missing or not JSON, and validates
    that any provided payload is an object.
    """
    payload = {}

    if form_data:
        try:
            payload = json.loads(form_data)
        except json.JSONDecodeError:
            raise HTTPException(status_code=400, detail=f"Invalid JSON in {form_field_name}")
    else:
        try:
            body = await request.json()
            payload = body.get(body_key, body) if body_key else body
        except Exception:
            payload = {}

    if not isinstance(payload, dict):
        raise HTTPException(status_code=400, detail="Invalid payload format")

    return payload


def parse_base64_image(image_string: str):
    """
    Parse base64 data-url image.
    """
    if not image_string or not image_string.startswith("data:"):
        return None, None

    match = re.match(r"data:(?P<mime>[\w/+-\.]+);base64,(?P<data>.+)", image_string)

    if not match:
        raise HTTPException(status_code=400, detail="Invalid image format")

    try:
        return base64.b64decode(match.group("data")), match.group("mime")
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid base64 image")


async def parse_image_input(image_file: Optional[UploadFile], image_value: Optional[str]):
    """Read either a multipart image upload or a base64 data URL."""
    if image_file:
        return await image_file.read(), image_file.content_type

    if isinstance(image_value, str) and image_value.startswith("data:"):
        return parse_base64_image(image_value)

    return None, None


def build_search(**kwargs):
    """
    Remove None values from search dict.
    """
    return {k: v for k, v in kwargs.items() if v is not None}


def decode_data_url(data_url: str):
    try:
        header, b64data = data_url.split(",", 1)
        mime = header.split(";")[0].split(":", 1)[1]
        raw = base64.b64decode(b64data)
        ext = mimetypes.guess_extension(mime) or f".{mime.split('/')[-1]}"
        return raw, mime, ext
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid icon format")


async def upload_data_url_asset(storage, data_url: str, folder: str, name: str):
    raw, mime, ext = decode_data_url(data_url)
    key_name = name.lower().replace(" ", "_") if name else uuid4().hex
    key = f"{folder}/{key_name}_{uuid4().hex}{ext}"
    await storage.upload_bytes(key, raw, content_type=mime)
    return key


async def replace_data_url_asset(storage, data_url: str, folder: str, name: str, old_key: Optional[str] = None):
    key = await upload_data_url_asset(storage, data_url, folder, name)

    if old_key:
        try:
            await storage.delete_object(old_key)
        except Exception:
            pass

    return key