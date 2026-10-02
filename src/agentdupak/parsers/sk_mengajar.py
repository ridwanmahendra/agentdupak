from __future__ import annotations

import re

from agentdupak.models import Aktivitas

HEADER_RE = re.compile(
    r"SEMESTER\s+(?P<semester>GENAP|GANJIL)\s+TAHUN\s+AKADEMIK\s+(?P<tahun_ajaran>\d{4}/\d{4})",
    re.IGNORECASE,
)
DOSEN_RE = re.compile(r"Nama Dosen\s*:\s*(?P<dosen>.+)")
ROW_RE = re.compile(
    r"^\d+\s+(?P<mk>.+?)\s+(?P<sks>\d+)\s+(?P<kelas>[A-Z0-9]+(?:\s+[A-Z0-9]+)*?)\s+(?P<prodi>S\d\s+\S+.*)$"
)


def parse(text: str, sumber_file: str = "") -> list[Aktivitas]:
    """Parse SK Penugasan Mengajar (format 'JA <tahun> <semester>') jadi daftar aktivitas mengajar per kelas."""
    header = HEADER_RE.search(text)
    semester = header.group("semester").capitalize() if header else None
    tahun_ajaran = header.group("tahun_ajaran") if header else None

    dosen_match = DOSEN_RE.search(text)
    dosen = dosen_match.group("dosen").strip() if dosen_match else ""

    aktivitas: list[Aktivitas] = []
    for line in text.splitlines():
        line = line.strip()
        row = ROW_RE.match(line)
        if not row:
            continue
        aktivitas.append(
            Aktivitas(
                kategori="pendidikan.mengajar",
                dosen=dosen,
                atribut={
                    "mata_kuliah": row.group("mk").strip(),
                    "sks": int(row.group("sks")),
                    "kelas": row.group("kelas").strip(),
                    "program_studi": row.group("prodi").strip(),
                    "tahun_ajaran": tahun_ajaran,
                    "semester": semester,
                },
                sumber_file=sumber_file,
            )
        )
    return aktivitas
