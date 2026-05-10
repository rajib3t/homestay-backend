# app/repositories/outbox_repository.py

from datetime import datetime


class OutboxRepository:

    def __init__(self, db):

        self.collection = db.outbox

    async def create(self, event, session=None):

        await self.collection.insert_one(
            event.to_dict(),
            session=session
        )

    async def get_unprocessed_events(self):

        cursor = self.collection.find({
            "processed": "pending"
        })

        return await cursor.to_list(length=100)

    async def mark_processed(self, event_id):

        await self.collection.update_one(
            {"_id": event_id},
            {
                "$set": {
                    "processed": "processed",
                    "processed_at": datetime.utcnow()
                }
            }
        )