import re

from agentdupak.models import Aktivitas

MAHASISWA_RE = re.compile(r"Nama Mahasiswa\s*:\s*(?P<nama>.+)")
NPM_RE = re.compile(r"NPM\s*:\s*(?P<npm>\d+)")
PEMBIMBING_RE = re.compile(r"Pembimbing\s*:\s*(?P<pembimbing>.+)")
JUDUL_RE = re.compile(r"Judul Publikasi Karya Ilmiah\s*:\s*(?P<judul>.+)")
NOMOR_BA_RE = re.compile(r"BERITA ACARA\s+.*?NOMOR\s*:\s*(?P<nomor>\S+)", re.IGNORECASE | re.DOTALL)
TANGGAL_RE = re.compile(
    r"Pada hari ini \w+,\s*(?P<tanggal>\d{1,2} \w+ \d{4})"
)
PERAN_RE = re.compile(r"penguji\s+(?P<peran>ketua|anggota)", re.IGNORECASE)
LULUS_RE = re.compile(r"huruf mutu\s*(?P<huruf_mutu>[A-E][+-]?)", re.IGNORECASE)
# nama penguji selalu ada di blok tanda tangan: "Penguji Ketua,\n\n<Nama>"
SIGNATORY_RE = re.compile(
    r"Penguji (?:Ketua|Anggota),\s*\n+\s*(?P<nama>.+)", re.IGNORECASE
)


def parse(text: str, sumber_file: str = "") -> list[Aktivitas]:
    """Parse Berita Acara ujian/diseminasi non-skripsi jadi 1 aktivitas 'menguji'."""
    mahasiswa = MAHASISWA_RE.search(text)
    npm = NPM_RE.search(text)
    pembimbing = PEMBIMBING_RE.search(text)
    judul = JUDUL_RE.search(text)
    nomor_ba = NOMOR_BA_RE.search(text)
    tanggal = TANGGAL_RE.search(text)
    peran = PERAN_RE.search(text)
    huruf_mutu = LULUS_RE.search(text)
    signatory = SIGNATORY_RE.search(text)

    if not mahasiswa:
        return []

    dosen = signatory.group("nama").strip() if signatory else (
        pembimbing.group("pembimbing").strip() if pembimbing else ""
    )

    return [
        Aktivitas(
            kategori="pendidikan.menguji",
            dosen=dosen,
            atribut={
                "nama_mahasiswa": mahasiswa.group("nama").strip(),
                "npm": npm.group("npm") if npm else None,
                "pembimbing": pembimbing.group("pembimbing").strip() if pembimbing else None,
                "judul": judul.group("judul").strip() if judul else None,
                "nomor_berita_acara": nomor_ba.group("nomor") if nomor_ba else None,
                "tanggal": tanggal.group("tanggal") if tanggal else None,
                "peran": peran.group("peran").lower() if peran else None,
                "huruf_mutu": huruf_mutu.group("huruf_mutu") if huruf_mutu else None,
            },
            sumber_file=sumber_file,
        )
    ]
