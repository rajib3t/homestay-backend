from datetime import datetime, timezone


class BaseService:
    def __init__(self, db):
        self.db = db

    def timestamps(self, data: dict, is_new: bool = False):
        now = datetime.now(timezone.utc)

        if is_new:
            data["created_at"] = now

        data["updated_at"] = now
        return data