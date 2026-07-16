class PropertySerializer:
    @staticmethod
    def serialize(doc) -> dict:
        if not doc:
            return None

        result = dict(doc)

        # Handle _id to id conversion if not already done
        if "_id" in result:
            result["id"] = str(result.pop("_id"))
        elif "id" not in result:
            result["id"] = str(result.get("_id", ""))

        created_at = result.get("created_at")
        updated_at = result.get("updated_at")
        if created_at and hasattr(created_at, "isoformat"):
            result["created_at"] = created_at.isoformat()
        if updated_at and hasattr(updated_at, "isoformat"):
            result["updated_at"] = updated_at.isoformat()

        return result