from agentdupak.export_dupak import generate_workbook
from agentdupak.webapp import db
from agentdupak.models import Aktivitas


def _seed(tmp_path, monkeypatch):
    monkeypatch.setattr(db, "DB_PATH", tmp_path / "test.db")
    db.init_db()
    dosen_id = db.upsert_dosen("test@x.com", "Test Dosen", None)
    aktivitas = [
        Aktivitas(
            kategori="pendidikan.mengajar",
            dosen="",
            atribut={"mata_kuliah": "Kecerdasan Buatan", "kelas": "IF 24 C", "sks": 4, "semester": "Genap", "tahun_ajaran": "2025/2026"},
            ak=4.0,
            sumber_file="JA Genap.pdf",
            sumber_url="https://drive.google.com/file/d/abc123/view",
        ),
        Aktivitas(
            kategori="pendidikan.mengajar",
            dosen="",
            atribut={"mata_kuliah": "Sistem Pakar", "kelas": "IF GAB", "sks": 2, "semester": "Genap", "tahun_ajaran": "2025/2026"},
            ak=2.0,
            sumber_file="JA Genap.pdf",
            sumber_url="https://drive.google.com/file/d/abc123/view",
        ),
        Aktivitas(
            kategori="pendidikan.menguji",
            dosen="",
            atribut={"peran": "ketua", "nama_mahasiswa": "Reza", "npm": "21312101", "tanggal": "13 Mei 2026", "judul": "x"},
            ak=1.0,
            sumber_file="Publikasi - Reza.pdf",
        ),
        Aktivitas(
            kategori="pendidikan.bimbingan_publikasi_ilmiah",
            dosen="",
            atribut={"nama_mahasiswa": "Khoirun Nida", "nim": None, "tanggal": None},
            ak=1.0,
            sumber_file="RIDWAN - KHOIRUN NIDA.pdf",
        ),
        Aktivitas(
            kategori="kategori.belum.ada.rule",
            dosen="",
            atribut={},
            ak=0.0,
            ak_perlu_review=True,
            sumber_file="entah.pdf",
        ),
    ]
    db.replace_aktivitas(dosen_id, aktivitas, ["[ok] test"])
    return dosen_id


def _semua_sel(ws):
    return {c.coordinate: c.value for row in ws.iter_rows() for c in row if c.value is not None}


def test_generate_workbook_meniru_struktur_sheet_pendidikan_asli(tmp_path, monkeypatch):
    dosen_id = _seed(tmp_path, monkeypatch)
    rows = db.get_aktivitas(dosen_id)

    wb = generate_workbook("Test Dosen", rows)

    assert "PENDIDIKAN" in wb.sheetnames
    # kategori yang belum ada parser/rule ditaruh di sheet terpisah, bukan hilang
    assert "Belum Terpetakan" in wb.sheetnames

    ws = wb["PENDIDIKAN"]
    sel = _semua_sel(ws)

    # judul & header kolom gaya form resmi
    assert sel["A1"] == "SURAT PERNYATAAN"
    assert sel["A2"] == "MELAKSANAKAN PENDIDIKAN"
    assert "Jumlah\nAngka\nKredit" in sel.values()

    # 2 kelas mengajar semester yang sama digabung 1 sub total per semester
    uraian_d = [v for k, v in sel.items() if k.startswith("D") and isinstance(v, str) and "Kecerdasan" in v]
    assert uraian_d == ["Kecerdasan Buatan (IF 24 C)"]
    subtotal_formula = [v for v in sel.values() if isinstance(v, str) and v.startswith("=SUM(J")]
    assert subtotal_formula, "sub total per semester (volume SKS) tidak ketemu"

    # mahasiswa bimbingan & menguji masing-masing muncul dengan label sub-kategorinya
    assert any("Laporan akhir studi" in str(v) for v in sel.values())
    assert any(v == "c. Skripsi" for v in sel.values())
    assert any("Khoirun Nida" in str(v) for v in sel.values())
    assert any("Reza" in str(v) for v in sel.values())

    # grand total menjumlahkan 3 kategori via formula, bukan angka hardcode
    grand_total = [v for v in sel.values() if isinstance(v, str) and v.count("+L") == 2 and v.startswith("=L")]
    assert grand_total, "formula total keseluruhan tidak ketemu"

    ws_lain = wb["Belum Terpetakan"]
    baris_lain = [tuple(c.value for c in row) for row in ws_lain.iter_rows(min_row=2)]
    assert baris_lain == [("kategori.belum.ada.rule", "entah.pdf", 0.0)]


def test_generate_workbook_hyperlink_border_dan_merge_tanggal(tmp_path, monkeypatch):
    dosen_id = _seed(tmp_path, monkeypatch)
    rows = db.get_aktivitas(dosen_id)

    wb = generate_workbook("Test Dosen", rows)
    ws = wb["PENDIDIKAN"]

    # "Link Lampiran" jadi hyperlink beneran ke sumber_url, bukan sekadar teks
    sel_link = [c for row in ws.iter_rows() for c in row if c.value == "Link Lampiran"]
    assert sel_link, "tidak ketemu cell 'Link Lampiran'"
    assert all(c.hyperlink is not None for c in sel_link)
    assert all(c.hyperlink.target == "https://drive.google.com/file/d/abc123/view" for c in sel_link)

    # 2 kelas mengajar di semester yang sama -> 1 sel Tanggal merge vertikal
    rentang_merge = [str(r) for r in ws.merged_cells.ranges]
    assert any(r.startswith("H") and ":H" in r for r in rentang_merge), f"tidak ketemu merge kolom H (Tanggal): {rentang_merge}"

    # area tabel punya border grid di semua sisi
    header_cell = ws["A7"]
    assert header_cell.border.left.style == "thin"
    assert header_cell.border.bottom.style == "thin"


def test_generate_workbook_tanpa_aktivitas_tidak_error(tmp_path, monkeypatch):
    monkeypatch.setattr(db, "DB_PATH", tmp_path / "kosong.db")
    db.init_db()
    dosen_id = db.upsert_dosen("kosong@x.com", "Dosen Kosong", None)

    wb = generate_workbook("Dosen Kosong", db.get_aktivitas(dosen_id))

    assert wb.sheetnames == ["PENDIDIKAN"]
