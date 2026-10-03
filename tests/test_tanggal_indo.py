from agentdupak.tanggal_indo import parse_tanggal, rentang_bulan, tentukan_semester


def test_parse_tanggal_berbagai_format_bulan():
    assert parse_tanggal("13 Mei 2026").isoformat() == "2026-05-13"
    assert parse_tanggal("24 Des 2025").isoformat() == "2025-12-24"
    assert parse_tanggal("2 Oktober 2024").isoformat() == "2024-10-02"


def test_parse_tanggal_tidak_dikenali_mengembalikan_none():
    assert parse_tanggal(None) is None
    assert parse_tanggal("") is None
    assert parse_tanggal("bukan tanggal") is None


def test_semester_genap_februari_sampai_juli():
    import datetime

    for bulan in range(2, 8):
        label, tahun_ajaran = tentukan_semester(datetime.date(2025, bulan, 1))
        assert label == "Genap"
        assert tahun_ajaran == "2024/2025"


def test_semester_ganjil_agustus_sampai_januari():
    import datetime

    label, ta = tentukan_semester(datetime.date(2025, 8, 1))
    assert (label, ta) == ("Ganjil", "2025/2026")

    label, ta = tentukan_semester(datetime.date(2026, 1, 15))
    assert (label, ta) == ("Ganjil", "2025/2026")


def test_rentang_bulan_sesuai_konvensi_template_asli():
    assert rentang_bulan("Genap", "2024/2025") == "(Februari 2025 s/d Juli 2025)"
    assert rentang_bulan("Ganjil", "2024/2025") == "(Agustus 2024 s/d Januari 2025)"
