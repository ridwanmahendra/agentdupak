from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass
class Aktivitas:
    """Satu baris aktivitas DUPAK hasil parsing, sebelum dihitung AK-nya."""

    kategori: str  # contoh: "pendidikan.mengajar", "pendidikan.menguji"
    dosen: str
    atribut: dict[str, Any] = field(default_factory=dict)
    sumber_file: str = ""
    sumber_url: str | None = None  # link Google Drive ke dokumen asli, kalau ada (untuk "Link Lampiran")
    ak: float | None = None  # diisi oleh rules engine, bukan oleh parser
    ak_perlu_review: bool = False  # True kalau kategorinya belum punya aturan AK resmi
