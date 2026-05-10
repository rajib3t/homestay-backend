from fastapi import Depends
from app.infrastructure.uow.mongo_uow import MongoUnitOfWork
from app.core.database import get_database, get_client


def get_uow(
    db=Depends(get_database),
    client=Depends(get_client),
):
    return MongoUnitOfWork(db=db, client=client)