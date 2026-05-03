# app/infrastructure/event_bus/event_bus.py

class EventBus:
    def __init__(self):
        self.handlers = {}

    def register(self, event_type, handler):
        self.handlers.setdefault(event_type, []).append(handler)

    async def publish(self, event):
        for handler in self.handlers.get(type(event), []):
            await handler(event)