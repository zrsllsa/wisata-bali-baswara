
import os
from fastapi import FastAPI, Query, HTTPException
from dotenv import load_dotenv
from supabase import create_client, Client

load_dotenv()
print("URL terbaca:", bool(os.getenv("SUPABASE_URL")))
print("KEY terbaca:", bool(os.getenv("SUPABASE_KEY")))
print("Awalan KEY:", (os.getenv("SUPABASE_KEY") or "")[:15])

app = FastAPI()

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

if not SUPABASE_URL or not SUPABASE_KEY:
    raise ValueError("SUPABASE_URL atau SUPABASE_KEY belum diatur di file .env")

supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)


@app.get("/")
def home():
    return {"message": "Backend Wisata Bali berhasil!"}


@app.get("/api/test-supabase")
def test_supabase():
    try:
        result = (
            supabase.table("Wisata-bali")
            .select("*", count="exact")
            .limit(1)
            .execute()
        )
        return {
            "message": "Koneksi Supabase berhasil!",
            "jumlah_data_ditemukan": result.count,
            "contoh_data": result.data,
        }
    except Exception as e:
        return {
            "message": "Koneksi atau pembacaan tabel gagal.",
            "detail": str(e),
        }



@app.get("/api/wisata")
def daftar_wisata():
    result = (
        supabase.table("Wisata-bali")
        .select("id,nama,kategori,kabupaten_kota,rating,preferensi,link,latitude,longitude")
        .execute()
    )

    return {
        "jumlah": len(result.data),
        "data": result.data
    }



from fastapi import Query

@app.get("/api/wisata/filter")
def filter_wisata(
    kategori: str | None = Query(default=None),
    kabupaten_kota: str | None = Query(default=None),
):
    query = supabase.table("Wisata-bali").select(
        "id,nama,kategori,kabupaten_kota,rating,preferensi,link,latitude,longitude"
    )

    if kategori:
        query = query.eq("kategori", kategori)

    if kabupaten_kota:
        query = query.eq("kabupaten_kota", kabupaten_kota)

    result = query.execute()

    return {
        "jumlah": len(result.data),
        "data": result.data
    }



from fastapi import HTTPException

@app.get("/api/wisata/{wisata_id}")
def detail_wisata(wisata_id: int):
    result = (
        supabase.table("Wisata-bali")
        .select("*")
        .eq("id", wisata_id)
        .limit(1)
        .execute()
    )

    if not result.data:
        raise HTTPException(
            status_code=404,
            detail="Wisata tidak ditemukan"
        )

    return result.data[0]



from pydantic import BaseModel, EmailStr
from fastapi import HTTPException

class RegisterRequest(BaseModel):
    email: EmailStr
    password: str


@app.post("/api/auth/register")
def register(data: RegisterRequest):
    try:
        
        result = supabase.auth.sign_up({
            "email": str(data.email),
            "password": data.password,
            "options": {
                "email_redirect_to": "https://langkah-baswara-progress1.vercel.app/"
            }
        })

        user = result.user

        if not user:
            raise HTTPException(
                status_code=400,
                detail="Register gagal"
            )

        return {
            "message": "Register berhasil diproses. Periksa email jika konfirmasi diperlukan.",
            "user_id": user.id,
            "email": user.email
        }

    except HTTPException:
        raise
    except Exception:
        raise HTTPException(
            status_code=400,
            detail="Register gagal. Periksa email, password, atau konfigurasi Supabase."
        )



class LoginRequest(BaseModel):
    email: EmailStr
    password: str


@app.post("/api/auth/login")
def login(data: LoginRequest):
    try:
        result = supabase.auth.sign_in_with_password({
            "email": str(data.email),
            "password": data.password
        })

        if not result.user or not result.session:
            raise HTTPException(
                status_code=401,
                detail="Login gagal. Periksa email atau password."
            )

        return {
            "message": "Login berhasil!",
            "user_id": result.user.id,
            "email": result.user.email,
            "access_token": result.session.access_token,
            "token_type": "bearer"
        }

    except HTTPException:
        raise
    except Exception:
        raise HTTPException(
            status_code=401,
            detail="Login gagal. Periksa email, password, atau status konfirmasi email."
        )
