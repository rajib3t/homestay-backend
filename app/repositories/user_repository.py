from app.repositories.base_repository import BaseRepository
from pymongo.errors import DuplicateKeyError


class UserRepository(BaseRepository):

    @property
    def collection(self):
        return self.db.users

    # -------------------------
    # READ METHODS
    # -------------------------

    async def find_by_email(self, email: str, session=None):
        return await self.collection.find_one(
            {"email": email},
            session=session
        )

    async def find_by_id(self, user_id, session=None):
        return await self.collection.find_one(
            {"_id": self.to_object_id(user_id)},
            session=session
        )

    async def find_by_email_excluding_id(self, email: str, user_id, session=None):
        return await self.collection.find_one(
            {
                "email": email,
                "_id": {"$ne": self.to_object_id(user_id)},
            },
            session=session
        )

    async def find_user_conflict(
        self,
        username: str,
        email: str,
        mobile: str,
        exclude_id=None,
        session=None
    ):
        query = {
            "$or": [
                {"username": username},
                {"email": email},
                {"mobile": mobile}
            ]
        }

        if exclude_id is not None:
            query["_id"] = {"$ne": self.to_object_id(exclude_id)}

        return await self.collection.find_one(
            query,
            {"_id": 1, "username": 1, "email": 1, "mobile": 1},
            session=session
        )

    async def find_many(self, query: dict, session=None):
        cursor = self.collection.find(query, session=session)
        return await cursor.to_list(length=None)

    async def count_documents(self, query: dict, session=None):
        return await self.collection.count_documents(query, session=session)

    async def get_vendor_users(self, session=None):
        cursor = self.collection.find({"role": "vendor"}, session=session)
        return await cursor.to_list(length=None)

    # -------------------------
    # WRITE METHODS
    # -------------------------

    async def insert(self, user_data: dict, session=None):
        try:
            return await self.collection.insert_one(user_data, session=session)
        except DuplicateKeyError as e:
            raise DuplicateKeyError(self._parse_duplicate_error(e))

    async def update_by_id(self, user_id, update_data: dict, session=None):
        return await self.collection.update_one(
            {"_id": self.to_object_id(user_id)},
            {"$set": update_data},
            session=session,  # 🔥 REQUIRED
        )

    # -------------------------
    # INTERNAL HELPERS
    # -------------------------

    def _parse_duplicate_error(self, error: DuplicateKeyError):
        msg = str(error)

        if "email" in msg:
            return "EMAIL_EXISTS"
        if "username" in msg:
            return "USERNAME_EXISTS"
        if "mobile" in msg:
            return "MOBILE_EXISTS"

        return "DUPLICATE_KEY"