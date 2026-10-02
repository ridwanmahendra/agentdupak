"""Operasi Drive API versi web: pakai access token dari sesi login (bukan
credentials.json/token.json di disk seperti drive_sync.py yang CLI).
"""

from __future__ import annotations

from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build

from agentdupak.drive_common import DriveFile, download_pdf_bytes, walk_pdfs

__all__ = ["DriveFile", "list_shared_folders", "walk_pdfs_for_user", "download_pdf_for_user"]


def _service(access_token: str):
    creds = Credentials(token=access_token)
    return build("drive", "v3", credentials=creds)


def list_shared_folders(access_token: str) -> list[dict]:
    """Folder yang di-share ke user yang sedang login -- ini yang dipilih user
    sebagai folder dosen miliknya sendiri (biasanya 1 folder dari BAAK fakultas)."""
    service = _service(access_token)
    response = (
        service.files()
        .list(
            q="sharedWithMe = true and mimeType = 'application/vnd.google-apps.folder' and trashed = false",
            fields="files(id, name)",
        )
        .execute()
    )
    return response.get("files", [])


def walk_pdfs_for_user(access_token: str, folder_id: str) -> list[DriveFile]:
    return walk_pdfs(_service(access_token), folder_id)


def download_pdf_for_user(access_token: str, file_id: str) -> bytes:
    return download_pdf_bytes(_service(access_token), file_id)
