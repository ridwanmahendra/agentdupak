"""Rules engine angka kredit (AK), berdasarkan Lampiran III Permenpan RB 17/2013 & 46/2013.

Tiap tabel di sheet 'DUPAK OK' pada file DUPAK asli jadi rujukan nilai-nilai ini.
Baru mencakup kategori yang sudah diverifikasi dari dokumen nyata -- kategori
lain ditambah setelah nilai AK resminya dikonfirmasi (lihat PARSER_BY_KATEGORI
di pipeline.py untuk kategori yang parsernya sudah ada tapi belum ada di sini).
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


def terapkan(aktivitas_list: list[Aktivitas]) -> tuple[list[Aktivitas], list[str]]:
    """Isi field .ak pada tiap aktivitas, in place. Kategori yang belum punya
    rule TIDAK menggagalkan seluruh sync -- AK-nya diisi 0 sementara dan
    ditandai ak_perlu_review=True, supaya datanya tetap kelihatan (dan bisa
    diaudit) sambil menunggu aturan resminya dikonfirmasi."""
    peringatan: list[str] = []
    for a in aktivitas_list:
        try:
            a.ak = hitung_ak(a)
        except ValueError as e:
            a.ak = 0.0
            a.ak_perlu_review = True
            peringatan.append(str(e))
    return aktivitas_list, peringatan
