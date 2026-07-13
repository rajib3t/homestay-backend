from app.services.base_service import BaseService
from app.repositories.app_setting_repository import AppSettingRepository


class AppSettingService(BaseService):
    def __init__(self, repository: AppSettingRepository):
        super().__init__(repository.db)
        self.repository = repository

    async def get_setting(self, session=None):
        setting = await self.repository.collection.find_one({}, session=session)
        if setting and "_id" in setting:
            setting["id"] = str(setting.pop("_id"))
        return setting

    async def save_setting(self, data: dict, session=None):
        await self.repository.save(data, session=session)
        return await self.get_setting(session=session)
