
from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    status
)

from fastapi.security import (
    HTTPBearer,
    HTTPAuthorizationCredentials
)

from supabase_client import (
    supabase,
    get_supabase_admin
)


router = APIRouter(
    prefix="/api/auth",
    tags=["Authentication"]
)

security = HTTPBearer()


@router.delete("/delete-account")
def delete_account(
    credentials: HTTPAuthorizationCredentials = Depends(security)
):

    try:

        # =========================================================
        # 1. AMBIL ACCESS TOKEN
        # =========================================================

        token = credentials.credentials

        if not token:

            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Access token tidak ditemukan."
            )

        # =========================================================
        # 2. VALIDASI TOKEN & AMBIL USER
        # =========================================================

        result = supabase.auth.get_user(token)

        if not result or not result.user:

            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token tidak valid atau sudah kedaluwarsa."
            )

        user = result.user

        user_id = user.id
        user_email = user.email

        print("======================================")
        print("DELETE ACCOUNT")
        print("USER ID:", user_id)
        print("EMAIL:", user_email)
        print("======================================")

        # =========================================================
        # 3. AMBIL SUPABASE ADMIN CLIENT
        # =========================================================

        supabase_admin = get_supabase_admin()

        # =========================================================
        # 4. HAPUS USER DARI SUPABASE AUTH
        # =========================================================

        delete_result = (
            supabase_admin
            .auth
            .admin
            .delete_user(user_id)
        )

        print(
            "SUPABASE DELETE RESULT:",
            delete_result
        )

        # =========================================================
        # 5. HAPUS DATA PROFILES
        # =========================================================

        try:

            (
                supabase_admin
                .table("profiles")
                .delete()
                .eq("id", user_id)
                .execute()
            )

            print(
                "Profile berhasil dihapus."
            )

        except Exception as profile_error:

            print(
                "PROFILE DELETE ERROR:",
                repr(profile_error)
            )

        # =========================================================
        # 6. HAPUS DATA PENDING REGISTRATION
        # =========================================================

        if user_email:

            try:

                (
                    supabase_admin
                    .table("pending_registrations")
                    .delete()
                    .eq("email", user_email)
                    .execute()
                )

                print(
                    "Pending registration berhasil dihapus."
                )

            except Exception as pending_error:

                print(
                    "PENDING DELETE ERROR:",
                    repr(pending_error)
                )

        # =========================================================
        # 7. RESPONSE BERHASIL
        # =========================================================

        return {

            "success": True,

            "message": "Akun berhasil dihapus.",

            "user_id": user_id,

            "email": user_email
        }

    # =============================================================
    # HTTP ERROR
    # =============================================================

    except HTTPException:

        raise

    # =============================================================
    # ERROR LAINNYA
    # =============================================================

    except Exception as e:

        print("======================================")
        print("ERROR DELETE ACCOUNT")
        print(repr(e))
        print("======================================")

        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Gagal menghapus akun: {str(e)}"
        )
