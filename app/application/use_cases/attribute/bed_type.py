from bson import ObjectId

from app.application.dto.bed_type import BedTypeQuery
from app.models.attribute_model import CreateRoomType, UpdateRoomType


class CreateBedTypeUseCase:
    def __init__(self, 
        attribute_service,
        current_user,
        uow,
        ):
        self.attribute_service = attribute_service
        self.current_user = current_user
        self.uow = uow

    async def execute(self, payload: CreateRoomType):
        created_payload = payload.model_dump()
        created_payload["created_by"] = ObjectId(str(self.current_user.id))
        
        async with self.uow as uow:
            session = uow.get_session()
            bed_type = await self.attribute_service.create_room_type(created_payload, session)
            return bed_type
        


class GetBedTypesUseCase:

    def __init__(
        self,
        attribute_service,
        current_user,
        uow,
    ):
        self.attribute_service = attribute_service
        self.current_user = current_user
        self.uow = uow

    async def execute(
            self,
               query: BedTypeQuery
        ):
         async with self.uow as uow:
            session = uow.get_session()

            result = await self.attribute_service.list_room_types(
                query=query,
                session=session
            )
            return result
    


class GetBedTypeUseCase:

    def __init__(
        self,
        attribute_service,
        current_user,
        uow,
    ):
        self.attribute_service = attribute_service
        self.current_user = current_user
        self.uow = uow

    async def execute(
            self,
            bed_type_id: str
        ):
         async with self.uow as uow:
            session = uow.get_session()
            bed_type = await self.attribute_service.get_room_type(
                room_type_id=bed_type_id,
                session=session
            )
            return bed_type
         

class UpdateBedTypeUseCase:

    def __init__(
        self,
        attribute_service,
        current_user,
        uow,
    ):
        self.attribute_service = attribute_service
        self.current_user = current_user
        self.uow = uow

    async def execute(
            self,
            bed_type_id: str,
            payload: UpdateRoomType
        ):
         async with self.uow as uow:
            session = uow.get_session()
            updated_payload = payload.model_dump(exclude_unset=True)
            updated_payload["updated_by"] = ObjectId(str(self.current_user.id))
            bed_type = await self.attribute_service.update_room_type(
                room_type_id=bed_type_id,
                data=updated_payload,
                session=session
            )
            return bed_type