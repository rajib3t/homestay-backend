from app.core.exceptions import AppException

from app.services.storage_service import StorageService

from app.domain.events.user_events import UserUpdatedEvent
class UpdateUserUseCase:

    def __init__(
        self,
        user_service,
        company_service,
        address_service,
        storage_service,
        uow,
    ):
        self.user_service = user_service
        self.company_service = company_service
        self.address_service = address_service
        self.storage_service = storage_service
        self.uow = uow

    async def execute(self, user_id: str, payload: dict) -> dict:
        actor_id = payload.get("updated_by")

        payload = payload.copy()
        company_data = payload.get("company")

        async with self.uow as uow:
            session = uow.get_session()

            # --- STEP 1: Update User ---
            await self.user_service.update_user(
                user_id,
                {k: v for k, v in payload.items() if k != "company"},
                session=session
            )

            # --- STEP 2: Company + Address ---
            if company_data is not None:
                company_data = company_data.copy()
                address_data = company_data.pop("address", None)

                company_id = await self._upsert_company(
                    user_id, company_data, actor_id, session
                )

                if address_data and company_id:
                    await self._upsert_address(
                        company_id, user_id, address_data, actor_id, session
                    )

            # --- STEP 3: Emit Event (AFTER SUCCESS) ---
            uow.collect_event(UserUpdatedEvent(user_id, actor_id))
            
        # --- STEP 4: Build Response (OUTSIDE TX) ---
        return await self._build_user_response(user_id)
    
    async def _upsert_company(self, user_id, data, actor_id, session):

        try:
            company = await self.company_service.get_company_by_user_id(
                user_id, include_address=False
            )
            company_id = company["id"]

            if data:
                await self.company_service.update_company(
                    company_id,
                    {**data, "updated_by": actor_id},
                    session=session
                )

            return company_id

        except AppException:
            if not data:
                return None

            return await self.company_service.create_company(
                {**data, "user_id": user_id, "created_by": actor_id},
                session=session
            )
    async def _upsert_address(self, company_id, user_id, data, actor_id, session):

        if not company_id:
            company = await self.company_service.get_company_by_user_id(
                user_id, include_address=False
            )
            company_id = company["id"]

        address = await self.address_service.get_address_by_company_id(company_id)

        if address:
            await self.address_service.update_address(
                address["id"],
                {**data, "updated_by": actor_id},
                session=session
            )
        else:
            await self.address_service.create_address(
                {
                    **data,
                    "company_id": company_id,
                    "user_id": user_id,
                    "created_by": actor_id,
                },
                session=session
            )

    async def _build_user_response(self, user_id: str) -> dict:
        # Fetch updated user
        user = await self.user_service.get_user(user_id)
        if not user:
            raise AppException(404, "User not found")

        # Resolve image URL if present
        if user.get("image"):
            user["image"] = self.storage_service.generate_presigned_url(user["image"])

        # Fetch company and address if exists
        try:
            company = await self.company_service.get_company_by_user_id(user_id)
            if company:
                company = company.copy()
                if "_id" in company:
                    company["id"] = str(company.pop("_id"))

                try:
                    address = await self.address_service.get_address_by_company_id(company["id"])
                    if address:
                        address = address.copy()
                        if "_id" in address:
                            address["id"] = str(address.pop("_id"))
                        address.pop("company_id", None)
                        address.pop("user_id", None)
                        company["address"] = address
                except Exception:
                    pass

                user["company"] = company
        except Exception:
            pass

        return user