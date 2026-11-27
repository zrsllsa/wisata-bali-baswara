import os

import httpx
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

def _buat_client(key: str):

    options = ClientOptions(
        auto_refresh_token=False,
        persist_session=False,
        # HTTP/1.1: koneksi HTTP/2 bawaan supabase-py rusak kalau dipakai banyak thread sekaligus
        httpx_client=httpx.Client(http2=False, timeout=30, follow_redirects=True)
    )

    return create_client(
        SUPABASE_URL,
        key,
        options=options
    )


# Untuk data saja. JANGAN dipakai sign-in: sesi user akan menimpa key client ini.
supabase = _buat_client(SUPABASE_KEY)


# =========================================================
# CLIENT AUTH (untuk sign-in, sesi tidak bocor ke client data)
# =========================================================

def get_supabase_auth():

    return _buat_client(SUPABASE_KEY)


# =========================================================
# ADMIN CLIENT
# =========================================================

def get_supabase_admin():

    return _buat_client(SUPABASE_SERVICE_ROLE_KEY)