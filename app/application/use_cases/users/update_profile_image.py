# app/application/use_cases/users/update_profile_image.py

from app.services.user_service import UserService
from app.services.storage_service import StorageService
from app.utils.api_utils import replace_data_url_asset
from fastapi import HTTPException, status


class UpdateUserProfileImageUseCase:
    def __init__(self, user_service: UserService, storage_service: StorageService):
        self.user_service = user_service
        self.storage_service = storage_service

    async def execute(self, user_id: str, image: str):
        if not image:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Image file is required"
            )

        user = await self.user_service.get_user(user_id)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )

        old_image = user.get("image")

        # Transform if needed
        if isinstance(image, str) and image.startswith("data:"):
            image = await replace_data_url_asset(
                self.storage_service,
                image,
                "profile_images",
                user_id,
                old_key=old_image
            )

        await self.user_service.update_user(user_id, {"image": image})

        return await self.user_service.get_user(
            user_id,
            storage=self.storage_service
        )