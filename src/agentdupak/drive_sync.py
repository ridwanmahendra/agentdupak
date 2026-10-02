"""Connector Google Drive untuk CLI: scan folder dosen lalu ekstrak teks tiap
PDF, siap dilempar ke parser di agentdupak.parsers.

Setup (sekali saja, dilakukan sendiri -- ini akun Google Anda, bukan punya Claude):
  1. Buka https://console.cloud.google.com/ , buat project baru (atau pakai yang ada).
  2. Aktifkan "Google Drive API" untuk project itu.
  3. Buat kredensial OAuth client ID, tipe "Desktop app". Download sebagai
     credentials.json, letakkan di root project ini (JANGAN di-commit ke git --
     sudah ditambahkan ke .gitignore).
  4. Jalankan modul ini sekali secara interaktif -- browser akan terbuka minta
     login & izin akses Drive, lalu token disimpan di token.json supaya tidak
     perlu login ulang tiap kali.

Akun Google yang login harus punya akses lihat (viewer) ke folder Drive yang
mau di-scan. credentials.json boleh dipakai bersama oleh beberapa dosen
(itu identitas aplikasi, bukan identitas login) -- token.json tetap personal
per orang yang login.

Untuk versi web (banyak dosen login sendiri-sendiri lewat browser tanpa
install apa pun), lihat src/agentdupak/webapp/.

Pakai:
    python3 -m agentdupak.drive_sync <folder_id>
"""

from __future__ import annotations

import sys
from pathlib import Path

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build

from agentdupak.drive_common import DriveFile, download_pdf_bytes, walk_pdfs

SCOPES = ["https://www.googleapis.com/auth/drive.readonly"]
CREDENTIALS_FILE = Path("credentials.json")
TOKEN_FILE = Path("token.json")


def _get_credentials() -> Credentials:
    creds: Credentials | None = None
    if TOKEN_FILE.exists():
        creds = Credentials.from_authorized_user_file(str(TOKEN_FILE), SCOPES)
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            if not CREDENTIALS_FILE.exists():
                raise FileNotFoundError(
                    f"{CREDENTIALS_FILE} tidak ditemukan. Lihat docstring modul ini "
                    "untuk cara membuatnya di Google Cloud Console."
                )
            flow = InstalledAppFlow.from_client_secrets_file(str(CREDENTIALS_FILE), SCOPES)
            creds = flow.run_local_server(port=0)
        TOKEN_FILE.write_text(creds.to_json())
    return creds


def list_pdfs(root_folder_id: str) -> list[DriveFile]:
    creds = _get_credentials()
    service = build("drive", "v3", credentials=creds)
    return walk_pdfs(service, root_folder_id)


def download_pdf(file_id: str) -> bytes:
    creds = _get_credentials()
    service = build("drive", "v3", credentials=creds)
    return download_pdf_bytes(service, file_id)


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Pakai: python3 -m agentdupak.drive_sync <folder_id>")
        sys.exit(1)

    for f in list_pdfs(sys.argv[1]):
        print(" / ".join(f.path), "->", f.title, f"({f.id})")
