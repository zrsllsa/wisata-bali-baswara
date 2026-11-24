from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field

from auth.dependencies import get_optional_user
from beranda.dikunjungi import id_dikunjungi
from services.itinerary import buat_itinerary

router = APIRouter(prefix="/jelajahi", tags=["Jelajahi"])


class RuteRequest(BaseModel):
    lat: float = Field(..., description="Latitude titik awal")
    lng: float = Field(..., description="Longitude titik awal")
    radius_km: float = Field(15, ge=1, le=50)
    hari: int = Field(..., ge=1, le=7)
    kategori: list[str] = []
    preferensi: str | None = Field(None, max_length=300)


@router.post("/rute")
def buat_rute(body: RuteRequest, user=Depends(get_optional_user)):
    # titik awal harus di sekitar Bali
    if not (-9.2 <= body.lat <= -8.0 and 114.4 <= body.lng <= 115.8):
        raise HTTPException(status_code=400, detail="Titik awal harus berada di Bali")

    try:
        return buat_itinerary(
            lat=body.lat,
            lng=body.lng,
            radius_km=body.radius_km,
            hari=body.hari,
            kategori=body.kategori,
            preferensi=body.preferensi,
            exclude_ids=id_dikunjungi(user.id) if user else (),
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Gagal membuat rute: {e}")