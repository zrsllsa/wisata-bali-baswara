from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from auth.dependencies import get_current_user
from supabase_client import supabase

router = APIRouter(prefix="/beranda", tags=["Beranda"])


class SimpanRequest(BaseModel):
    wisata_id: int  # ganti ke str jika id di Wisata-bali bertipe uuid/text


def _user_id(user) -> str:
    # mendukung user berupa dict maupun object
    return user["id"] if isinstance(user, dict) else user.id


@router.post("/simpan", status_code=201)
def simpan_destinasi(body: SimpanRequest, user=Depends(get_current_user)):
    user_id = _user_id(user)

    try:
        # pastikan wisata ada
        wisata = (
            supabase.table("Wisata-bali")
            .select("id")
            .eq("id", body.wisata_id)
            .execute()
            .data
        )
        if not wisata:
            raise HTTPException(status_code=404, detail="Wisata tidak ditemukan")

        # cegah duplikat
        sudah = (
            supabase.table("saved_destinations")
            .select("id")
            .eq("user_id", user_id)
            .eq("wisata_id", body.wisata_id)
            .execute()
            .data
        )
        if sudah:
            raise HTTPException(status_code=409, detail="Destinasi sudah disimpan")

        res = (
            supabase.table("saved_destinations")
            .insert({"user_id": user_id, "wisata_id": body.wisata_id})
            .execute()
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Gagal menyimpan destinasi: {e}")

    return {"message": "Destinasi berhasil disimpan", "data": res.data[0]}


@router.delete("/simpan/{wisata_id}")
def hapus_simpanan(wisata_id: int, user=Depends(get_current_user)):
    """Opsional: kalau user pencet tombol lagi untuk batal simpan."""
    user_id = _user_id(user)
    try:
        supabase.table("saved_destinations").delete().eq("user_id", user_id).eq(
            "wisata_id", wisata_id
        ).execute()
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Gagal menghapus simpanan: {e}")

    return {"message": "Simpanan dihapus"}