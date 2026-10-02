from __future__ import annotations

from pathlib import Path

from pypdf import PdfReader


def extract_text(pdf_path: str | Path) -> str:
    """Ekstrak teks dari PDF 'teks asli' (bukan hasil scan/gambar).

    Untuk dokumen seperti SK Mengajar / Berita Acara Penguji yang dibuat dari
    Word/aplikasi office, ini cukup -- tidak perlu OCR. Untuk dokumen hasil
    scan (Lembar Pengesahan, Cover skripsi lama) hasilnya akan kosong atau
    sangat buruk; itu butuh jalur OCR terpisah (lihat README).
    """
    reader = PdfReader(str(pdf_path))
    return "\n".join(page.extract_text() or "" for page in reader.pages)
