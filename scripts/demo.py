"""Demo: parse fixture dokumen asli -> aktivitas -> hitung AK.

Jalankan dari root project:
    PYTHONPATH=src python3 scripts/demo.py
"""

from pathlib import Path

from agentdupak.parsers import sk_mengajar, sk_penguji
from agentdupak.rules.ak_rules import terapkan

FIXTURES = Path(__file__).parent.parent / "tests" / "fixtures"


def main() -> None:
    mengajar_text = (FIXTURES / "sk_mengajar.txt").read_text()
    penguji_text = (FIXTURES / "sk_penguji_non_skripsi.txt").read_text()

    aktivitas = sk_mengajar.parse(mengajar_text, sumber_file="sk_mengajar.txt")
    aktivitas += sk_penguji.parse(penguji_text, sumber_file="sk_penguji_non_skripsi.txt")

    terapkan(aktivitas)

    total_ak = 0.0
    for a in aktivitas:
        print(f"[{a.kategori}] {a.dosen} -> AK = {a.ak}")
        print(f"    atribut: {a.atribut}")
        total_ak += a.ak

    print(f"\nTotal AK dari {len(aktivitas)} aktivitas: {total_ak}")


if __name__ == "__main__":
    main()
