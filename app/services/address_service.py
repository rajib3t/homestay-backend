from datetime import datetime
from typing import Optional

from app.services.base_service import BaseService
from app.core.exceptions import AppException
from app.repositories.address_repository import AddressRepository


class AddressService(BaseService):
    def __init__(self, repository: AddressRepository):
        super().__init__(repository.db)
        self.repository = repository

    @staticmethod
    def _serialize_address(address: dict):
        if not address:
            return None
        address = address.copy()
        address["id"] = str(address.pop("_id"))

        if address.get("created_at") and isinstance(address.get("created_at"), datetime):
            address["created_at"] = address["created_at"].isoformat()

        if address.get("updated_at") and isinstance(address.get("updated_at"), datetime):
            address["updated_at"] = address["updated_at"].isoformat()

        # Remove internal fields from response
        address.pop("user_id", None)
        address.pop("company_id", None)

        return address

    async def create_address(self, address_data: dict):
        self.timestamps(address_data, is_new=True)
        result = await self.repository.insert(address_data)
        return str(result.inserted_id)

    async def get_address_by_company_id(self, company_id: str):
        address = await self.repository.find_by_company_id(company_id)
        if not address:
            return None
        return self._serialize_address(address)

    async def get_address_by_id(self, address_id: str):
        address = await self.repository.find_by_id(address_id)
        if not address:
            raise AppException(404, "Address not found")
        return self._serialize_address(address)

    async def update_address(self, address_id: str, update_data: dict):
        if not update_data:
            raise AppException(400, "No fields provided for update")

        self.timestamps(update_data)
        result = await self.repository.update_by_id(address_id, update_data)

        if result.matched_count == 0:
            raise AppException(404, "Address not found")

        return await self.get_address_by_id(address_id)

    async def delete_by_company_id(self, company_id: str):
        await self.repository.delete_by_company_id(company_id)
