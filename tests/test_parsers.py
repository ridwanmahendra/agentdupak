from pathlib import Path

from agentdupak.parsers import sk_mengajar, sk_penguji
from agentdupak.rules.ak_rules import terapkan

FIXTURES = Path(__file__).parent / "fixtures"


def test_parse_sk_mengajar_mengembalikan_4_kelas_dengan_sks_benar():
    text = (FIXTURES / "sk_mengajar.txt").read_text()
    aktivitas = sk_mengajar.parse(text, sumber_file="sk_mengajar.txt")

    assert len(aktivitas) == 4
    assert [a.atribut["sks"] for a in aktivitas] == [4, 2, 3, 3]
    assert aktivitas[0].atribut["mata_kuliah"] == "Kecerdasan Buatan"
    assert aktivitas[0].atribut["kelas"] == "IF 24 C"
    assert aktivitas[0].atribut["tahun_ajaran"] == "2025/2026"
    assert aktivitas[0].atribut["semester"] == "Genap"
    assert "Ridwan Mahenra" in aktivitas[0].dosen


def test_hitung_ak_mengajar_sama_dengan_sks():
    text = (FIXTURES / "sk_mengajar.txt").read_text()
    aktivitas = terapkan(sk_mengajar.parse(text))

    assert sum(a.ak for a in aktivitas) == 4 + 2 + 3 + 3


def test_parse_sk_penguji_menangkap_peran_dan_data_mahasiswa():
    text = (FIXTURES / "sk_penguji_non_skripsi.txt").read_text()
    aktivitas = sk_penguji.parse(text, sumber_file="sk_penguji_non_skripsi.txt")

    assert len(aktivitas) == 1
    a = aktivitas[0]
    assert a.atribut["nama_mahasiswa"] == "Reza Pajriansyah"
    assert a.atribut["npm"] == "21312101"
    assert a.atribut["peran"] == "ketua"
    assert a.atribut["huruf_mutu"] == "A"


def test_hitung_ak_penguji_ketua_adalah_1():
    text = (FIXTURES / "sk_penguji_non_skripsi.txt").read_text()
    aktivitas = terapkan(sk_penguji.parse(text))

    assert aktivitas[0].ak == 1.0
