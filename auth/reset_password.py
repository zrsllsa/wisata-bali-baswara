from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from supabase_client import (
    supabase,
    SUPABASE_URL,
    SUPABASE_KEY
)

from supabase import create_client


router = APIRouter(
    prefix="/api/auth",
    tags=["Authentication"]
)


class ResetPasswordRequest(BaseModel):
    access_token: str
    new_password: str


@router.post("/reset-password")
def reset_password(
    data: ResetPasswordRequest
):

    try:

        result = supabase.auth.get_user(
            data.access_token
        )

        if not result or not result.user:

            raise HTTPException(
                status_code=401,
                detail=(
                    "Token reset password "
                    "tidak valid atau sudah expired."
                )
            )

        recovery_client = create_client(
            SUPABASE_URL,
            SUPABASE_KEY
        )

        recovery_client.auth.update_user({
            "password": data.new_password
        })

        return {
            "message": "Password berhasil diubah."
        }

    except HTTPException:
        raise

    except Exception as e:

        raise HTTPException(
            status_code=400,
            detail=(
                f"Reset password gagal: {str(e)}"
            )
        )