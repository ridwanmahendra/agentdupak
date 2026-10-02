"""Web app DUPAK: dosen login dengan Google, pilih folder Drive miliknya,
klik sync, lihat aktivitas + total AK -- tanpa install apa pun di sisi dosen.

Jalankan (lihat README untuk setup OAuth client "Web application"):
    GOOGLE_CLIENT_ID=... GOOGLE_CLIENT_SECRET=... SESSION_SECRET=... \
        uvicorn agentdupak.webapp.main:app --reload
"""

from __future__ import annotations

import os

from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from starlette.middleware.sessions import SessionMiddleware

from agentdupak.rules.ak_rules import terapkan
from agentdupak.webapp import db, drive_web
from agentdupak.webapp.auth import oauth

TEMPLATES_DIR = os.path.join(os.path.dirname(__file__), "templates")

app = FastAPI()
app.add_middleware(SessionMiddleware, secret_key=os.environ["SESSION_SECRET"])
templates = Jinja2Templates(directory=TEMPLATES_DIR)

db.init_db()


def _current_dosen(request: Request):
    email = request.session.get("email")
    if not email:
        return None
    return db.get_dosen_by_email(email)


@app.get("/", response_class=HTMLResponse)
async def index(request: Request):
    dosen = _current_dosen(request)
    if not dosen:
        return templates.TemplateResponse(request, "login.html", {})

    if not dosen["drive_folder_id"]:
        access_token = request.session.get("access_token")
        folders = drive_web.list_shared_folders(access_token) if access_token else []
        return templates.TemplateResponse(
            request, "pilih_folder.html", {"dosen": dosen, "folders": folders}
        )

    aktivitas = db.get_aktivitas(dosen["id"])
    total_ak = sum(a["ak"] for a in aktivitas)
    sync_log = request.session.pop("sync_log", None)
    return templates.TemplateResponse(
        request,
        "dashboard.html",
        {
            "dosen": dosen,
            "aktivitas": aktivitas,
            "total_ak": total_ak,
            "sync_log": sync_log,
        },
    )


@app.get("/auth/login")
async def login(request: Request):
    redirect_uri = request.url_for("auth_callback")
    return await oauth.google.authorize_redirect(request, redirect_uri, prompt="consent", access_type="offline")


@app.get("/auth/callback", name="auth_callback")
async def auth_callback(request: Request):
    token = await oauth.google.authorize_access_token(request)
    userinfo = token["userinfo"]

    dosen_id = db.upsert_dosen(
        email=userinfo["email"],
        nama=userinfo.get("name", userinfo["email"]),
        refresh_token=token.get("refresh_token"),
    )
    request.session["email"] = userinfo["email"]
    request.session["access_token"] = token["access_token"]
    request.session["dosen_id"] = dosen_id
    return RedirectResponse(url="/")


@app.post("/auth/logout")
async def logout(request: Request):
    request.session.clear()
    return RedirectResponse(url="/", status_code=303)


@app.post("/pilih-folder")
async def pilih_folder(request: Request):
    dosen = _current_dosen(request)
    form = await request.form()
    folder_id = form["folder_id"]
    folder_nama = form["folder_nama"]
    db.set_drive_folder(dosen["id"], folder_id, folder_nama)
    return RedirectResponse(url="/", status_code=303)


@app.post("/sync")
async def sync(request: Request):
    dosen = _current_dosen(request)
    access_token = request.session.get("access_token")

    files = drive_web.walk_pdfs_for_user(access_token, dosen["drive_folder_id"])

    from agentdupak.pipeline import proses  # import lokal, hindari circular saat startup

    aktivitas, log = proses(
        files, download_bytes=lambda file_id: drive_web.download_pdf_for_user(access_token, file_id)
    )
    terapkan(aktivitas)
    db.replace_aktivitas(dosen["id"], aktivitas)

    request.session["sync_log"] = log
    return RedirectResponse(url="/", status_code=303)
