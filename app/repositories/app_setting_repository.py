from app.repositories.base_repository import BaseRepository


class AppSettingRepository(BaseRepository):
    @property
    def collection(self):
        return self.db.app_setting

    async def save(self, data: dict, session=None):
        return await self.collection.update_one(
            {},
            {"$set": data},
            upsert=True,
            session=session
        )