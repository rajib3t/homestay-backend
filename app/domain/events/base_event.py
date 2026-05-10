from datetime import datetime
from uuid import uuid4


class BaseEvent:
    def __init__(self, aggregate_id: str, event_type: str, payload: dict):
        self.id = str(uuid4())
        self.aggregate_id = aggregate_id
        self.event_type = event_type
        self.payload = payload
        self.created_at = datetime.utcnow()
        self.processed = 'pending'

    def to_dict(self):
        return {
            "id": self.id,
            "aggregate_id": self.aggregate_id,
            "event_type": self.event_type,
            "payload": self.payload,
            "created_at": self.created_at.isoformat(),
            "processed": self.processed,
        }