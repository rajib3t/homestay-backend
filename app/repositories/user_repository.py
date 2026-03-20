from app.repositories.base_repository import BaseRepository


class UserRepository(BaseRepository):
    @property
    def collection(self):
        return self.db.users

    async def find_by_email(self, email: str):
        return await self.collection.find_one({"email": email})

    async def find_by_id(self, user_id):
        return await self.collection.find_one({"_id": self.to_object_id(user_id)})

    async def find_by_email_excluding_id(self, email: str, user_id):
        return await self.collection.find_one(
            {
                "email": email,
                "_id": {"$ne": self.to_object_id(user_id)},
            }
        )

    async def insert(self, user_data: dict):
        return await self.collection.insert_one(user_data)

    async def update_by_id(self, user_id, update_data: dict):
        return await self.collection.update_one(
            {"_id": self.to_object_id(user_id)},
            {"$set": update_data},
        )
    
    async def get_vendor_users(self):
        return await self.collection.find({"role": "vendor"}).to_list(length=None)