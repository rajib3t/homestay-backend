from app.repositories.coming_soon_setting_repository import ComingSoonSettingRepository
from app.services.base_service import BaseService


class ComingSoonSettingService(BaseService):
    def __init__(self, repository: ComingSoonSettingRepository):
        super().__init__(repository.db)
        self.repository = repository
    

    async def get(self, session=None):
        setting = await self.repository.collection.find_one({}, session=session)
        if setting and "_id" in setting:
            setting["id"] = str(setting.pop("_id"))
        return setting

    async def save(self, data: dict, session=None):
        await self.repository.save(data, session=session)
        return await self.get(session=session)