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
from agentdupak.parsers import sk_mengajar, sk_penguji

# nama folder (persis seperti di Drive) -> parser yang cocok
PARSER_BY_FOLDER = {
    "SK Mengajar": sk_mengajar.parse,
    "SK Penguji": sk_penguji.parse,
}


def pilih_parser(path: list[str]):
    for folder_name, parser in PARSER_BY_FOLDER.items():
        if folder_name in path:
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

            pdf_path = Path(tmp) / f"{f.id}.pdf"
            pdf_path.write_bytes(download_bytes(f.id))
            text = pdf_extract.extract_text(pdf_path)

            aktivitas = parser(text, sumber_file=f.title)
            if not aktivitas:
                log.append(f"[kosong] {label} -- parser tidak menemukan data, cek formatnya")
                continue

            semua_aktivitas += aktivitas
            log.append(f"[ok] {label} -- {len(aktivitas)} aktivitas")

    return semua_aktivitas, log
