from fastapi import Depends, HTTPException
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

from supabase_client import supabase


security = HTTPBearer()


def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security)
):

    token = credentials.credentials

    try:

        result = supabase.auth.get_user(token)

        if not result or not result.user:
            raise HTTPException(
                status_code=401,
                detail="Invalid or expired token"
            )

        return result.user

    except HTTPException:
        raise

    except Exception:

        raise HTTPException(
            status_code=401,
            detail="Invalid or expired token"
        )