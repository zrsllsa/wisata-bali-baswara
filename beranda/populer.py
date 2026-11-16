from typing import Literal

from fastapi import APIRouter, HTTPException, Query
from supabase_client import supabase

router = APIRouter(prefix="/beranda", tags=["Beranda"])

Kategori = Literal["all", "budaya", "alam", "olahraga", "edukasi"]


@router.get("/populer")
def destinasi_populer(
    kategori: Kategori = Query("all", description="Filter kategori"),
):
    try:
        # 1. Ambil 6 wisata dengan rating tertinggi
        query = supabase.table("Wisata-bali").select("id, nama, rating")

        if kategori != "all":
            # ilike tanpa wildcard = cocok persis tapi tidak peka huruf besar/kecil
            query = query.ilike("kategori", kategori)

        wisata = query.order("rating", desc=True).limit(6).execute().data

        if not wisata:
            return {"kategori": kategori, "data": []}

        # 2. Ambil deskripsi dari wisata_detail untuk 6 wisata tadi
        ids = [w["id"] for w in wisata]
        detail = (
            supabase.table("wisata_detail")
            .select("wisata_id, deskripsi")
            .in_("wisata_id", ids)
            .execute()
            .data
        )
        deskripsi_map = {}
        for d in detail:
            deskripsi_map.setdefault(d["wisata_id"], d["deskripsi"])

        # 3. Gabungkan
        hasil = [
            {
                "id": w["id"],
                "nama": w["nama"],
                "rating": w["rating"],
                "deskripsi": deskripsi_map.get(w["id"]),
            }
            for w in wisata
        ]
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Gagal mengambil destinasi populer: {e}")

    return {"kategori": kategori, "data": hasil}