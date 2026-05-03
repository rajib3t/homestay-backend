# app/application/use_cases/create_user.py

from app.domain.events.user_events import UserCreatedEvent

class CreateUserUseCase:

    def __init__(self, user_service, event_bus):
        self.user_service = user_service
        self.event_bus = event_bus

    async def execute(self, data: dict):
        user_id = await self.user_service.create_user(data)
        user = await self.user_service.get_user(user_id)
        if not user:
            raise ValueError("User creation failed")
        
        await self.event_bus.publish(UserCreatedEvent(user))

        return user