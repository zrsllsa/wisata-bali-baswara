import random

from fastapi import APIRouter, HTTPException

from supabase_client import supabase

router = APIRouter(prefix="/jelajahi", tags=["Jelajahi"])


def _bersih(v):
    """Ubah NULL / 'nan' / string kosong menjadi None."""
    if v is None:
        return None
    s = str(v).strip()
    return None if s == "" or s.lower() in ("nan", "none", "null") else s


def _singkat(teks: str, maks: int = 200) -> str:
    if len(teks) <= maks:
        return teks
    potong = teks[:maks].rsplit(" ", 1)[0]
    return potong.rstrip(".,;:- ") + "…"


def _angka(v) -> float:
    try:
        return float(v)
    except (TypeError, ValueError):
        return 0.0


@router.get("/destinasi/{wisata_id}")
def detail_destinasi(wisata_id: int):
    try:
        utama = (
            supabase.table("Wisata-bali")
            .select("id, nama, kategori, kabupaten_kota, preferensi, rating, latitude, longitude, link")
            .eq("id", wisata_id)
            .limit(1)
            .execute()
            .data
        )
        if not utama:
            raise HTTPException(status_code=404, detail="Wisata tidak ditemukan")
        w = utama[0]

        det = (
            supabase.table("wisata_detail")
            .select("deskripsi, alamat_lengkap, desa_kelurahan, kecamatan, jam_buka, photo_url_utama")
            .eq("wisata_id", wisata_id)
            .limit(1)
            .execute()
            .data
        )
        d = det[0] if det else {}

        foto_rows = (
            supabase.table("wisata_foto")
            .select("photo_url")
            .eq("wisata_id", wisata_id)
            .execute()
            .data
        )

        ulasan_rows = (
            supabase.table("wisata_ulasan")
            .select("nama_pengulas, rating, waktu, komentar")
            .eq("wisata_id", wisata_id)
            .order("rating", desc=True)
            .limit(20)
            .execute()
            .data
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Gagal mengambil detail wisata: {e}")

    # ---- foto: 1 acak dari wisata_foto, cadangan photo_url_utama ----
    daftar_foto = [f["photo_url"] for f in foto_rows if _bersih(f.get("photo_url"))]
    if daftar_foto:
        foto = random.choice(daftar_foto)
    else:
        foto = _bersih(d.get("photo_url_utama"))

    # ---- lokasi ----
    desa = _bersih(d.get("desa_kelurahan"))
    kabupaten = _bersih(w.get("kabupaten_kota"))
    lokasi = ", ".join(x for x in (desa, kabupaten) if x)

    # ---- deskripsi singkat ----
    deskripsi = _bersih(d.get("deskripsi"))
    if deskripsi:
        deskripsi = _singkat(deskripsi)
    else:
        jenis = _bersih(w.get("preferensi")) or _bersih(w.get("kategori")) or "wisata"
        deskripsi = f"{w['nama']} termasuk {jenis} di {kabupaten or 'Bali'}."

    # ---- 1 ulasan terbaik: rating tertinggi, lalu komentar terpanjang ----
    ulasan = None
    kandidat = [u for u in ulasan_rows if _bersih(u.get("komentar"))]
    if kandidat:
        terbaik = max(kandidat, key=lambda u: (_angka(u.get("rating")), len(u["komentar"])))
        ulasan = {
            "nama_pengulas": _bersih(terbaik.get("nama_pengulas")),
            "rating": _angka(terbaik.get("rating")),
            "waktu": _bersih(terbaik.get("waktu")),
            "komentar": _singkat(terbaik["komentar"].strip(), 300),
        }

    # ---- link google maps ----
    link_maps = _bersih(w.get("link")) or (
        f"https://www.google.com/maps?q={w.get('latitude')},{w.get('longitude')}"
    )

    return {
        "id": w["id"],
        "nama": w["nama"],
        "kategori": _bersih(w.get("kategori")),
        "rating": w.get("rating"),
        "desa_kelurahan": desa,
        "kabupaten": kabupaten,
        "lokasi": lokasi,
        "deskripsi": deskripsi,
        "foto": foto,
        "ulasan": ulasan,
        "link_maps": link_maps,
        "latitude": w.get("latitude"),
        "longitude": w.get("longitude"),
    }