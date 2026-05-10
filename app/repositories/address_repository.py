from app.repositories.base_repository import BaseRepository


class AddressRepository(BaseRepository):
    @property
    def collection(self):
        return self.db.addresses

    async def find_by_id(self, address_id: str):
        return await self.collection.find_one({"_id": self.to_object_id(address_id)})

    async def find_by_company_id(self, company_id: str):
        return await self.collection.find_one({"company_id": company_id})

    async def find_by_user_id(self, user_id: str):
        return await self.collection.find_one({"user_id": user_id})

    async def insert(self, address_data: dict, session=None):
        return await self.collection.insert_one(address_data, session=session)

    async def update_by_id(self, address_id: str, update_data: dict, session=None):
        return await self.collection.update_one(
            {"_id": self.to_object_id(address_id)},
            {"$set": update_data},
            session=session,
        )

    async def delete_by_company_id(self, company_id: str):
        return await self.collection.delete_many({"company_id": company_id})

    async def count_documents(self, query: dict):
        return await self.collection.count_documents(query)
