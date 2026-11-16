import math
import time

import numpy as np
from sklearn.cluster import KMeans
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

from supabase_client import supabase

PER_DAY = 3
CACHE_TTL = 600  # detik
_cache = {"data": None, "time": 0.0}


# ---------- Data ----------
def load_wisata() -> list[dict]:
    """Ambil semua wisata (730 baris), di-cache 10 menit supaya cepat."""
    now = time.time()
    if _cache["data"] is not None and now - _cache["time"] < CACHE_TTL:
        return _cache["data"]

    rows = (
        supabase.table("Wisata-bali")
        .select("id, nama, kategori, rating, latitude, longitude")
        .limit(2000)
        .execute()
        .data
    )

    bersih = []
    for r in rows:
        try:
            r["latitude"] = float(r["latitude"])
            r["longitude"] = float(r["longitude"])
        except (TypeError, ValueError):
            continue  # lewati baris tanpa koordinat valid
        r["rating"] = float(r["rating"] or 0)
        bersih.append(r)

    _cache["data"], _cache["time"] = bersih, now
    return bersih


def load_deskripsi(ids: list) -> dict:
    hasil = {}
    for i in range(0, len(ids), 100):  # dipecah supaya URL tidak kepanjangan
        chunk = ids[i : i + 100]
        rows = (
            supabase.table("wisata_detail")
            .select("wisata_id, deskripsi")
            .in_("wisata_id", chunk)
            .execute()
            .data
        )
        for d in rows:
            hasil.setdefault(d["wisata_id"], d["deskripsi"] or "")
    return hasil


# ---------- Stage 1: filter ----------
def haversine(lat1, lon1, lat2, lon2):
    R = 6371.0
    p1, p2 = np.radians(lat1), np.radians(lat2)
    dlat = p2 - p1
    dlon = np.radians(lon2) - np.radians(lon1)
    a = np.sin(dlat / 2) ** 2 + np.cos(p1) * np.cos(p2) * np.sin(dlon / 2) ** 2
    return R * 2 * np.arctan2(np.sqrt(a), np.sqrt(1 - a))


def filter_kategori(rows: list[dict], kategori: list[str]) -> list[dict]:
    keys = [k.strip().lower() for k in kategori if k.strip()]
    if not keys:
        return rows
    return [r for r in rows if any(k in (r.get("kategori") or "").lower() for k in keys)]


def tambah_jarak(rows: list[dict], lat: float, lng: float) -> list[dict]:
    for r in rows:
        r["jarak_km"] = float(haversine(lat, lng, r["latitude"], r["longitude"]))
    return rows


def filter_radius(rows: list[dict], radius_km: float) -> list[dict]:
    return [r for r in rows if r["jarak_km"] <= radius_km]


# ---------- Stage 2: scoring ----------
def beri_skor(kandidat: list[dict], radius_km: float, preferensi: str | None):
    for r in kandidat:
        r["_rating_n"] = r["rating"] / 5.0
        r["_jarak_n"] = 1 - (r["jarak_km"] / radius_km)

    if preferensi and preferensi.strip():
        desk = load_deskripsi([r["id"] for r in kandidat])
        corpus = [
            f'{r["nama"]} {r.get("kategori") or ""} {desk.get(r["id"], "")}'
            for r in kandidat
        ]
        tfidf = TfidfVectorizer().fit_transform(corpus + [preferensi])
        sim = cosine_similarity(tfidf[-1], tfidf[:-1]).flatten()
        for r, s in zip(kandidat, sim):
            r["skor"] = 0.40 * float(s) + 0.35 * r["_rating_n"] + 0.25 * r["_jarak_n"]
    else:
        for r in kandidat:
            r["skor"] = 0.70 * r["_rating_n"] + 0.30 * r["_jarak_n"]

    return sorted(kandidat, key=lambda x: x["skor"], reverse=True)


# ---------- Stage 3: K-Means seimbang ----------
def bagi_per_hari(items: list[dict], hari: int) -> list[list[dict]]:
    k = min(hari, len(items))
    if k <= 1:
        return [items]

    coords = np.array([[i["latitude"], i["longitude"]] for i in items])
    km = KMeans(n_clusters=k, random_state=42, n_init=10).fit(coords)
    pusat = km.cluster_centers_

    # semua pasangan (titik, cluster) diurut dari yang terdekat,
    # lalu ditempatkan selama kapasitas cluster (3) belum penuh
    pasangan = sorted(
        (float(haversine(c[0], c[1], pusat[j][0], pusat[j][1])), i, j)
        for i, c in enumerate(coords)
        for j in range(k)
    )
    ditempatkan, isi = {}, [0] * k
    for _, i, j in pasangan:
        if i in ditempatkan or isi[j] >= PER_DAY:
            continue
        ditempatkan[i] = j
        isi[j] += 1

    grup = [[] for _ in range(k)]
    for i, j in ditempatkan.items():
        grup[j].append(items[i])
    return [g for g in grup if g]


# ---------- Stage 4: urutan rute (Nearest Neighbor) ----------
def urutkan_rute(start: tuple[float, float], items: list[dict]):
    sisa, rute, cur, total = items[:], [], start, 0.0
    while sisa:
        nxt = min(sisa, key=lambda x: haversine(cur[0], cur[1], x["latitude"], x["longitude"]))
        jarak = float(haversine(cur[0], cur[1], nxt["latitude"], nxt["longitude"]))
        sisa.remove(nxt)
        nxt["_dari_sebelumnya"] = jarak
        total += jarak
        rute.append(nxt)
        cur = (nxt["latitude"], nxt["longitude"])
    return rute, total


# ---------- Pipeline utama ----------
def buat_itinerary(lat, lng, radius_km, hari, kategori, preferensi=None) -> dict:
    semua = [dict(r) for r in load_wisata()]  # salin supaya cache tidak berubah

    kandidat = filter_kategori(semua, kategori)
    kandidat = tambah_jarak(kandidat, lat, lng)
    kandidat = filter_radius(kandidat, radius_km)

    target = hari * PER_DAY
    peringatan = None
    if not kandidat:
        return {
            "titik_awal": {"lat": lat, "lng": lng},
            "hari": [],
            "peringatan": "Tidak ada destinasi dalam radius dan kategori ini. "
                          "Coba perbesar jarak atau ganti kategori.",
        }
    if len(kandidat) < target:
        peringatan = (
            f"Hanya {len(kandidat)} destinasi yang cocok (diminta {target}). "
            "Coba perbesar jarak atau tambah kategori."
        )

    terpilih = beri_skor(kandidat, radius_km, preferensi)[:target]
    kelompok = bagi_per_hari(terpilih, hari)

    # hari 1 = kelompok yang paling dekat dari titik awal
    def jarak_pusat(g):
        la = sum(x["latitude"] for x in g) / len(g)
        lo = sum(x["longitude"] for x in g) / len(g)
        return float(haversine(lat, lng, la, lo))

    kelompok.sort(key=jarak_pusat)

    hasil_hari = []
    for n, g in enumerate(kelompok, start=1):
        rute, total = urutkan_rute((lat, lng), g)
        hasil_hari.append({
            "hari_ke": n,
            "total_jarak_km": round(total, 1),
            "destinasi": [
                {
                    "urutan": u,
                    "id": d["id"],
                    "nama": d["nama"],
                    "kategori": d.get("kategori"),
                    "rating": d["rating"],
                    "latitude": d["latitude"],
                    "longitude": d["longitude"],
                    "jarak_dari_titik_awal_km": round(d["jarak_km"], 1),
                    "jarak_dari_sebelumnya_km": round(d["_dari_sebelumnya"], 1),
                }
                for u, d in enumerate(rute, start=1)
            ],
        })

    return {
        "titik_awal": {"lat": lat, "lng": lng},
        "radius_km": radius_km,
        "jumlah_hari": len(hasil_hari),
        "peringatan": peringatan,
        "hari": hasil_hari,
    }