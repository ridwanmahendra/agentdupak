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


def test_sk_bimbingan_dipilih():
    parser = pilih_parser(["SK Bimbingan", "2024-2025", "Genap"])
    assert parser is not None
    assert parser.__module__ == "agentdupak.parsers.sk_bimbingan"


def test_folder_tanpa_parser_mengembalikan_none():
    assert pilih_parser(["Lembar Pengesahan", "2024"]) is None
    assert pilih_parser(["Cover", "2024"]) is None


def test_proses_skip_download_untuk_parser_yang_tidak_butuh():
    from agentdupak.drive_common import DriveFile
    from agentdupak.pipeline import proses

    files = [DriveFile(id="abc", title="RIDWAN MAHENDRA - KHOIRUN NIDA.pdf", path=["SK Bimbingan"])]

    dipanggil = []

    def download_bytes_harus_tidak_dipanggil(file_id):
        dipanggil.append(file_id)
        raise AssertionError("download_bytes tidak boleh dipanggil untuk SK Bimbingan")

    aktivitas, log = proses(files, download_bytes=download_bytes_harus_tidak_dipanggil)

    assert dipanggil == []
    assert len(aktivitas) == 1
    assert "[ok]" in log[0]
