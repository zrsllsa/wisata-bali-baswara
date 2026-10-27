from fastapi import APIRouter, HTTPException
from supabase_client import supabase


router = APIRouter(
    prefix="/api/auth",
    tags=["Authentication"]
)


# =========================================================
# LOGIN GOOGLE
# =========================================================

@router.get("/google")
def google_login():

    try:

        result = supabase.auth.sign_in_with_oauth({
            "provider": "google",
            "options": {
                "redirect_to": (
                    "http://127.0.0.1:8000"
                    "/api/auth/google/callback"
                )
            }
        })

        return {
            "url": result.url
        }

    except Exception as e:

        raise HTTPException(
            status_code=400,
            detail=f"Login Google gagal: {str(e)}"
        )


# =========================================================
# GOOGLE CALLBACK
# =========================================================

@router.get("/google/callback")
def google_callback(code: str):

    try:

        result = supabase.auth.exchange_code_for_session({
            "auth_code": code
        })

        if not result.user or not result.session:

            raise HTTPException(
                status_code=401,
                detail="Login Google gagal"
            )

        return {
            "message": "Login Google berhasil!",
            "user_id": result.user.id,
            "email": result.user.email,
            "access_token": result.session.access_token,
            "refresh_token": result.session.refresh_token,
            "token_type": "bearer"
        }

    except HTTPException:
        raise

    except Exception as e:

        raise HTTPException(
            status_code=401,
            detail=f"Login Google gagal: {str(e)}"
        )