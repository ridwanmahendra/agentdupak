"""Logic Drive API yang dipakai bersama oleh drive_sync.py (CLI, credentials.json)
dan webapp/drive_web.py (web, access token dari sesi login) -- bedanya cuma
cara membuat objek `service`, bukan cara jalan-jalan di foldernya.
"""

from __future__ import annotations

import io
from dataclasses import dataclass

from googleapiclient.http import MediaIoBaseDownload


@dataclass
class DriveFile:
    id: str
    title: str
    path: list[str]  # nama folder dari root sampai ke file ini


def walk_pdfs(service, folder_id: str, path: list[str] | None = None) -> list[DriveFile]:
    """Rekursif susun daftar semua file PDF di bawah folder_id, dengan jejak path folder-nya."""
    path = path or []
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
                results += walk_pdfs(service, item["id"], path + [item["name"]])
            elif item["mimeType"] == "application/pdf":
                results.append(DriveFile(id=item["id"], title=item["name"], path=path))
        page_token = response.get("nextPageToken")
        if not page_token:
            break
    return results


def download_pdf_bytes(service, file_id: str) -> bytes:
    request = service.files().get_media(fileId=file_id)
    buffer = io.BytesIO()
    downloader = MediaIoBaseDownload(buffer, request)
    done = False
    while not done:
        _, done = downloader.next_chunk()
    return buffer.getvalue()
