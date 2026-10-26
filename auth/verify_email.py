import hashlib
from datetime import datetime, timezone

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, EmailStr

from supabase_client import supabase


router = APIRouter(
    prefix="/api/auth",
    tags=["Authentication"]
)


class VerifyEmailRequest(BaseModel):
    email: EmailStr
    otp: str


@router.post("/verify-email")
def verify_email(data: VerifyEmailRequest):

    try:
        # =========================================================
        # 1. NORMALISASI DATA
        # =========================================================

        email = str(data.email).lower().strip()
        otp = str(data.otp).strip()

        print("======================================")
        print("VERIFY EMAIL")
        print("EMAIL:", email)
        print("OTP:", otp)
        print("======================================")


        # =========================================================
        # 2. VALIDASI OTP
        # =========================================================

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


        # =========================================================
        # 3. HASH OTP
        # =========================================================

        otp_hash = hashlib.sha256(
            otp.encode("utf-8")
        ).hexdigest()

        print("OTP HASH:", otp_hash)


        # =========================================================
        # 4. CARI DATA PENDING REGISTRATION
        # =========================================================

        result = (
            supabase
            .table("pending_registrations")
            .select("*")
            .eq("email", email)
            .limit(1)
            .execute()
        )

        print("PENDING DATA:", result.data)


        if not result.data:
            raise HTTPException(
                status_code=400,
                detail=(
                    "Data registrasi tidak ditemukan. "
                    "Silakan daftar kembali."
                )
            )


        pending = result.data[0]


        # =========================================================
        # 5. AMBIL OTP HASH
        # =========================================================

        stored_otp_hash = pending.get("otp_hash")

        print("STORED OTP HASH:", stored_otp_hash)
        print("INPUT OTP HASH :", otp_hash)


        if not stored_otp_hash:
            raise HTTPException(
                status_code=400,
                detail="OTP belum tersimpan pada data registrasi."
            )


        # =========================================================
        # 6. VALIDASI OTP
        # =========================================================

        if str(stored_otp_hash).strip() != otp_hash:
            raise HTTPException(
                status_code=400,
                detail="OTP tidak valid."
            )

        print("✅ OTP BENAR")


        # =========================================================
        # 7. CEK EXPIRED
        # =========================================================

        expires_at_raw = pending.get("expires_at")

        if not expires_at_raw:
            raise HTTPException(
                status_code=400,
                detail="Waktu kedaluwarsa OTP tidak ditemukan."
            )


        try:
            expires_at = datetime.fromisoformat(
                str(expires_at_raw).replace(
                    "Z",
                    "+00:00"
                )
            )

        except ValueError:
            raise HTTPException(
                status_code=400,
                detail="Format waktu OTP tidak valid."
            )


        if expires_at.tzinfo is None:
            expires_at = expires_at.replace(
                tzinfo=timezone.utc
            )


        now = datetime.now(timezone.utc)

        print("CURRENT TIME :", now)
        print("EXPIRES TIME :", expires_at)


        if now > expires_at:
            raise HTTPException(
                status_code=400,
                detail="OTP sudah kedaluwarsa."
            )


        # =========================================================
        # 8. AMBIL DATA USER
        # =========================================================

        name = pending.get("name")
        password = pending.get("password")
        pending_email = pending.get("email")


        if not name:
            raise HTTPException(
                status_code=400,
                detail="Nama registrasi tidak ditemukan."
            )


        if not password:
            raise HTTPException(
                status_code=400,
                detail="Password registrasi tidak ditemukan."
            )


        if not pending_email:
            raise HTTPException(
                status_code=400,
                detail="Email registrasi tidak ditemukan."
            )


        pending_email = str(
            pending_email
        ).lower().strip()


        # =========================================================
        # 9. CEK USER DI PUBLIC.USERS
        # =========================================================
        # Sementara tetap dipertahankan agar tidak mengubah
        # alur kode kamu yang lain.
        # =========================================================

        existing_user = (
            supabase
            .table("users")
            .select("id, email")
            .eq("email", pending_email)
            .limit(1)
            .execute()
        )


        if existing_user.data:
            raise HTTPException(
                status_code=409,
                detail="Email sudah terdaftar. Silakan login."
            )


        # =========================================================
        # 10. BUAT USER DI SUPABASE AUTH
        # =========================================================

        print("======================================")
        print("MEMBUAT USER DI SUPABASE AUTH")
        print("EMAIL:", pending_email)
        print("======================================")


        user_result = supabase.auth.admin.create_user({
            "email": pending_email,
            "password": password,
            "email_confirm": True,
            "user_metadata": {
                "full_name": name
            }
        })


        # =========================================================
        # 10.1. CEK HASIL CREATE USER
        # =========================================================

        print("=== AUTH USER RESULT ===")
        print("USER:", user_result.user)
        print(
            "USER ID:",
            user_result.user.id
            if user_result.user
            else None
        )
        print(
            "EMAIL:",
            user_result.user.email
            if user_result.user
            else None
        )


        if not user_result.user:
            raise HTTPException(
                status_code=400,
                detail="Gagal membuat akun di Supabase Auth."
            )


        user_id = user_result.user.id

        print("✅ USER BERHASIL DIBUAT DI AUTH.USERS")
        print("USER ID:", user_id)


        # =========================================================
        # 11. HAPUS DATA PENDING
        # =========================================================

        delete_result = (
            supabase
            .table("pending_registrations")
            .delete()
            .eq("email", pending_email)
            .execute()
        )


        print(
            "DELETE PENDING:",
            delete_result.data
        )


        # =========================================================
        # 12. BERHASIL
        # =========================================================

        return {
            "success": True,
            "message": (
                "OTP berhasil diverifikasi. "
                "Registrasi berhasil."
            ),
            "email": pending_email,
            "redirect": "/login"
        }


    # =============================================================
    # HTTP EXCEPTION
    # =============================================================

    except HTTPException:
        raise


    # =============================================================
    # ERROR LAINNYA
    # =============================================================

    except Exception as e:

        print("======================================")
        print("ERROR VERIFY EMAIL")
        print(repr(e))
        print("======================================")


        raise HTTPException(
            status_code=400,
            detail=f"Verifikasi OTP gagal: {str(e)}"
        )