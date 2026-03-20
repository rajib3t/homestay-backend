from bson import ObjectId


class BaseRepository:
    def __init__(self, db):
        self.db = db

    @staticmethod
    def to_object_id(value):
        if isinstance(value, str) and ObjectId.is_valid(value):
            return ObjectId(value)
        return value