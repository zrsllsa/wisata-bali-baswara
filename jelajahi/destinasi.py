from fastapi import APIRouter, Query

from services.itinerary import (
    filter_kategori,
    filter_radius,
    load_wisata,
    tambah_jarak,
)

router = APIRouter(prefix="/jelajahi", tags=["Jelajahi"])


@router.get("/destinasi")
def list_destinasi(
    q: str | None = Query(None, max_length=100, description="Cari nama wisata"),
    kategori: list[str] = Query(default=[], description="Bisa lebih dari satu"),
    lat: float | None = None,
    lng: float | None = None,
    radius_km: float | None = Query(None, ge=1, le=50),
    limit: int | None = Query(None, ge=1, le=1000, description="Batasi jumlah hasil"),
):
    rows = [dict(r) for r in load_wisata()]

    if q and q.strip():
        kw = q.strip().lower()
        rows = [r for r in rows if kw in (r["nama"] or "").lower()]

        def relevansi(r):
            n = (r["nama"] or "").lower()
            tingkat = 0 if n == kw else 1 if n.startswith(kw) else 2
            return (tingkat, -r["rating"])

        rows.sort(key=relevansi)  # yang paling cocok di urutan pertama

    rows = filter_kategori(rows, kategori)

    if lat is not None and lng is not None:
        rows = tambah_jarak(rows, lat, lng)
        if radius_km:
            rows = filter_radius(rows, radius_km)

    total = len(rows)
    if limit:
        rows = rows[:limit]

    data = [
        {
            "id": r["id"],
            "nama": r["nama"],
            "kategori": r.get("kategori"),
            "rating": r["rating"],
            "latitude": r["latitude"],
            "longitude": r["longitude"],
        }
        for r in rows
    ]
    return {"total": total, "data": data}