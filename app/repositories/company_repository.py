from app.repositories.base_repository import BaseRepository


class CompanyRepository(BaseRepository):
    @property
    def collection(self):
        return self.db.companies

    async def find_by_id(self, company_id: str):
        return await self.collection.find_one({"_id": self.to_object_id(company_id)})

    async def find_by_email(self, email: str):
        return await self.collection.find_one({"email": email})

    async def find_by_user_id(self, user_id: str):
        return await self.collection.find_one({"user_id": user_id})

    async def insert(self, company_data: dict):
        return await self.collection.insert_one(company_data)

    async def update_by_id(self, company_id: str, update_data: dict):
        return await self.collection.update_one(
            {"_id": self.to_object_id(company_id)},
            {"$set": update_data},
        )

    async def count_documents(self, query: dict):
        return await self.collection.count_documents(query)
