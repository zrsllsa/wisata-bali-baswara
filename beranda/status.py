from fastapi import APIRouter, Depends, HTTPException

from auth.dependencies import get_current_user
from beranda.dikunjungi import id_dikunjungi
from supabase_client import supabase

router = APIRouter(prefix="/beranda", tags=["Beranda"])


@router.get("/status")
def status_kartu(user=Depends(get_current_user)):
    """Satu request untuk mewarnai tombol favorit & dikunjungi di semua kartu."""
    try:
        fav = (
            supabase.table("saved_destinations")
            .select("wisata_id")
            .eq("user_id", user.id)
            .execute()
            .data
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Gagal mengambil status: {e}")
    return {
        "favorit": [r["wisata_id"] for r in fav],
        "dikunjungi": sorted(id_dikunjungi(user.id)),
    }
