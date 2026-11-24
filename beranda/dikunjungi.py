from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from auth.dependencies import get_current_user
from beranda.simpan import ringkas_wisata
from supabase_client import get_supabase_admin

router = APIRouter(prefix="/beranda", tags=["Beranda"])

# service role: tabel ini hanya diakses lewat backend, selalu difilter per user_id
admin = get_supabase_admin()
TABEL = "visited_destinations"


class DikunjungiRequest(BaseModel):
    wisata_id: int


def id_dikunjungi(user_id: str) -> set:
    """Dipakai /jelajahi/rute untuk membuang destinasi yang sudah dikunjungi."""
    try:
        rows = admin.table(TABEL).select("wisata_id").eq("user_id", user_id).execute().data
    except Exception as e:
        print("ERROR BACA DIKUNJUNGI:", repr(e))
        return set()  # jangan gagalkan rute hanya karena daftar ini tidak terbaca
    return {r["wisata_id"] for r in rows}


@router.post("/dikunjungi", status_code=201)
def tandai_dikunjungi(body: DikunjungiRequest, user=Depends(get_current_user)):
    try:
        ada = admin.table("Wisata-bali").select("id").eq("id", body.wisata_id).execute().data
        if not ada:
            raise HTTPException(status_code=404, detail="Wisata tidak ditemukan")
        # upsert: menekan tombol dua kali tidak error
        admin.table(TABEL).upsert(
            {"user_id": user.id, "wisata_id": body.wisata_id},
            on_conflict="user_id,wisata_id",
        ).execute()
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Gagal menandai dikunjungi: {e}")
    return {"message": "Ditandai sudah dikunjungi"}


@router.delete("/dikunjungi/{wisata_id}")
def batal_dikunjungi(wisata_id: int, user=Depends(get_current_user)):
    try:
        admin.table(TABEL).delete().eq("user_id", user.id).eq("wisata_id", wisata_id).execute()
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Gagal membatalkan: {e}")
    return {"message": "Tanda dikunjungi dihapus"}


@router.get("/dikunjungi")
def daftar_dikunjungi(user=Depends(get_current_user)):
    """Daftar wisata yang sudah dikunjungi user, terbaru di atas."""
    try:
        rows = (
            admin.table(TABEL)
            .select("wisata_id")
            .eq("user_id", user.id)
            .order("created_at", desc=True)
            .execute()
            .data
        )
        ids = [r["wisata_id"] for r in rows]
        info = ringkas_wisata(ids)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Gagal mengambil daftar: {e}")
    return {"total": len(ids), "ids": ids, "data": [info[i] for i in ids if i in info]}
