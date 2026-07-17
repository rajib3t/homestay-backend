from app.repositories.base_repository import BaseRepository


class ComingSoonSettingRepository(BaseRepository):
    def __init__(self, db):
        super().__init__(db)
        self.collection_name = "coming_soon_settings"

    @property
    def collection(self):
        return getattr(self.db, self.collection_name)


    async def save(self, data: dict, session=None):
        return await self.collection.update_one(
            {},
            {"$set": data},
            upsert=True,
            session=session
        )
