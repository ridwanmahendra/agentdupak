"""Connector Google Drive: scan folder 'FTIK - DATA DOSEN/<nama dosen>/...' lalu
ekstrak teks tiap PDF, siap dilempar ke parser di agentdupak.parsers.

Setup (sekali saja, dilakukan sendiri -- ini akun Google Anda, bukan punya Claude):
  1. Buka https://console.cloud.google.com/ , buat project baru (atau pakai yang ada).
  2. Aktifkan "Google Drive API" untuk project itu.
  3. Buat kredensial OAuth client ID, tipe "Desktop app". Download sebagai
     credentials.json, letakkan di root project ini (JANGAN di-commit ke git --
     sudah ditambahkan ke .gitignore).
  4. Jalankan modul ini sekali secara interaktif -- browser akan terbuka minta
     login & izin akses Drive, lalu token disimpan di token.json supaya tidak
     perlu login ulang tiap kali.

Akun Google yang login harus punya akses lihat (viewer) ke folder
"FTIK - DATA DOSEN" -- sama seperti akses yang dipakai saat Anda share link
folder itu ke saya.

Pakai:
    python3 -m agentdupak.drive_sync <folder_id>
"""

from __future__ import annotations

import io
import sys
from dataclasses import dataclass
from pathlib import Path

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseDownload

SCOPES = ["https://www.googleapis.com/auth/drive.readonly"]
CREDENTIALS_FILE = Path("credentials.json")
TOKEN_FILE = Path("token.json")


@dataclass
class DriveFile:
    id: str
    title: str
    path: list[str]  # nama folder dari root sampai ke file ini, contoh:
    # ["Ridwan Mahenra", "SK Mengajar", "Sesuai Forlap"]


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


def _walk_folder(service, folder_id: str, path: list[str]) -> list[DriveFile]:
    """Rekursif susun daftar semua file PDF di bawah folder_id, dengan jejak path folder-nya."""
    results: list[DriveFile] = []
    page_token = None
    while True:
        response = (
            service.files()
            .list(
                q=f"'{folder_id}' in parents and trashed = false",
                fields="nextPageToken, files(id, name, mimeType)",
                pageToken=page_token,
            )
            .execute()
        )
        for item in response.get("files", []):
            if item["mimeType"] == "application/vnd.google-apps.folder":
                results += _walk_folder(service, item["id"], path + [item["name"]])
            elif item["mimeType"] == "application/pdf":
                results.append(DriveFile(id=item["id"], title=item["name"], path=path))
        page_token = response.get("nextPageToken")
        if not page_token:
            break
    return results


def list_pdfs(root_folder_id: str) -> list[DriveFile]:
    creds = _get_credentials()
    service = build("drive", "v3", credentials=creds)
    return _walk_folder(service, root_folder_id, path=[])


def download_pdf_bytes(file_id: str) -> bytes:
    creds = _get_credentials()
    service = build("drive", "v3", credentials=creds)
    request = service.files().get_media(fileId=file_id)
    buffer = io.BytesIO()
    downloader = MediaIoBaseDownload(buffer, request)
    done = False
    while not done:
        _, done = downloader.next_chunk()
    return buffer.getvalue()


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Pakai: python3 -m agentdupak.drive_sync <folder_id>")
        sys.exit(1)

    for f in list_pdfs(sys.argv[1]):
        print(" / ".join(f.path), "->", f.title, f"({f.id})")
