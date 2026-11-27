import os

import secrets

import hashlib

import requests


from datetime import datetime, timedelta, timezone



from fastapi import APIRouter, HTTPException

from pydantic import BaseModel, EmailStr

from supabase_client import supabase, get_supabase_admin



router = APIRouter(
    prefix="/api/auth",
    tags=["Authentication"]
)


# =========================================================
# REQUEST MODEL
# =========================================================

class RegisterRequest(BaseModel):
    name: str
    email: EmailStr
    password: str


class VerifyOTPRequest(BaseModel):
    email: EmailStr
    otp: str


# =========================================================
# PASSWORD HASH
# =========================================================

def hash_password(password: str) -> str:
    """
    Hash password menggunakan PBKDF2 SHA-256.

    Hasil:
        salt$password_hash
    """

    salt = secrets.token_hex(16)

    password_hash = hashlib.pbkdf2_hmac(
        "sha256",
        password.encode("utf-8"),
        salt.encode("utf-8"),
        100_000
    ).hex()

    return f"{salt}${password_hash}"


# =========================================================
# VERIFY PASSWORD
# =========================================================

def verify_password(
    password: str,
    stored_password: str
) -> bool:

    try:

        salt, password_hash = stored_password.split(
            "$",
            1
        )

        check_hash = hashlib.pbkdf2_hmac(
            "sha256",
            password.encode("utf-8"),
            salt.encode("utf-8"),
            100_000
        ).hex()

        return secrets.compare_digest(
            check_hash,
            password_hash
        )

    except Exception:

        return False


# =========================================================
# SEND OTP EMAIL
# =========================================================

def send_verification_email(
    email: str,
    otp: str
):

    # Brevo lewat HTTPS: Railway memblokir SMTP keluar.
    # Pengirim = SMTP_EMAIL, harus sudah diverifikasi sebagai sender di Brevo.
    api_key = os.getenv("BREVO_API_KEY")

    sender = os.getenv("SMTP_EMAIL")

    if not api_key:
        raise Exception("BREVO_API_KEY tidak ditemukan di env")

    if not sender:
        raise Exception("SMTP_EMAIL tidak ditemukan di env")

    res = requests.post(
        "https://api.brevo.com/v3/smtp/email",
        headers={"api-key": api_key},
        json={
            "sender": {"name": "Langkah Baswara", "email": sender},
            "to": [{"email": email}],
            "subject": "Kode Verifikasi Akun Langkah Baswara",
            "textContent": f"""Halo!

Terima kasih sudah mendaftar di Langkah Baswara.

Kode OTP verifikasi akun kamu: {otp}

Kode ini berlaku selama 30 menit.

Jika kamu tidak merasa melakukan pendaftaran, abaikan email ini.

Salam,
Langkah Baswara""",
        },
        timeout=30,
    )

    if not res.ok:
        raise Exception(f"Brevo {res.status_code}: {res.text}")


# =========================================================
# REGISTER
# =========================================================

admin = get_supabase_admin()

admin.table("pending_registrations")


@router.post("/register")

def register(data: RegisterRequest):

    print("====================================")

    print("🔥 REGISTER BARU")

    print("EMAIL:", data.email)

    print("====================================")


    try:

        admin = get_supabase_admin()


        # =================================================
        # 1. NORMALISASI DATA
        # =================================================

        name = data.name.strip()

        email = str(data.email).lower().strip()

        password = data.password


        # -------------------------------------------------
        # Validasi nama
        # -------------------------------------------------

        if not name:

            raise HTTPException(
                status_code=400,
                detail="Nama tidak boleh kosong."
            )


        # -------------------------------------------------
        # Validasi password
        # -------------------------------------------------

        if len(password) < 8:

            raise HTTPException(
                status_code=400,
                detail="Password minimal 8 karakter."
            )


        # =================================================
        # 2. CEK EMAIL DI USERS
        # =================================================

        existing_user = (

            supabase

            .table("users")

            .select("id")

            .eq("email", email)

            .limit(1)

            .execute()

        )


        if existing_user.data:

            raise HTTPException(
                status_code=400,
                detail="Email sudah terdaftar."
            )


        # =================================================
        # 3. BUAT OTP 6 DIGIT
        # =================================================

        otp = str(
            secrets.randbelow(1_000_000)
        ).zfill(6)


        print("OTP dibuat untuk:", email)


        # =================================================
        # 4. HASH OTP
        # =================================================

        otp_hash = hashlib.sha256(
            otp.encode("utf-8")
        ).hexdigest()


        # =================================================
        # 5. WAKTU EXPIRED
        # =================================================

        expires_at = (

            datetime.now(timezone.utc)

            + timedelta(minutes=30)

        )


        # =================================================
        # 6. HASH PASSWORD
        # =================================================

        password_hash = password


        # =================================================
        # 7. HAPUS PENDING LAMA
        # =================================================

        admin.table(
            "pending_registrations"
        ).delete().eq(
            "email",
            email
        ).execute()


        # =================================================
        # 8. SIMPAN KE PENDING
        # =================================================

        pending_data = {

            "name": name,

            "email": email,

            "password": password_hash,

            "otp_hash": otp_hash,

            "expires_at": expires_at.isoformat()

        }


        admin.table(
            "pending_registrations"
        ).insert(
            pending_data
        ).execute()


        print(
            "✅ Data pending berhasil disimpan"
        )


        # =================================================
        # 9. KIRIM OTP KE GMAIL
        # =================================================

        try:

            send_verification_email(
                email=email,
                otp=otp
            )


            print(
                "✅ OTP berhasil dikirim ke:",
                email
            )


        except Exception as e:

            print(
                "❌ ERROR SMTP:",
                repr(e)
            )


            # ---------------------------------------------
            # HAPUS PENDING JIKA EMAIL GAGAL
            # ---------------------------------------------

            try:

                admin.table(
                    "pending_registrations"
                ).delete().eq(
                    "email",
                    email
                ).execute()


                print(
                    "✅ Pending registration dihapus"
                )


            except Exception as delete_error:

                print(
                    "❌ ERROR DELETE PENDING:",
                    repr(delete_error)
                )


            raise HTTPException(
                status_code=400,
                detail=(
                    "Registrasi gagal. "
                    "Email OTP tidak dapat dikirim."
                )
            )


        # =================================================
        # 10. RESPONSE
        # =================================================

        return {

            "success": True,

            "message": (
                "OTP berhasil dikirim. "
                "Silakan cek email kamu."
            ),

            "email": email

        }


    # =====================================================
    # HTTP ERROR
    # =====================================================

    except HTTPException:

        raise


    # =====================================================
    # ERROR LAIN
    # =====================================================

    except Exception as e:

        print(
            "❌ ERROR REGISTER:",
            repr(e)
        )


        raise HTTPException(
            status_code=500,
            detail=f"Register gagal: {str(e)}"
        )


# =========================================================
# KIRIM ULANG OTP
# =========================================================

class ResendOTPRequest(BaseModel):
    email: EmailStr


@router.post("/resend-otp")
def resend_otp(data: ResendOTPRequest):

    email = str(data.email).lower().strip()
    admin = get_supabase_admin()
    masa_berlaku = timedelta(minutes=30)

    try:
        rows = (
            admin.table("pending_registrations")
            .select("expires_at")
            .eq("email", email)
            .limit(1)
            .execute()
            .data
        )
        if not rows:
            raise HTTPException(
                status_code=400,
                detail="Data pendaftaran tidak ditemukan. Silakan daftar kembali."
            )

        expires_at = datetime.fromisoformat(rows[0]["expires_at"].replace("Z", "+00:00"))
        if expires_at.tzinfo is None:
            expires_at = expires_at.replace(tzinfo=timezone.utc)

        # jeda 60 detik sejak OTP terakhir, supaya tidak bisa dipakai membanjiri email
        if datetime.now(timezone.utc) - (expires_at - masa_berlaku) < timedelta(seconds=60):
            raise HTTPException(
                status_code=429,
                detail="Tunggu 1 menit sebelum meminta kode baru."
            )

        otp = str(secrets.randbelow(1_000_000)).zfill(6)

        # kirim dulu: kalau email gagal, kode lama tetap berlaku
        send_verification_email(email=email, otp=otp)

        admin.table("pending_registrations").update({
            "otp_hash": hashlib.sha256(otp.encode("utf-8")).hexdigest(),
            "expires_at": (datetime.now(timezone.utc) + masa_berlaku).isoformat()
        }).eq("email", email).execute()

    except HTTPException:
        raise

    except Exception as e:
        print("ERROR RESEND OTP:", repr(e))
        raise HTTPException(status_code=500, detail="Gagal mengirim ulang kode OTP.")

    return {"success": True, "message": "Kode OTP baru sudah dikirim."}


# =========================================================
# VERIFY OTP
# =========================================================

@router.post("/verify-otp")

def verify_otp(data: VerifyOTPRequest):

    print("====================================")

    print("🔐 VERIFY OTP")

    print("EMAIL:", data.email)

    print("====================================")


    try:


        # =================================================
        # 1. NORMALISASI
        # =================================================

        email = str(data.email).lower().strip()

        otp = data.otp.strip()


        # =================================================
        # 2. VALIDASI OTP
        # =================================================

        if not otp.isdigit():

            raise HTTPException(
                status_code=400,
                detail="OTP harus berupa angka."
            )


        if len(otp) != 6:

            raise HTTPException(
                status_code=400,
                detail="OTP harus terdiri dari 6 digit."
            )


        # =================================================
        # 3. CARI PENDING REGISTRATION
        # =================================================

        result = (

            supabase

            .table("pending_registrations")

            .select("*")

            .eq("email", email)

            .limit(1)

            .execute()

        )


        if not result.data:

            raise HTTPException(
                status_code=400,
                detail=(
                    "Data pendaftaran tidak ditemukan. "
                    "Silakan daftar kembali."
                )
            )


        pending = result.data[0]


        # =================================================
        # 4. CEK EXPIRED
        # =================================================

        expires_at = datetime.fromisoformat(

            pending["expires_at"].replace(
                "Z",
                "+00:00"
            )

        )


        now = datetime.now(timezone.utc)


        if now > expires_at:


            # ---------------------------------------------
            # HAPUS DATA EXPIRED
            # ---------------------------------------------

            admin.table(
                "pending_registrations"
            ).delete().eq(
                "email",
                email
            ).execute()


            raise HTTPException(
                status_code=400,
                detail=(
                    "Kode OTP sudah kadaluarsa. "
                    "Silakan daftar kembali."
                )
            )


        # =================================================
        # 5. HASH OTP YANG DIINPUT USER
        # =================================================

        entered_otp_hash = hashlib.sha256(
            otp.encode("utf-8")
        ).hexdigest()


        # =================================================
        # 6. BANDINKAN OTP
        # =================================================

        if not secrets.compare_digest(
            entered_otp_hash,
            pending["otp_hash"]
        ):

            raise HTTPException(
                status_code=400,
                detail="Kode OTP salah."
            )


        print(
            "✅ OTP BENAR"
        )


        # =================================================
        # 7. CEK LAGI EMAIL DI USERS
        # =================================================

        existing_user = (

            supabase

            .table("users")

            .select("id")

            .eq("email", email)

            .limit(1)

            .execute()

        )


        if existing_user.data:


            # Hapus pending

            admin.table(
                "pending_registrations"
            ).delete().eq(
                "email",
                email
            ).execute()


            raise HTTPException(
                status_code=400,
                detail="Email sudah terdaftar."
            )


        # =================================================
        # 8. PINDAHKAN KE USERS
        # =================================================

        admin = get_supabase_admin()


        user_result = supabase.auth.admin.create_user({

            "email": pending["email"],

            "password": pending["password"],

            "email_confirm": True,

            "user_metadata": {

                "full_name": pending["name"]

            }

        })


        print("=== AUTH USER RESULT ===")

        print("USER:", user_result.user)

        print(
            "USER ID:",
            user_result.user.id if user_result.user else None
        )

        print(
            "EMAIL:",
            user_result.user.email if user_result.user else None
        )


        if not user_result.user:

            raise HTTPException(
                status_code=400,
                detail="Gagal membuat akun di Supabase Auth."
            )


        user_id = user_result.user.id


        print(
            "✅ USER BERHASIL DIBUAT DI AUTH.USERS"
        )


        # =================================================
        # 9. HAPUS PENDING
        # =================================================

        admin.table(
            "pending_registrations"
        ).delete().eq(
            "email",
            email
        ).execute()


        print(
            "✅ PENDING REGISTRATION DIHAPUS"
        )


        # =================================================
        # 10. RESPONSE KE FRONTEND
        # =================================================

        return {

            "success": True,

            "message": (
                "Email berhasil diverifikasi. "
                "Akun berhasil dibuat."
            ),

            "email": email,

            "redirect": "/login"

        }


    # =====================================================
    # HTTP ERROR
    # =====================================================

    except HTTPException:

        raise


    # =====================================================
    # ERROR LAIN
    # =====================================================

    except Exception as e:

        print(
            "❌ ERROR VERIFY OTP:",
            repr(e)
        )


        raise HTTPException(
            status_code=500,
            detail=(
                f"Verifikasi OTP gagal: {str(e)}"
            )
        )
