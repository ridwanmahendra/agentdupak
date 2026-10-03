from __future__ import annotations

import re

from agentdupak.models import Aktivitas


_BULAN = (
    r"Jan(?:uari)?|Feb(?:ruari)?|Mar(?:et)?|Apr(?:il)?|Mei|Jun(?:i)?|"
    r"Jul(?:i)?|Agu(?:stus)?|Sep(?:tember)?|Okt(?:ober)?|Nov(?:ember)?|Des(?:ember)?"
)
_TANGGAL_DI_AWAL_RE = re.compile(
    rf"^(?P<tanggal>\d{{1,2}}\s+(?:{_BULAN})\.?\s+\d{{4}})\s*-\s*", re.IGNORECASE
)
_NIM_DI_AKHIR_RE = re.compile(r"(?P<nim>\d{6,})\s*$")

# Kode prodi pendek yang kelihatan muncul di nama file ini (bukan daftar lengkap
# resmi -- cuma yang ketemu di sampel nyata; tambah kalau ketemu kode lain).
_KODE_PRODI_DIKENAL = {"IF", "SI", "TI", "TK", "MI"}


def parse(text: str, sumber_file: str = "") -> list[Aktivitas]:
    """Parse nama file bimbingan non-skripsi/publikasi karya ilmiah.

    Nama filenya TIDAK konsisten (beda urutan segmen antar file, kadang tanpa
    tanggal, kadang nama+NIM nempel tanpa spasi) -- jadi parsing dilakukan per
    segmen (dipisah ' - '), bukan posisi tetap, supaya lebih tahan terhadap
    variasi itu. `text` diabaikan sepenuhnya (lihat `butuh_download`).
    """
    nama = sumber_file
    for akhiran in (".pdf", ".PDF"):
        if nama.endswith(akhiran):
            nama = nama[: -len(akhiran)]
            break

    tanggal = None
    m = _TANGGAL_DI_AWAL_RE.match(nama)
    if m:
        tanggal = m.group("tanggal")
        nama = nama[m.end() :]

    segmen = [s.strip() for s in nama.split(" - ") if s.strip()]
    if not segmen:
        return []

    segmen_mahasiswa = segmen[-1]
    nim = None
    nim_match = _NIM_DI_AKHIR_RE.search(segmen_mahasiswa)
    if nim_match:
        nim = nim_match.group("nim")
        segmen_mahasiswa = segmen_mahasiswa[: nim_match.start()].strip()

    prodi = next((s.upper() for s in segmen[:-1] if s.upper() in _KODE_PRODI_DIKENAL), None)

    return [
        Aktivitas(
            kategori="pendidikan.bimbingan_publikasi_ilmiah",
            dosen="",  # folder ini sudah per-dosen, tidak perlu diekstrak ulang dari nama file
            atribut={
                "nama_mahasiswa": segmen_mahasiswa,
                "nim": nim,
                "program_studi": prodi,
                "tanggal": tanggal,
            },
            sumber_file=sumber_file,
        )
    ]


# Semua metadata sudah ada di nama file -- pipeline cek atribut ini supaya
# tidak perlu download+ekstrak PDF sama sekali untuk kategori ini (lebih cepat).
parse.butuh_download = False
