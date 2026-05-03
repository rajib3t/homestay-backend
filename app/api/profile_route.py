from fastapi import APIRouter, Depends
from app.schemas.user_schema import ProfileResponse
from app.models.user_model import UserUpdate
from app.services.user_service import UserService
from app.deps import get_user_service, get_current_user
from app.deps.auth import CurrentUser

router = APIRouter(prefix="/profile", tags=["Profile"])

@router.get("", response_model=ProfileResponse, response_model_by_alias=False)
async def get_profile(
    current_user: CurrentUser = Depends(get_current_user),
    user_service: UserService = Depends(get_user_service),
):
    user = await user_service.get_user(current_user.id)
    return {
        "status": "success",
        "message": "Profile data retrieved",
        "data": user,
    }

@router.put("", response_model=ProfileResponse, response_model_by_alias=False)
async def update_profile(
    current_user: CurrentUser = Depends(get_current_user),
    update_data: UserUpdate = ..., 
    user_service: UserService = Depends(get_user_service),
):
    # Filter out None values to avoid overwriting with nulls
    data = update_data.model_dump(exclude_unset=True)

    updated_user = await user_service.update_user(current_user.id, data)
    return {
        "status": "success",
        "message": "Profile updated successfully",
        "data": updated_user,
    }
