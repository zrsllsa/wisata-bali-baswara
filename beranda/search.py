from fastapi import APIRouter, HTTPException, Query
from supabase_client import supabase

router = APIRouter(prefix="/beranda", tags=["Beranda"])


@router.get("/search")
def search_wisata(
    q: str = Query(..., min_length=1, max_length=100, description="Kata kunci pencarian"),
    limit: int = Query(20, ge=1, le=50),
):
    # bersihkan karakter yang bisa mengganggu filter ilike
    keyword = q.strip().replace("%", "").replace(",", " ")
    if not keyword:
        raise HTTPException(status_code=400, detail="Kata kunci tidak valid")

    try:
        res = (
            supabase.table("Wisata-bali")
            .select("id, nama, rating")
            .ilike("nama", f"%{keyword}%")
            .order("rating", desc=True)
            .limit(limit)
            .execute()
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Gagal mencari wisata: {e}")

    return {"query": keyword, "total": len(res.data), "data": res.data}