import os

from dotenv import load_dotenv
from supabase import create_client
from supabase.client import ClientOptions


load_dotenv()


# =========================================================
# ENVIRONMENT
# =========================================================

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")
SUPABASE_SERVICE_ROLE_KEY = os.getenv(
    "SUPABASE_SERVICE_ROLE_KEY"
)


# =========================================================
# VALIDASI ENV
# =========================================================

if not SUPABASE_URL:
    raise Exception(
        "SUPABASE_URL tidak ditemukan di .env"
    )


if not SUPABASE_KEY:
    raise Exception(
        "SUPABASE_KEY tidak ditemukan di .env"
    )


if not SUPABASE_SERVICE_ROLE_KEY:
    raise Exception(
        "SUPABASE_SERVICE_ROLE_KEY tidak ditemukan di .env"
    )


# =========================================================
# CLIENT BIASA
# =========================================================

supabase = create_client(
    SUPABASE_URL,
    SUPABASE_KEY
)


# =========================================================
# ADMIN CLIENT
# =========================================================

def get_supabase_admin():

    options = ClientOptions(
        auto_refresh_token=False,
        persist_session=False
    )

    return create_client(
        SUPABASE_URL,
        SUPABASE_SERVICE_ROLE_KEY,
        options=options
    )