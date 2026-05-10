# app/infrastructure/uow/mongo_uow.py

from app.repositories.outbox_repository import (
    OutboxRepository
)


class MongoUnitOfWork:

    def __init__(self, db, client):

        self.db = db

        self.client = client

        self.outbox = OutboxRepository(db)

        self._events = []

    async def __aenter__(self):

        self.session = await self.client.start_session()

        self.session.start_transaction()

        return self

    async def __aexit__(self, exc_type, exc, tb):

        try:

            if exc:

                await self.session.abort_transaction()

            else:

                # -----------------------------------
                # SAVE EVENTS TO OUTBOX
                # -----------------------------------

                for event in self._events:

                    await self.outbox.create(
                        event,
                        session=self.session
                    )

                # -----------------------------------
                # COMMIT TRANSACTION
                # -----------------------------------

                await self.session.commit_transaction()

        finally:

            await self.session.end_session()

    def get_session(self):

        return self.session

    def collect_event(self, event):

        self._events.append(event)