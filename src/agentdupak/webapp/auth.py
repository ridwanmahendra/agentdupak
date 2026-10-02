"""Login Google OAuth untuk web app (beda dari drive_sync.py yang CLI/Desktop flow).

Butuh OAuth client tipe "Web application" (bukan "Desktop app") di Google
Cloud Console, dengan Authorized redirect URI: http://localhost:8000/auth/callback
(ganti domainnya saat deploy). GOOGLE_CLIENT_ID dan GOOGLE_CLIENT_SECRET
diambil dari environment variable -- jangan hardcode di kode.
"""

from __future__ import annotations

import os

from authlib.integrations.starlette_client import OAuth

SCOPES = "openid email profile https://www.googleapis.com/auth/drive.readonly"

oauth = OAuth()
oauth.register(
    name="google",
    client_id=os.environ.get("GOOGLE_CLIENT_ID"),
    client_secret=os.environ.get("GOOGLE_CLIENT_SECRET"),
    server_metadata_url="https://accounts.google.com/.well-known/openid-configuration",
    client_kwargs={"scope": SCOPES},
)
