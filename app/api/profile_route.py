from fastapi import APIRouter, Depends
from app.application.use_cases.users.user import GetUserUseCase
from app.deps.user_use import get_single_user_use_case
from app.schemas.user_schema import ProfileResponse
from app.models.user_model import UserUpdate
from app.services.user_service import UserService
from app.services.storage_service import StorageService
from app.deps import get_user_service, get_current_user, get_storage_service
from app.deps.auth import CurrentUser

router = APIRouter(prefix="/profile", tags=["Profile"])

@router.get("", response_model=ProfileResponse, response_model_by_alias=False)
async def get_profile(
    current_user: CurrentUser = Depends(get_current_user),
    
    use_case: GetUserUseCase = Depends(get_single_user_use_case)
):
    user = await use_case.execute(current_user.id)
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
    storage_service: StorageService = Depends(get_storage_service),
):
    # Filter out None values to avoid overwriting with nulls
    data = update_data.model_dump(exclude_unset=True)

    await user_service.update_user(current_user.id, data)
    updated_user = await user_service.get_user(current_user.id, storage=storage_service)
    return {
        "status": "success",
        "message": "Profile updated successfully",
        "data": updated_user,
    }
