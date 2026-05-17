class UserSerializer:
    @staticmethod
    def serialize(doc):
        if not doc:
            return None

        result = dict(doc)
        result["id"] = str(result.pop("_id"))
        

        return result