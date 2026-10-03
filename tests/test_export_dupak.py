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
            dosen="Test Dosen",
            atribut={"mata_kuliah": "Kecerdasan Buatan", "kelas": "IF 24 C", "sks": 4, "semester": "Genap", "tahun_ajaran": "2025/2026"},
            ak=4.0,
            sumber_file="JA Genap.pdf",
        ),
        Aktivitas(
            kategori="pendidikan.menguji",
            dosen="Test Dosen",
            atribut={"peran": "ketua", "nama_mahasiswa": "Reza", "npm": "21312101", "judul": "Judul singkat"},
            ak=1.0,
            sumber_file="Publikasi - Reza.pdf",
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


def test_generate_workbook_punya_2_sheet_dengan_formula_bukan_angka_statis(tmp_path, monkeypatch):
    dosen_id = _seed(tmp_path, monkeypatch)
    rows = db.get_aktivitas(dosen_id)

    wb = generate_workbook("Test Dosen", rows)

    assert wb.sheetnames == ["Ringkasan", "Detail"]

    ws_ringkasan = wb["Ringkasan"]
    # total ringkasan selalu formula SUM, bukan angka langsung
    nilai_formula = [c.value for row in ws_ringkasan.iter_rows() for c in row if isinstance(c.value, str) and c.value.startswith("=SUM(")]
    assert nilai_formula, "tidak ketemu formula SUM di sheet Ringkasan"

    ws_detail = wb["Detail"]
    assert ws_detail["A1"].value == "No"
    assert ws_detail["F1"].value == "AK"

    uraian_kolom_c = {row[1].value: row[2].value for row in ws_detail.iter_rows(min_row=2, max_row=1 + len(rows))}
    assert uraian_kolom_c["pendidikan.mengajar"] == "Kecerdasan Buatan (IF 24 C) -- 4 SKS -- Genap 2025/2026"

    # baris kategori yang belum ada rule tetap muncul dan ditandai, tidak disembunyikan
    status_perlu_review = [c.value for row in ws_detail.iter_rows() for c in row if c.value == "Perlu review"]
    assert len(status_perlu_review) == 1

    total_formula = [c.value for row in ws_detail.iter_rows() for c in row if isinstance(c.value, str) and c.value.startswith("=SUM(F")]
    assert total_formula == [f"=SUM(F2:F{len(rows) + 1})"]
