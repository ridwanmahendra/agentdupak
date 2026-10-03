from agentdupak.drive_common import DriveFile
from agentdupak.pipeline import proses


def test_aktivitas_dapat_sumber_url_dari_drive_file_id():
    files = [DriveFile(id="abc123", title="RIDWAN MAHENDRA - KHOIRUN NIDA.pdf", path=["SK Bimbingan"])]

    aktivitas, _ = proses(files, download_bytes=lambda fid: b"")

    assert len(aktivitas) == 1
    assert aktivitas[0].sumber_url == "https://drive.google.com/file/d/abc123/view"
