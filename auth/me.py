from fastapi import APIRouter, Depends

from auth.dependencies import get_current_user


router = APIRouter(
    prefix="/api/auth",
    tags=["Authentication"]
)


@router.get("/me")
def get_me(
    user=Depends(get_current_user)
):

    return {
        "user_id": user.id,
        "email": user.email,
        "name": user.user_metadata.get("full_name"),
        "avatar_url": user.user_metadata.get("avatar_url"),
        "provider": user.app_metadata.get("provider")
    }