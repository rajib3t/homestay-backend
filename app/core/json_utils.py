import json
from datetime import date, datetime

from bson import ObjectId


def json_default(obj):
    if isinstance(obj, ObjectId):
        return str(obj)
    if isinstance(obj, (datetime, date)):
        return obj.isoformat()
    raise TypeError(f"Object of type {type(obj).__name__} is not JSON serializable")


def dumps(obj, **kwargs):
    return json.dumps(obj, default=json_default, **kwargs)
