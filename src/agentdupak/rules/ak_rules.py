"""Rules engine angka kredit (AK), berdasarkan Lampiran III Permenpan RB 17/2013 & 46/2013.

Tiap tabel di sheet 'DUPAK OK' pada file DUPAK asli jadi rujukan nilai-nilai ini.
Baru mencakup 2 kategori yang sudah diverifikasi dari dokumen nyata (SK Mengajar,
SK Penguji non-skripsi) -- kategori lain ditambah setelah parser-nya ada.
"""

from __future__ import annotations

from agentdupak.models import Aktivitas

AK_PER_SKS_MENGAJAR = 1.0
AK_PENGUJI = {"ketua": 1.0, "anggota": 0.5}


def hitung_ak(aktivitas: Aktivitas) -> float:
    if aktivitas.kategori == "pendidikan.mengajar":
        return aktivitas.atribut["sks"] * AK_PER_SKS_MENGAJAR

    if aktivitas.kategori == "pendidikan.menguji":
        peran = aktivitas.atribut.get("peran")
        if peran not in AK_PENGUJI:
            raise ValueError(
                f"Peran penguji tidak dikenali: {peran!r} (sumber: {aktivitas.sumber_file})"
            )
        return AK_PENGUJI[peran]

    raise ValueError(f"Kategori belum punya rule AK: {aktivitas.kategori!r}")


def terapkan(aktivitas_list: list[Aktivitas]) -> list[Aktivitas]:
    """Isi field .ak pada tiap aktivitas, in place, lalu kembalikan list yang sama."""
    for a in aktivitas_list:
        a.ak = hitung_ak(a)
    return aktivitas_list
