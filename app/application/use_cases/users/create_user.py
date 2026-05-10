from app.domain.events.user_events import UserCreatedEvent
from app.core.exceptions import AppException


class CreateUserUseCase:

    def __init__(self, user_service, uow):
        self.user_service = user_service
        self.uow = uow

    async def execute(self, data: dict):

        async with self.uow as uow:
            session = uow.get_session()

            # --- STEP 1: CREATE USER ---
            user_id = await self.user_service.create_user(
                data,
                session=session
            )

            # --- STEP 2: FETCH USER INSIDE TX ---
            user = await self.user_service.get_user(
                user_id,
                session=session
            )

            if not user:
                raise AppException(500, "User creation failed")

            # --- STEP 3: COLLECT EVENT ---
            uow.collect_event(
                UserCreatedEvent(
                    user_id=user["id"],
                    email=user["email"],
                    username=user["username"],
                )
            )

        # --- STEP 4: RETURN RESPONSE ---
        return user