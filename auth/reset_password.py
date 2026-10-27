from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from supabase_client import (
    supabase,
    get_supabase_admin
)


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

        # =================================================
        # 1. VALIDASI ACCESS TOKEN
        # =================================================

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


        user_id = result.user.id

        print("====================================")
        print("🔐 RESET PASSWORD")
        print("USER ID:", user_id)
        print("EMAIL:", result.user.email)
        print("====================================")


        # =================================================
        # 2. VALIDASI PASSWORD BARU
        # =================================================

        if len(data.new_password) < 8:

            raise HTTPException(
                status_code=400,
                detail="Password minimal 8 karakter."
            )


        # =================================================
        # 3. AMBIL ADMIN CLIENT
        # =================================================

        admin = get_supabase_admin()


        # =================================================
        # 4. UPDATE PASSWORD USER
        # =================================================

        admin.auth.admin.update_user_by_id(
            user_id,
            {
                "password": data.new_password
            }
        )


        print(
            "✅ PASSWORD BERHASIL DIUBAH"
        )


        # =================================================
        # 5. RESPONSE
        # =================================================

        return {
            "success": True,
            "message": "Password berhasil diubah."
        }


    except HTTPException:

        raise


    except Exception as e:

        print(
            "❌ ERROR RESET PASSWORD:",
            repr(e)
        )

        raise HTTPException(
            status_code=400,
            detail=(
                f"Reset password gagal: {str(e)}"
            )
        )