import json
import mimetypes
import re
import base64
from typing import Optional
from fastapi import HTTPException, Request

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