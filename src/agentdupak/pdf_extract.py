from __future__ import annotations

from pathlib import Path

from pypdf import PdfReader

# Di bawah ambang ini, dianggap PDF-nya hasil scan (gambar) tanpa text layer --
# ditemukan secara nyata pada dokumen "SK Penguji" dan "Lembar Pengesahan/Cover"
# yang ukurannya besar (ratusan KB - belasan MB) padahal isinya cuma beberapa
# halaman teks. pypdf mengembalikan string kosong untuk PDF semacam ini.
_AMBANG_TEKS_KOSONG = 50


def extract_text(pdf_path: str | Path) -> str:
    """Ekstrak teks dari PDF. Coba baca text layer asli dulu (cepat, akurat);
    kalau kosong/nyaris kosong (indikasi hasil scan), fallback ke OCR.

    OCR butuh dependency sistem yang tidak bisa dipasang lewat pip:
      - Debian/Ubuntu : apt install tesseract-ocr tesseract-ocr-ind poppler-utils
      - macOS         : brew install tesseract tesseract-lang poppler
    Hasil OCR dari dokumen ber-watermark cenderung berisik (karakter acak di
    sela-sela teks asli) -- parser yang membaca hasil OCR harus cari
    frasa/pola kunci, bukan mengandalkan teks yang 100% bersih.
    """
    reader = PdfReader(str(pdf_path))
    teks = "\n".join(page.extract_text() or "" for page in reader.pages)

    if len(teks.strip()) >= _AMBANG_TEKS_KOSONG:
        return teks

    return _ocr(pdf_path)


def _ocr(pdf_path: str | Path) -> str:
    from pdf2image import convert_from_path
    from pytesseract import image_to_string

    halaman = convert_from_path(str(pdf_path), dpi=200)
    return "\n".join(image_to_string(gambar, lang="ind+eng") for gambar in halaman)
