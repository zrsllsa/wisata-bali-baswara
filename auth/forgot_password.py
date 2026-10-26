from fastapi import APIRouter
from pydantic import BaseModel, EmailStr

from supabase_client import supabase


router = APIRouter(
    prefix="/api/auth",
    tags=["Authentication"]
)


class ForgotPasswordRequest(BaseModel):
    email: EmailStr


@router.post("/forgot-password")
def forgot_password(
    data: ForgotPasswordRequest
):

    try:

        supabase.auth.reset_password_for_email(
            str(data.email),
            {
                "redirect_to": (
                    "https://"
                    "bauble-clergyman-glisten"
                    ".ngrok-free.dev"
                    "/api/auth/reset-password"
                )
            }
        )

    except Exception as e:

        print(
            "ERROR FORGOT PASSWORD:",
            repr(e)
        )

    return {
        "message": (
            "Jika email terdaftar, "
            "link reset password telah dikirim."
        )
    }