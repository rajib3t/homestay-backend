from datetime import datetime
from typing import Optional

from app.services.base_service import BaseService
from app.core.exceptions import AppException
from app.repositories.company_repository import CompanyRepository
from app.repositories.address_repository import AddressRepository
from pymongo.errors import DuplicateKeyError


class CompanyService(BaseService):
    def __init__(self, repository: CompanyRepository, address_repository: Optional[AddressRepository] = None):
        super().__init__(repository.db)
        self.repository = repository
        self.address_repository = address_repository

    @staticmethod
    def _serialize_company(company: dict):
        company = company.copy()
        company["id"] = str(company.pop("_id"))

        if company.get("created_at") and isinstance(company.get("created_at"), datetime):
            company["created_at"] = company["created_at"].isoformat()

        if company.get("updated_at") and isinstance(company.get("updated_at"), datetime):
            company["updated_at"] = company["updated_at"].isoformat()

        return company

    async def create_company(self, company_data: dict):
        # Check if company with this email already exists
        existing = await self.repository.find_by_email(company_data["email"])
        if existing:
            raise AppException(
                status_code=409,
                message="Company with this email already exists",
                error_code="COMPANY_EMAIL_EXISTS",
                field="email"
            )

        # Check if user already has a company
        existing_by_user = await self.repository.find_by_user_id(company_data["user_id"])
        if existing_by_user:
            raise AppException(
                status_code=409,
                message="User already has a company",
                error_code="USER_COMPANY_EXISTS",
                field="user_id"
            )

        # Extract address data if provided
        address_data = company_data.pop("address", None)

        try:
            self.timestamps(company_data, is_new=True)
            result = await self.repository.insert(company_data)
            company_id = str(result.inserted_id)

            # Create address if provided
            if address_data and self.address_repository:
                address_data["company_id"] = company_id
                self.timestamps(address_data, is_new=True)
                await self.address_repository.insert(address_data)

            return company_id
        except DuplicateKeyError as e:
            error_msg = str(e)

            if "email" in error_msg:
                raise AppException(
                    status_code=409,
                    message="Company with this email already exists",
                    error_code="COMPANY_EMAIL_EXISTS",
                    field="email"
                )

            raise

    async def get_company(self, company_id: str, include_address: bool = True):
        company = await self.repository.find_by_id(company_id)
        if not company:
            raise AppException(404, "Company not found")

        serialized = self._serialize_company(company)

        # Fetch and include address if requested
        if include_address and self.address_repository:
            address = await self.address_repository.find_by_company_id(company_id)
            if address:
                address = address.copy()
                address["id"] = str(address.pop("_id"))
                address.pop("company_id", None)
                address.pop("user_id", None)
                serialized["address"] = address

        return serialized

    async def get_company_by_user_id(self, user_id: str, include_address: bool = True):
        company = await self.repository.find_by_user_id(user_id)
        if not company:
            raise AppException(404, "Company not found for this user")

        serialized = self._serialize_company(company)
        company_id = serialized["id"]

        # Fetch and include address if requested
        if include_address and self.address_repository:
            address = await self.address_repository.find_by_company_id(company_id)
            if address:
                address = address.copy()
                address["id"] = str(address.pop("_id"))
                address.pop("company_id", None)
                address.pop("user_id", None)
                serialized["address"] = address

        return serialized

    async def update_company(self, company_id: str, update_data: dict):
        if not update_data:
            raise AppException(400, "No fields provided for update")

        # Check if email is being updated and if it's already taken
        if "email" in update_data:
            existing = await self.repository.find_by_email(update_data["email"])
            if existing and str(existing["_id"]) != company_id:
                raise AppException(409, "Email already exists")

        self.timestamps(update_data)
        result = await self.repository.update_by_id(company_id, update_data)

        if result.matched_count == 0:
            raise AppException(404, "Company not found")

        return await self.get_company(company_id)
