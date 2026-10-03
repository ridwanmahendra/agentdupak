"""Generate rekap Excel dari aktivitas tersimpan -- bukan isi ulang template
DUPAK OK aslinya (banyak merged cell & struktur manual per baris yang rapuh
untuk digenerate otomatis), tapi rekap bersih per aktivitas + total per
kategori, siap jadi lampiran atau acuan transkripsi manual ke form resmi.
"""

from __future__ import annotations

import json
from typing import Callable

from openpyxl import Workbook
from openpyxl.styles import Alignment, Font, PatternFill
from openpyxl.utils import get_column_letter
from openpyxl.worksheet.worksheet import Worksheet

FONT_NORMAL = Font(name="Arial", size=10)
FONT_HEADER = Font(name="Arial", size=10, bold=True, color="FFFFFF")
FONT_TOTAL = Font(name="Arial", size=10, bold=True)
FILL_HEADER = PatternFill(start_color="1F4E78", end_color="1F4E78", fill_type="solid")


def _uraian_mengajar(atribut: dict) -> str:
    return (
        f"{atribut.get('mata_kuliah', '?')} ({atribut.get('kelas', '?')}) "
        f"-- {atribut.get('sks', '?')} SKS -- {atribut.get('semester', '?')} {atribut.get('tahun_ajaran', '?')}"
    )


def _uraian_menguji(atribut: dict) -> str:
    peran = atribut.get("peran", "?")
    judul = atribut.get("judul") or ""
    judul_singkat = judul if len(judul) <= 70 else judul[:67] + "..."
    return f"Penguji {peran} -- {atribut.get('nama_mahasiswa', '?')} ({atribut.get('npm', '?')}) -- {judul_singkat}"


def _uraian_bimbingan(atribut: dict) -> str:
    return f"Pembimbing -- {atribut.get('nama_mahasiswa', '?')} ({atribut.get('nim') or '-'})"


_URAIAN_BY_KATEGORI: dict[str, Callable[[dict], str]] = {
    "pendidikan.mengajar": _uraian_mengajar,
    "pendidikan.menguji": _uraian_menguji,
    "pendidikan.bimbingan_publikasi_ilmiah": _uraian_bimbingan,
}


def _uraian(kategori: str, atribut_json: str) -> str:
    atribut = json.loads(atribut_json)
    formatter = _URAIAN_BY_KATEGORI.get(kategori)
    if formatter:
        return formatter(atribut)
    return json.dumps(atribut, ensure_ascii=False)


def _tanggal(kategori: str, atribut_json: str) -> str:
    atribut = json.loads(atribut_json)
    return atribut.get("tanggal") or atribut.get("semester") or ""


def _set_lebar_kolom(ws: Worksheet, lebar: dict[int, int]) -> None:
    for kolom, w in lebar.items():
        ws.column_dimensions[get_column_letter(kolom)].width = w


def generate_workbook(dosen_nama: str, aktivitas_rows) -> Workbook:
    """aktivitas_rows: hasil db.get_aktivitas() -- list sqlite3.Row dengan
    kolom kategori, atribut_json, ak, ak_perlu_review, sumber_file."""
    wb = Workbook()

    # --- Sheet 1: Ringkasan per kategori ---
    ws_ringkasan = wb.active
    ws_ringkasan.title = "Ringkasan"
    ws_ringkasan["A1"] = f"Rekap Angka Kredit -- {dosen_nama}"
    ws_ringkasan["A1"].font = Font(name="Arial", size=12, bold=True)

    kategori_unik = sorted({row["kategori"] for row in aktivitas_rows})
    header_row = 3
    ws_ringkasan.cell(row=header_row, column=1, value="Kategori").font = FONT_HEADER
    ws_ringkasan.cell(row=header_row, column=2, value="Jumlah Aktivitas").font = FONT_HEADER
    ws_ringkasan.cell(row=header_row, column=3, value="Total AK").font = FONT_HEADER
    for col in (1, 2, 3):
        ws_ringkasan.cell(row=header_row, column=col).fill = FILL_HEADER

    baris = header_row + 1
    for kategori in kategori_unik:
        ws_ringkasan.cell(row=baris, column=1, value=kategori).font = FONT_NORMAL
        # dihitung lewat formula yang merujuk sheet Detail, bukan angka hardcode,
        # supaya tetap benar kalau nanti baris Detail diedit manual
        ws_ringkasan.cell(
            row=baris, column=2, value=f'=COUNTIF(Detail!B:B,A{baris})'
        ).font = FONT_NORMAL
        ws_ringkasan.cell(
            row=baris, column=3, value=f'=SUMIF(Detail!B:B,A{baris},Detail!F:F)'
        ).font = FONT_NORMAL
        baris += 1

    ws_ringkasan.cell(row=baris, column=1, value="TOTAL").font = FONT_TOTAL
    ws_ringkasan.cell(row=baris, column=3, value=f"=SUM(C{header_row + 1}:C{baris - 1})").font = FONT_TOTAL
    _set_lebar_kolom(ws_ringkasan, {1: 42, 2: 18, 3: 12})

    # --- Sheet 2: Detail per aktivitas ---
    ws_detail = wb.create_sheet("Detail")
    kolom = ["No", "Kategori", "Uraian", "Tanggal/Semester", "Sumber File (Bukti)", "AK", "Status"]
    for i, judul in enumerate(kolom, start=1):
        c = ws_detail.cell(row=1, column=i, value=judul)
        c.font = FONT_HEADER
        c.fill = FILL_HEADER

    for i, row in enumerate(aktivitas_rows, start=1):
        r = i + 1
        ws_detail.cell(row=r, column=1, value=i).font = FONT_NORMAL
        ws_detail.cell(row=r, column=2, value=row["kategori"]).font = FONT_NORMAL
        ws_detail.cell(row=r, column=3, value=_uraian(row["kategori"], row["atribut_json"])).font = FONT_NORMAL
        ws_detail.cell(row=r, column=4, value=_tanggal(row["kategori"], row["atribut_json"])).font = FONT_NORMAL
        ws_detail.cell(row=r, column=5, value=row["sumber_file"]).font = FONT_NORMAL
        ws_detail.cell(row=r, column=6, value=row["ak"]).font = FONT_NORMAL
        status = "Perlu review" if row["ak_perlu_review"] else "Terverifikasi"
        ws_detail.cell(row=r, column=7, value=status).font = FONT_NORMAL

    total_row = len(aktivitas_rows) + 2
    ws_detail.cell(row=total_row, column=5, value="TOTAL").font = FONT_TOTAL
    ws_detail.cell(row=total_row, column=6, value=f"=SUM(F2:F{total_row - 1})").font = FONT_TOTAL

    _set_lebar_kolom(ws_detail, {1: 5, 2: 36, 3: 60, 4: 18, 5: 36, 6: 8, 7: 14})
    for row in ws_detail.iter_rows(min_row=2, max_row=total_row, min_col=1, max_col=7):
        for cell in row:
            cell.alignment = Alignment(wrap_text=True, vertical="top")

    return wb
