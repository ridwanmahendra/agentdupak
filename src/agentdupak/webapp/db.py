"""Penyimpanan SQLite sederhana: 1 baris per dosen, 1 baris per aktivitas.

Sengaja pakai sqlite3 bawaan Python, bukan ORM -- prototipe ini belum perlu
abstraksi lebih dari ini. Kalau nanti pindah ke Postgres (multi-instance,
butuh concurrent write yang lebih baik), skema di bawah ini jadi acuan migrasi.
"""

from __future__ import annotations

import json
import sqlite3
from contextlib import contextmanager
from pathlib import Path

DB_PATH = Path(__file__).parent.parent.parent.parent / "agentdupak.db"

SCHEMA = """
CREATE TABLE IF NOT EXISTS dosen (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    email TEXT UNIQUE NOT NULL,
    nama TEXT NOT NULL,
    refresh_token TEXT,
    drive_folder_id TEXT,
    drive_folder_nama TEXT,
    last_sync_log TEXT,
    last_synced_pada TEXT
);

CREATE TABLE IF NOT EXISTS aktivitas (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    dosen_id INTEGER NOT NULL REFERENCES dosen(id),
    kategori TEXT NOT NULL,
    atribut_json TEXT NOT NULL,
    ak REAL NOT NULL,
    ak_perlu_review INTEGER NOT NULL DEFAULT 0,
    sumber_file TEXT NOT NULL,
    disinkron_pada TEXT NOT NULL DEFAULT (datetime('now'))
);
"""


@contextmanager
def connect():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    try:
        yield conn
        conn.commit()
    finally:
        conn.close()


def init_db() -> None:
    with connect() as conn:
        conn.executescript(SCHEMA)
        # migrasi ringan untuk database lama yang sudah ada sebelum kolom ini ditambahkan
        for ddl in (
            "ALTER TABLE dosen ADD COLUMN last_sync_log TEXT",
            "ALTER TABLE dosen ADD COLUMN last_synced_pada TEXT",
            "ALTER TABLE aktivitas ADD COLUMN ak_perlu_review INTEGER NOT NULL DEFAULT 0",
        ):
            try:
                conn.execute(ddl)
            except sqlite3.OperationalError:
                pass  # kolom sudah ada


def upsert_dosen(email: str, nama: str, refresh_token: str | None) -> int:
    with connect() as conn:
        row = conn.execute("SELECT id FROM dosen WHERE email = ?", (email,)).fetchone()
        if row:
            if refresh_token:
                conn.execute(
                    "UPDATE dosen SET nama = ?, refresh_token = ? WHERE id = ?",
                    (nama, refresh_token, row["id"]),
                )
            return row["id"]
        cursor = conn.execute(
            "INSERT INTO dosen (email, nama, refresh_token) VALUES (?, ?, ?)",
            (email, nama, refresh_token),
        )
        return cursor.lastrowid


def get_dosen_by_email(email: str) -> sqlite3.Row | None:
    with connect() as conn:
        return conn.execute("SELECT * FROM dosen WHERE email = ?", (email,)).fetchone()


def set_drive_folder(dosen_id: int, folder_id: str, folder_nama: str) -> None:
    with connect() as conn:
        conn.execute(
            "UPDATE dosen SET drive_folder_id = ?, drive_folder_nama = ? WHERE id = ?",
            (folder_id, folder_nama, dosen_id),
        )


def replace_aktivitas(dosen_id: int, aktivitas_list, log: list[str]) -> None:
    """Ganti seluruh aktivitas milik 1 dosen dengan hasil sync terbaru, dan simpan
    log sync-nya secara permanen (bukan cuma sekali tampil lalu hilang)."""
    with connect() as conn:
        conn.execute("DELETE FROM aktivitas WHERE dosen_id = ?", (dosen_id,))
        conn.executemany(
            """INSERT INTO aktivitas (dosen_id, kategori, atribut_json, ak, ak_perlu_review, sumber_file)
               VALUES (?, ?, ?, ?, ?, ?)""",
            [
                (
                    dosen_id,
                    a.kategori,
                    json.dumps(a.atribut, ensure_ascii=False),
                    a.ak,
                    int(a.ak_perlu_review),
                    a.sumber_file,
                )
                for a in aktivitas_list
            ],
        )
        conn.execute(
            "UPDATE dosen SET last_sync_log = ?, last_synced_pada = datetime('now') WHERE id = ?",
            (json.dumps(log, ensure_ascii=False), dosen_id),
        )


def get_sync_log(dosen_id: int) -> list[str]:
    with connect() as conn:
        row = conn.execute("SELECT last_sync_log FROM dosen WHERE id = ?", (dosen_id,)).fetchone()
        if not row or not row["last_sync_log"]:
            return []
        return json.loads(row["last_sync_log"])


def get_aktivitas(dosen_id: int) -> list[sqlite3.Row]:
    with connect() as conn:
        return conn.execute(
            "SELECT * FROM aktivitas WHERE dosen_id = ? ORDER BY kategori, id", (dosen_id,)
        ).fetchall()
