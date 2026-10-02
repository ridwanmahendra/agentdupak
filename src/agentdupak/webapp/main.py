"""Web app DUPAK: dosen login dengan Google, pilih folder Drive miliknya,
klik sync, lihat aktivitas + total AK -- tanpa install apa pun di sisi dosen.

Jalankan (lihat README untuk setup OAuth client "Web application"):
    GOOGLE_CLIENT_ID=... GOOGLE_CLIENT_SECRET=... SESSION_SECRET=... \
        uvicorn agentdupak.webapp.main:app --reload
"""

from __future__ import annotations

import base64
import json
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


def _urutkan_folder_relevan(folders: list[dict], nama_dosen: str) -> list[dict]:
    """Taruh folder yang namanya mengandung kata dari nama dosen di urutan
    paling atas -- daftar 'shared with me' biasanya berisi puluhan folder
    tidak relevan, jadi ini bikin folder milik dosen sendiri kelihatan duluan
    tanpa dia harus ketik di kotak pencarian."""
    kata_nama = [k.lower() for k in nama_dosen.split() if len(k) > 2]

    def skor(folder: dict) -> int:
        nama_folder = folder["name"].lower()
        return -sum(1 for kata in kata_nama if kata in nama_folder)

    return sorted(folders, key=skor)


def _encode_path(crumbs: list[dict]) -> str:
    return base64.urlsafe_b64encode(json.dumps(crumbs).encode()).decode()


def _decode_path(path_param: str | None) -> list[dict]:
    if not path_param:
        return []
    return json.loads(base64.urlsafe_b64decode(path_param.encode()).decode())


@app.get("/", response_class=HTMLResponse)
async def index(request: Request):
    dosen = _current_dosen(request)
    if not dosen:
        return templates.TemplateResponse(request, "login.html", {})

    if not dosen["drive_folder_id"]:
        return RedirectResponse(url="/browse")

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


@app.get("/browse", response_class=HTMLResponse)
async def browse(request: Request, folder_id: str | None = None, path: str | None = None):
    """Browser folder Drive bertingkat: dosen bisa masuk ke folder induk
    (misal 'FTIK - DATA DOSEN' yang berisi folder SEMUA dosen) dan pilih
    subfolder yang spesifik miliknya -- supaya sync tidak ikut membaca
    dokumen dosen lain."""
    dosen = _current_dosen(request)
    if not dosen:
        return RedirectResponse(url="/")
    access_token = request.session.get("access_token")

    crumbs = _decode_path(path)

    if folder_id is None:
        items = drive_web.list_shared_folders(access_token)
        items = _urutkan_folder_relevan(items, dosen["nama"])
        current_folder_name = None
    else:
        items = drive_web.list_subfolders_for_user(access_token, folder_id)
        current_folder_name = crumbs[-1]["name"] if crumbs else drive_web.get_folder_name(access_token, folder_id)

    for item in items:
        new_crumbs = crumbs + [{"id": item["id"], "name": item["name"]}]
        item["drill_href"] = f"/browse?folder_id={item['id']}&path={_encode_path(new_crumbs)}"

    breadcrumbs = [{"name": "Folder Drive Saya", "href": "/browse"}]
    for i, c in enumerate(crumbs):
        sub_path = crumbs[: i + 1]
        breadcrumbs.append({"name": c["name"], "href": f"/browse?folder_id={c['id']}&path={_encode_path(sub_path)}"})

    return templates.TemplateResponse(
        request,
        "browse.html",
        {
            "dosen": dosen,
            "items": items,
            "breadcrumbs": breadcrumbs,
            "current_folder_id": folder_id,
            "current_folder_name": current_folder_name,
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


@app.post("/ganti-folder")
async def ganti_folder(request: Request):
    """Reset pilihan folder supaya dosen bisa browse & pilih ulang."""
    dosen = _current_dosen(request)
    db.set_drive_folder(dosen["id"], None, None)
    return RedirectResponse(url="/browse", status_code=303)


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
