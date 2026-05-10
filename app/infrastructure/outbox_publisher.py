class OutboxPublisher:
    def __init__(self, outbox_repo, event_bus):
        self.outbox_repo = outbox_repo
        self.event_bus = event_bus

    async def publish_pending(self):
        events = await self.outbox_repo.get_unprocessed_events()

        for event in events:
            try:
                await self.event_bus.publish(
                    event["event_type"],
                    event["payload"]
                )

                await self.outbox_repo.mark_processed(event["_id"])

            except Exception as e:
                # log and retry later
                print(f"Failed to publish event {event['_id']}: {e}")