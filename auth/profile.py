import time

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile

from auth.dependencies import get_current_user
from supabase_client import get_supabase_admin

router = APIRouter(prefix="/api/auth", tags=["Authentication"])

AVATAR_BUCKET = "avatars"  # harus dibuat manual di Supabase Storage (public)
MAX_FOTO = 2 * 1024 * 1024
TIPE_FOTO = {"image/jpeg": "jpg", "image/png": "png", "image/webp": "webp"}


@router.patch("/profile")
async def edit_profile(
    name: str | None = Form(None),
    foto: UploadFile | None = File(None),
    password_lama: str | None = Form(None),
    password_baru: str | None = Form(None),
    user=Depends(get_current_user),
):
    admin = get_supabase_admin()
    metadata = dict(user.user_metadata or {})
    update: dict = {}

    # ---- nama ----
    if name is not None:
        name = name.strip()
        if not name:
            raise HTTPException(status_code=400, detail="Nama tidak boleh kosong.")
        metadata["full_name"] = name

    # ---- foto ----
    if foto is not None and foto.filename:
        ext = TIPE_FOTO.get(foto.content_type)
        if not ext:
            raise HTTPException(status_code=400, detail="Foto harus JPG, PNG, atau WEBP.")
        data = await foto.read()
        if len(data) > MAX_FOTO:
            raise HTTPException(status_code=400, detail="Ukuran foto maksimal 2 MB.")
        path = f"{user.id}/avatar.{ext}"
        try:
            admin.storage.from_(AVATAR_BUCKET).upload(
                path, data, {"content-type": foto.content_type, "upsert": "true"}
            )
            url = admin.storage.from_(AVATAR_BUCKET).get_public_url(path)
        except Exception as e:
            print("ERROR UPLOAD FOTO:", repr(e))
            raise HTTPException(status_code=500, detail="Gagal mengunggah foto.")
        # ?v= supaya browser tidak memakai foto lama dari cache
        metadata["avatar_url"] = f"{url.split('?')[0]}?v={int(time.time())}"

    # ---- password ----
    if password_baru is not None or password_lama is not None:
        if (user.app_metadata or {}).get("provider") != "email":
            raise HTTPException(
                status_code=400,
                detail="Akun Google tidak memakai password, jadi tidak bisa diganti.",
            )
        if not password_lama or not password_baru:
            raise HTTPException(
                status_code=400, detail="Password lama dan password baru wajib diisi."
            )
        if len(password_baru) < 8:
            raise HTTPException(status_code=400, detail="Password minimal 8 karakter.")
        try:
            # client admin baru tiap panggilan, jadi sesi login ini tidak menimpa client global
            get_supabase_admin().auth.sign_in_with_password(
                {"email": user.email, "password": password_lama}
            )
        except Exception:
            raise HTTPException(status_code=400, detail="Password lama salah.")
        update["password"] = password_baru

    if not update and metadata == (user.user_metadata or {}):
        raise HTTPException(status_code=400, detail="Tidak ada data yang diubah.")

    update["user_metadata"] = metadata
    try:
        admin.auth.admin.update_user_by_id(user.id, update)
    except Exception as e:
        print("ERROR EDIT PROFILE:", repr(e))
        raise HTTPException(status_code=400, detail=f"Gagal memperbarui profil: {e}")

    return {
        "message": "Profil berhasil diperbarui.",
        "name": metadata.get("full_name"),
        "avatar_url": metadata.get("avatar_url"),
        "password_diubah": "password" in update,
    }
