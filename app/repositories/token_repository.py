from app.models.token_model import Token
from app.repositories.base_repository import BaseRepository


class TokenRepository(BaseRepository):
    @property
    def collection(self):
        return self.db[Token.COLLECTION_NAME]

    async def insert(self, token_data: dict):
        return await self.collection.insert_one(token_data)

    async def find_by_token(self, token_string: str):
        return await self.collection.find_one({"token": token_string})

    async def revoke(self, token_string: str):
        return await self.collection.update_one(
            {"token": token_string},
            {"$set": {"is_revoked": True}},
        )