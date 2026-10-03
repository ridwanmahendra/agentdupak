"""Pipeline: daftar DriveFile -> download -> ekstrak teks -> parse -> Aktivitas.

Dipakai bersama oleh scripts/sync_and_parse.py (CLI) dan webapp (per-request
dari browser) supaya logicnya cuma ditulis sekali.
"""

from __future__ import annotations

import tempfile
from pathlib import Path
from typing import Callable

from agentdupak import pdf_extract
from agentdupak.drive_common import DriveFile
from agentdupak.models import Aktivitas
from agentdupak.parsers import sk_bimbingan, sk_mengajar, sk_penguji

# (folder yang harus ADA di path, folder yang harus TIDAK ADA di path, parser)
#
# "SK Mengajar/Sesuai Forlap" sengaja wajib persis itu, bukan cuma "SK Mengajar":
# di Drive asli ada folder sodara "SK Mengajar/Sesuai Siakad" yang isinya
# representasi lain dari data mengajar yang SAMA (SIAKAD vs Forlap PDDikti).
# Kalau keduanya ikut diparse, AK mengajar bakal double-counting. Forlap yang
# dipakai karena itu sumber resmi untuk pelaporan ke LLDIKTI.
PARSER_RULES: list[tuple[list[str], list[str], object]] = [
    (["SK Mengajar", "Sesuai Forlap"], ["Sesuai Siakad"], sk_mengajar.parse),
    (["SK Penguji"], [], sk_penguji.parse),
    (["SK Bimbingan"], [], sk_bimbingan.parse),
]


def pilih_parser(path: list[str]):
    for wajib_ada, wajib_tidak_ada, parser in PARSER_RULES:
        if all(f in path for f in wajib_ada) and not any(f in path for f in wajib_tidak_ada):
            return parser
    return None


def proses(
    files: list[DriveFile], download_bytes: Callable[[str], bytes]
) -> tuple[list[Aktivitas], list[str]]:
    """Jalankan pipeline untuk semua file. Kembalikan (aktivitas, log_per_file)."""
    semua_aktivitas: list[Aktivitas] = []
    log: list[str] = []

    with tempfile.TemporaryDirectory() as tmp:
        for f in files:
            label = f"{' / '.join(f.path)} / {f.title}"
            parser = pilih_parser(f.path)
            if parser is None:
                log.append(f"[skip] {label} -- belum ada parser untuk folder ini")
                continue

            if getattr(parser, "butuh_download", True):
                pdf_path = Path(tmp) / f"{f.id}.pdf"
                pdf_path.write_bytes(download_bytes(f.id))
                text = pdf_extract.extract_text(pdf_path)
            else:
                text = ""  # parser ini baca nama file saja, lihat sk_bimbingan.py

            aktivitas = parser(text, sumber_file=f.title)
            if not aktivitas:
                log.append(f"[kosong] {label} -- parser tidak menemukan data, cek formatnya")
                continue

            semua_aktivitas += aktivitas
            log.append(f"[ok] {label} -- {len(aktivitas)} aktivitas")

    return semua_aktivitas, log
