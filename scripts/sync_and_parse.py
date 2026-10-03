"""End-to-end (CLI): scan folder dosen di Drive -> ekstrak PDF -> parse -> hitung AK.

Pakai:
    PYTHONPATH=src python3 scripts/sync_and_parse.py <folder_id_dosen>
"""

import sys

from agentdupak import drive_sync
from agentdupak.pipeline import proses
from agentdupak.rules.ak_rules import terapkan


def main(folder_id: str) -> None:
    files = drive_sync.list_pdfs(folder_id)
    print(f"Ditemukan {len(files)} file PDF.\n")

    aktivitas, log = proses(files, download_bytes=drive_sync.download_pdf)
    for line in log:
        print(line)

    _, peringatan = terapkan(aktivitas)
    total = sum(a.ak for a in aktivitas)
    print(f"\nTotal {len(aktivitas)} aktivitas, {total} AK")
    for p in sorted(set(peringatan)):
        print(f"PERINGATAN: {p}")


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Pakai: PYTHONPATH=src python3 scripts/sync_and_parse.py <folder_id_dosen>")
        sys.exit(1)
    main(sys.argv[1])
