from typing import Literal

from fastapi import APIRouter, HTTPException, Query
from supabase_client import supabase

from jelajahi.detail import _bersih, _singkat

router = APIRouter(prefix="/beranda", tags=["Beranda"])

Kategori = Literal["all", "budaya", "alam", "olahraga", "edukasi"]


@router.get("/populer")
def destinasi_populer(
    kategori: Kategori = Query("all", description="Filter kategori"),
):
    try:
        # 1. Ambil 6 wisata dengan rating tertinggi
        # rating NULL harus dibuang: di Postgres NULL dianggap terbesar saat desc
        query = (
            supabase.table("Wisata-bali")
            .select("id, nama, kategori, kabupaten_kota, preferensi, rating")
            .not_.is_("rating", "null")
        )

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
            .select("wisata_id, deskripsi, photo_url_utama")
            .in_("wisata_id", ids)
            .execute()
            .data
        )
        deskripsi_map, utama_map = {}, {}
        for d in detail:
            deskripsi_map.setdefault(d["wisata_id"], _bersih(d["deskripsi"]))
            utama_map.setdefault(d["wisata_id"], _bersih(d["photo_url_utama"]))

        # foto: yang is_primary dulu, cadangan photo_url_utama
        foto_rows = (
            supabase.table("wisata_foto")
            .select("wisata_id, photo_url")
            .in_("wisata_id", ids)
            .order("is_primary", desc=True)
            .order("urutan")
            .execute()
            .data
        )
        foto_map = {}
        for f in foto_rows:
            if _bersih(f["photo_url"]):
                foto_map.setdefault(f["wisata_id"], f["photo_url"])

        # 3. Gabungkan
        hasil = [
            {
                "id": w["id"],
                "nama": w["nama"],
                "rating": w["rating"],
                "foto": foto_map.get(w["id"]) or utama_map.get(w["id"]),
                "deskripsi": (deskripsi_map.get(w["id"]) and _singkat(deskripsi_map[w["id"]]))
                or f'{w["nama"]} termasuk {_bersih(w.get("preferensi")) or _bersih(w.get("kategori")) or "wisata"} di {_bersih(w.get("kabupaten_kota")) or "Bali"}.',
            }
            for w in wisata
        ]
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Gagal mengambil destinasi populer: {e}")

    return {"kategori": kategori, "data": hasil}