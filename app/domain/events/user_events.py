# app/domain/events/user_events.py

class UserCreatedEvent:
    def __init__(self, user: dict):
        self.user = user


class UserGetEvent:
    def __init__(self, user: dict):
        self.user = user