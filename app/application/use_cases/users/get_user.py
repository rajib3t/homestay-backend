# app/application/use_cases/get_user.py

from app.core.exceptions import AppException


class GetUserUseCase:
    def __init__(
        self,
        user_service,
        company_service,
        address_service,
        storage_service,
    ):
        self.user_service = user_service
        self.company_service = company_service
        self.address_service = address_service
        self.storage_service = storage_service

    async def execute(self, user_id: str, include_company: bool = False) -> dict:
        # 1. Fetch user (core entity)
        user = await self.user_service.get_user(user_id)

        if not user:
            raise AppException(404, "User not found")

        # 2. Resolve image (external concern)
        if user.get("image"):
            user["image"] = self.storage_service.generate_presigned_url(
                user["image"]
            )

        # 3. Fetch company (optional aggregate) - only if requested
        if include_company:
            try:
                company = await self.company_service.get_company_by_user_id(user_id)

                if company:
                    company = company.copy()

                    # normalize id
                    if "_id" in company:
                        company["id"] = str(company.pop("_id"))

                    # 4. Fetch address (depends on company)
                    try:
                        address = await self.address_service.get_address_by_company_id(
                            company["id"]
                        )

                        if address:
                            address = address.copy()

                            if "_id" in address:
                                address["id"] = str(address.pop("_id"))

                            address.pop("company_id", None)
                            address.pop("user_id", None)

                            company["address"] = address
                    except Exception:
                        # Address not found or error - continue without address
                        pass

                    user["company"] = company
            except Exception:
                # Company not found or error - continue without company
                pass

        return user