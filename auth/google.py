import os
from urllib.parse import urlencode

from dotenv import load_dotenv
from fastapi import APIRouter, HTTPException
from fastapi.responses import RedirectResponse
from supabase_client import supabase

load_dotenv()

router = APIRouter(prefix="/api/auth", tags=["Authentication"])

FRONTEND_URL = os.getenv("FRONTEND_URL", "http://localhost:5173").rstrip("/")
BACKEND_URL = os.getenv("BACKEND_URL", "http://localhost:8000").rstrip("/")


@router.get("/google")
def google_login():
    
    try:

        result = supabase.auth.sign_in_with_oauth({
            "provider": "google",
            "options": {
                "redirect_to": f"{BACKEND_URL}/api/auth/google/callback"
            },
        })

        if not result.url:
            raise HTTPException(
                status_code=400,
                detail="URL login Google tidak berhasil dibuat",
            )

        return {"url": result.url}

    except HTTPException:
        raise
    except Exception as e:
        print("ERROR GOOGLE LOGIN:", repr(e))
        raise HTTPException(status_code=400, detail=f"Login Google gagal: {e}")


@router.get("/google/callback")
def google_callback(code: str | None = None, error: str | None = None):
    print("GOOGLE CALLBACK DIPANGGIL, code ada:", bool(code), "error:", error)

    if error or not code:
        return RedirectResponse(
            url=f"{FRONTEND_URL}/#error=Login%20Google%20gagal",
            status_code=302,
        )

    try:
        result = supabase.auth.exchange_code_for_session({"auth_code": code})

        if not result.user or not result.session:
            raise HTTPException(status_code=401, detail="Login Google gagal")

        user = result.user
        session = result.session
        metadata = user.user_metadata or {}

        params = urlencode({
            "access_token": session.access_token,
            "refresh_token": session.refresh_token or "",
            "email": user.email or "",
            "name": metadata.get("full_name") or metadata.get("name") or "",
            "picture": metadata.get("avatar_url") or metadata.get("picture") or "",
        })

        return RedirectResponse(url=f"{FRONTEND_URL}/#{params}", status_code=302)

    except Exception as e:
        print("ERROR GOOGLE CALLBACK:", repr(e))
        return RedirectResponse(
            url=f"{FRONTEND_URL}/#error=Login%20Google%20gagal",
            status_code=302,
        )