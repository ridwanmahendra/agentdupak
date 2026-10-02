"""End-to-end: scan folder dosen di Drive -> ekstrak PDF -> parse -> hitung AK.

Baru menangani 2 jenis dokumen (lihat README). File lain akan dilewati dengan
peringatan, bukan error, supaya 1 dokumen aneh tidak menghentikan seluruh sync.

Pakai:
    PYTHONPATH=src python3 scripts/sync_and_parse.py <folder_id_dosen>
"""

import sys
import tempfile
from pathlib import Path

from agentdupak import drive_sync, pdf_extract
from agentdupak.parsers import sk_mengajar, sk_penguji
from agentdupak.rules.ak_rules import terapkan

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


def main(folder_id: str) -> None:
    files = drive_sync.list_pdfs(folder_id)
    print(f"Ditemukan {len(files)} file PDF.\n")

    semua_aktivitas = []
    with tempfile.TemporaryDirectory() as tmp:
        for f in files:
            parser = pilih_parser(f.path)
            if parser is None:
                print(f"[skip] {' / '.join(f.path)} / {f.title} -- belum ada parser untuk folder ini")
                continue

            pdf_path = Path(tmp) / f"{f.id}.pdf"
            pdf_path.write_bytes(drive_sync.download_pdf_bytes(f.id))
            text = pdf_extract.extract_text(pdf_path)

            aktivitas = parser(text, sumber_file=f.title)
            if not aktivitas:
                print(f"[kosong] {' / '.join(f.path)} / {f.title} -- parser tidak menemukan data, cek formatnya")
                continue

            semua_aktivitas += aktivitas
            print(f"[ok] {' / '.join(f.path)} / {f.title} -- {len(aktivitas)} aktivitas")

    terapkan(semua_aktivitas)
    total = sum(a.ak for a in semua_aktivitas)
    print(f"\nTotal {len(semua_aktivitas)} aktivitas, {total} AK")


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Pakai: PYTHONPATH=src python3 scripts/sync_and_parse.py <folder_id_dosen>")
        sys.exit(1)
    main(sys.argv[1])
