from app.domain.events.base_event import BaseEvent


class UserCreatedEvent(BaseEvent):

    def __init__(
        self,
        user_id: str,
        email: str,
        username: str,
    ):
        super().__init__(
            aggregate_id=user_id,
            event_type="USER_CREATED",
            payload={
                "user_id": user_id,
                "email": email,
                "username": username,
            },
        )


class UserUpdatedEvent(BaseEvent):
    def __init__(self, user_id: str, updated_by: str):
        super().__init__(
            aggregate_id=user_id,
            event_type="USER_UPDATED",
            payload={
                "user_id": user_id,
                "updated_by": updated_by,
            },
        )