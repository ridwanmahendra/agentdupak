from agentdupak.pipeline import pilih_parser


def test_sk_mengajar_sesuai_forlap_dipilih():
    parser = pilih_parser(["SK Mengajar", "Sesuai Forlap"])
    assert parser is not None
    assert parser.__module__ == "agentdupak.parsers.sk_mengajar"


def test_sk_mengajar_sesuai_siakad_tidak_dipilih():
    """Siakad dan Forlap adalah representasi lain dari data mengajar yang SAMA --
    kalau keduanya ikut diparse, AK mengajar bakal double-counting."""
    assert pilih_parser(["SK Mengajar", "Sesuai Siakad"]) is None


def test_sk_penguji_dipilih():
    parser = pilih_parser(["SK Penguji", "Berita Acara Non Skripsi", "2025"])
    assert parser is not None
    assert parser.__module__ == "agentdupak.parsers.sk_penguji"


def test_folder_tanpa_parser_mengembalikan_none():
    assert pilih_parser(["SK Bimbingan", "2024-2025"]) is None
    assert pilih_parser(["Lembar Pengesahan", "2024"]) is None
