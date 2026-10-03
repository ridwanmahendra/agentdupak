"""Parsing tanggal berbahasa Indonesia + penentuan semester akademik dari
tanggal itu -- dibutuhkan karena data dari SK Penguji & SK Bimbingan cuma
punya tanggal mentah (bukan label semester eksplisit seperti SK Mengajar),
padahal format DUPAK resmi mengelompokkan semua aktivitas per semester.

Konvensi (sesuai contoh di template DUPAK asli):
  Genap  = Februari s/d Juli,   tahun ajaran <tahun-1>/<tahun>
  Ganjil = Agustus s/d Januari, tahun ajaran <tahun>/<tahun+1> (Jan jadi tahun-1/tahun)
"""

from __future__ import annotations

import re
from datetime import date

_BULAN_KE_ANGKA = {
    "januari": 1, "jan": 1,
    "februari": 2, "feb": 2,
    "maret": 3, "mar": 3,
    "april": 4, "apr": 4,
    "mei": 5,
    "juni": 6, "jun": 6,
    "juli": 7, "jul": 7,
    "agustus": 8, "agu": 8, "aug": 8,
    "september": 9, "sep": 9,
    "oktober": 10, "okt": 10,
    "november": 11, "nov": 11,
    "desember": 12, "des": 12, "dec": 12,
}

_POLA_TANGGAL = re.compile(r"(\d{1,2})\s+([A-Za-z]+)\.?\s+(\d{4})")


def parse_tanggal(teks: str | None) -> date | None:
    """Parse '13 Mei 2026', '24 Des 2025', dst. Kembalikan None kalau tidak dikenali."""
    if not teks:
        return None
    m = _POLA_TANGGAL.search(teks)
    if not m:
        return None
    hari, nama_bulan, tahun = m.groups()
    bulan = _BULAN_KE_ANGKA.get(nama_bulan.lower())
    if bulan is None:
        return None
    try:
        return date(int(tahun), bulan, int(hari))
    except ValueError:
        return None


def tentukan_semester(tanggal: date) -> tuple[str, str]:
    """Kembalikan (label, tahun_ajaran), misal ('Genap', '2024/2025')."""
    if 2 <= tanggal.month <= 7:
        return "Genap", f"{tanggal.year - 1}/{tanggal.year}"
    if tanggal.month == 1:
        return "Ganjil", f"{tanggal.year - 1}/{tanggal.year}"
    return "Ganjil", f"{tanggal.year}/{tanggal.year + 1}"


def rentang_bulan(label: str, tahun_ajaran: str) -> str:
    """'(Februari 2025 s/d Juli 2025)' atau '(Agustus 2024 s/d Januari 2025)'."""
    awal, akhir = tahun_ajaran.split("/")
    if label == "Genap":
        return f"(Februari {akhir} s/d Juli {akhir})"
    return f"(Agustus {awal} s/d Januari {akhir})"
