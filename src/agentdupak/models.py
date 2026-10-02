from dataclasses import dataclass, field
from typing import Any


@dataclass
class Aktivitas:
    """Satu baris aktivitas DUPAK hasil parsing, sebelum dihitung AK-nya."""

    kategori: str  # contoh: "pendidikan.mengajar", "pendidikan.menguji"
    dosen: str
    atribut: dict[str, Any] = field(default_factory=dict)
    sumber_file: str = ""
    ak: float | None = None  # diisi oleh rules engine, bukan oleh parser
