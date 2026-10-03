from agentdupak.parsers import sk_bimbingan
from agentdupak.rules.ak_rules import terapkan


def test_parse_nama_file_lengkap_dengan_tanggal_prodi_nim():
    hasil = sk_bimbingan.parse("", sumber_file="19 April 2025 - IF - Ridwan M - Aditya 18312043.pdf")

    assert len(hasil) == 1
    atribut = hasil[0].atribut
    assert atribut["nama_mahasiswa"] == "Aditya"
    assert atribut["nim"] == "18312043"
    assert atribut["program_studi"] == "IF"
    assert atribut["tanggal"] == "19 April 2025"


def test_parse_nama_file_minim_tanpa_tanggal_atau_nim():
    hasil = sk_bimbingan.parse("", sumber_file="RIDWAN MAHENDRA - KHOIRUN NIDA.pdf")

    assert len(hasil) == 1
    atribut = hasil[0].atribut
    assert atribut["nama_mahasiswa"] == "KHOIRUN NIDA"
    assert atribut["nim"] is None
    assert atribut["tanggal"] is None


def test_parse_urutan_segmen_dosen_sebelum_prodi():
    hasil = sk_bimbingan.parse(
        "", sumber_file="26 Juli 2025 - Ridwan Mahenra, S.Kom., M.Cs. (AI) - IF - Erick Yoga Res21312132.pdf"
    )

    assert len(hasil) == 1
    atribut = hasil[0].atribut
    assert atribut["nim"] == "21312132"
    assert atribut["program_studi"] == "IF"


def test_tidak_butuh_download_pdf():
    assert sk_bimbingan.parse.butuh_download is False


def test_ak_belum_ada_rule_ditandai_perlu_review_bukan_crash():
    """Kategori ini belum punya nilai AK resmi -- terapkan() tidak boleh
    melempar exception dan menghentikan seluruh sync gara-gara ini."""
    aktivitas = sk_bimbingan.parse("", sumber_file="RIDWAN MAHENDRA - KHOIRUN NIDA.pdf")
    hasil, peringatan = terapkan(aktivitas)

    assert hasil[0].ak == 0.0
    assert hasil[0].ak_perlu_review is True
    assert len(peringatan) == 1
    assert "pendidikan.bimbingan_publikasi_ilmiah" in peringatan[0]
