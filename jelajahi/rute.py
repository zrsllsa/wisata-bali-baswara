from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

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
def buat_rute(body: RuteRequest):
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
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Gagal membuat rute: {e}")