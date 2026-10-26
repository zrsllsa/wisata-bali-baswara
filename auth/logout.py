from fastapi import APIRouter, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

from supabase_client import supabase


router = APIRouter(
    prefix="/api/auth",
    tags=["Authentication"]
)

security = HTTPBearer()


@router.post("/logout")
def logout(
    credentials: HTTPAuthorizationCredentials = Depends(security)
):

    token = credentials.credentials

    try:

        result = supabase.auth.get_user(token)

        if not result or not result.user:
            return {
                "message": "Logout berhasil!"
            }

        return {
            "message": "Logout berhasil!",
            "user_id": result.user.id
        }
 
    except Exception as e:

        raise Exception(
            f"Logout gagal: {str(e)}"
        )