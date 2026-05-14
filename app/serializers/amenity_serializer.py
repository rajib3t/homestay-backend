class AmenitySerializer:
    @staticmethod
    def serialize(doc):
        if not doc:
            return None

        result = dict(doc)
        result["id"] = str(result.pop("_id"))
        result["status"] = bool(result.get("status", True))

        return result