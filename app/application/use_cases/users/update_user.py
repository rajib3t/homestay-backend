
from app.core.exceptions import AppException


class UpdateUserUseCase:

    def __init__(self, user_service, company_service, address_service):
        self.user_service = user_service
        self.company_service = company_service
        self.address_service = address_service

    async def execute(self, user_id, payload):
        company_data = payload.pop("company", None)

        # Update user data
        await self.user_service.update_user(user_id, payload)

        if company_data is not None:
            address_data = company_data.pop("address", None)
            company_id = None

            try:
                company = await self.company_service.get_company_by_user_id(user_id, include_address=False)
                company_id = company["id"]
                if company_data:
                    await self.company_service.update_company(company_id, company_data)
            except AppException:
                if company_data:
                    company_data["user_id"] = user_id
                    company_id = await self.company_service.create_company(company_data)
                else:
                    company_id = None

            if address_data:
                if not company_id:
                    try:
                        company = await self.company_service.get_company_by_user_id(user_id, include_address=False)
                        company_id = company["id"]
                    except AppException:
                        raise AppException(400, "Company is required to update address")

                address = await self.address_service.get_address_by_company_id(company_id)
                if address:
                    await self.address_service.update_address(address["id"], address_data)
                else:
                    address_data["company_id"] = company_id
                    address_data["user_id"] = user_id
                    await self.address_service.create_address(address_data)

        # Return user with company data if present
        user = await self.user_service.get_user(user_id)
        try:
            company = await self.company_service.get_company_by_user_id(user_id)
            if company:
                user["company"] = company
        except AppException:
            pass

        return user