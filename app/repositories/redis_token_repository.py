from datetime import datetime, timezone
import json


class RedisTokenRepository:
    def __init__(self, redis_client, key_prefix: str = "refresh_token"):
        self.redis = redis_client
        self.key_prefix = key_prefix

    def _build_key(self, token_string: str) -> str:
        return f"{self.key_prefix}:{token_string}"

    @staticmethod
    def _serialize_datetime(value):
        if value is None:
            return None
        if isinstance(value, datetime):
            return value.astimezone(timezone.utc).isoformat()
        return value

    @staticmethod
    def _deserialize_datetime(value):
        if value is None or not isinstance(value, str):
            return value
        return datetime.fromisoformat(value)

    def _serialize_doc(self, token_data: dict) -> dict:
        return {
            "user_id": str(token_data.get("user_id")),
            "token": token_data.get("token"),
            "token_type": token_data.get("token_type"),
            "is_revoked": token_data.get("is_revoked", False),
            "expires_at": self._serialize_datetime(token_data.get("expires_at")),
            "absolute_expiry": self._serialize_datetime(token_data.get("absolute_expiry")),
            "created_at": self._serialize_datetime(token_data.get("created_at")),
            "additional_claims": token_data.get("additional_claims", {}),
        }

    def _deserialize_doc(self, token_data: dict) -> dict:
        return {
            "user_id": token_data.get("user_id"),
            "token": token_data.get("token"),
            "token_type": token_data.get("token_type"),
            "is_revoked": token_data.get("is_revoked", False),
            "expires_at": self._deserialize_datetime(token_data.get("expires_at")),
            "absolute_expiry": self._deserialize_datetime(token_data.get("absolute_expiry")),
            "created_at": self._deserialize_datetime(token_data.get("created_at")),
            "additional_claims": token_data.get("additional_claims", {}),
        }

    async def insert(self, token_data: dict):
        expires_at = token_data.get("expires_at")
        if expires_at is None:
            raise ValueError("Token expiry is required for Redis persistence")

        ttl_seconds = max(int((expires_at - datetime.now(timezone.utc)).total_seconds()), 1)
        serialized_data = json.dumps(self._serialize_doc(token_data))
        await self.redis.set(self._build_key(token_data["token"]), serialized_data, ex=ttl_seconds)
        return True

    async def find_by_token(self, token_string: str):
        serialized_data = await self.redis.get(self._build_key(token_string))
        if not serialized_data:
            return None
        return self._deserialize_doc(json.loads(serialized_data))

    async def revoke(self, token_string: str):
        return await self.redis.delete(self._build_key(token_string))