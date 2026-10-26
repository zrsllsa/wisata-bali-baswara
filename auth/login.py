from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, EmailStr

from supabase_client import supabase


router = APIRouter(
    prefix="/api/auth",
    tags=["Authentication"]
)


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


@router.post("/login")
def login(data: LoginRequest):

    try:
        email = str(data.email).lower().strip()

        print("====================================")
        print("🔐 LOGIN")
        print("EMAIL:", email)
        print("====================================")

        auth_result = supabase.auth.sign_in_with_password({
            "email": email,
            "password": data.password
        })

        print("AUTH USER:", auth_result.user)
        print("AUTH SESSION:", auth_result.session)

        if not auth_result.user:
            raise HTTPException(
                status_code=401,
                detail="Email atau password salah."
            )

        user = auth_result.user

        return {
            "message": "Login berhasil!",
            "user_id": user.id,
            "name": user.user_metadata.get("full_name"),
            "email": user.email,
            "token_type": "bearer",
            "access_token": (
                auth_result.session.access_token
                if auth_result.session
                else None
            )
        }

    except HTTPException:
        raise

    except Exception as e:

        print("====================================")
        print("❌ ERROR LOGIN")
        print("ERROR:", repr(e))
        print("====================================")

        raise HTTPException(
            status_code=401,
            detail=f"Email atau password salah: {str(e)}"
        )