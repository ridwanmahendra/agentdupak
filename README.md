# agentdupak

Prototipe parser + rules engine untuk mengubah dokumen SK/Berita Acara dosen
(dari Drive, dikelola BAAK fakultas) menjadi aktivitas DUPAK terstruktur dan
angka kredit (AK) otomatis — tanpa mengisi Excel manual.

## Status saat ini

Sudah divalidasi sync end-to-end dari Drive asli (bukan cuma fixture), termasuk
lewat beberapa putaran perbaikan dari log sync nyata.

| Jenis dokumen | Parser | Catatan |
|---|---|---|
| SK Mengajar / Sesuai Forlap ("JA ... Genap/Ganjil") | `parsers/sk_mengajar.py` | ✅ Tervalidasi di data nyata (lintas semester). **Sumber kebenaran untuk mengajar** — folder "Sesuai Siakad" di sebelahnya sengaja di-skip permanen (representasi lain dari data yang sama, akan double-counting kalau diparse juga). |
| Berita Acara Penguji (non-skripsi + TA) | `parsers/sk_penguji.py` | ✅ Tervalidasi di data nyata setelah OCR fallback dipasang — dokumen aslinya hasil scan (pypdf dapat 0 karakter), bukan teks asli seperti dugaan awal. |
| SK Bimbingan (Pembimbing Publikasi Karya Ilmiah) | `parsers/sk_bimbingan.py` | ✅ Parser jalan (dari nama file, tanpa download PDF). ⚠️ **AK-nya BELUM ada rule resmi** — ditandai `ak_perlu_review=True`, dihitung 0 sementara, tidak bikin sync gagal. Perlu dikonfirmasi nilai AK resminya dulu sebelum dipakai untuk pengajuan DUPAK sungguhan. |
| Lembar Pengesahan / Cover (hasil scan, ber-watermark) | belum dibuat | OCR terbukti jalan (`pdf_extract.py` auto-fallback), tapi hasilnya noisy karena watermark — parsernya nanti harus toleran, cari frasa kunci bukan posisi baris persis. |

## Menjalankan

Butuh 2 dependency sistem untuk OCR dokumen hasil scan (tidak bisa lewat pip):

```bash
# macOS
brew install tesseract tesseract-lang poppler

# Debian/Ubuntu
sudo apt install tesseract-ocr tesseract-ocr-ind poppler-utils
```

```bash
pip install -r requirements.txt

PYTHONPATH=src python3 scripts/demo.py      # pakai fixture teks, cepat buat ngecek logic
PYTHONPATH=src python3 -m pytest tests/ -v   # jalankan test
```

### Jalan dengan PDF asli dari Google Drive

Butuh setup sekali (akun Google Anda sendiri, bukan bagian dari repo ini):

1. Buat project di [Google Cloud Console](https://console.cloud.google.com/), aktifkan **Google Drive API**.
2. Buat OAuth client ID tipe **Desktop app**, download sebagai `credentials.json`, letakkan di root project ini (sudah di-`.gitignore`, jangan sampai ke-commit).
3. Jalankan:
   ```bash
   PYTHONPATH=src python3 scripts/sync_and_parse.py <folder_id_dosen>
   ```
   `<folder_id_dosen>` adalah ID folder dosen di Drive (bagian setelah `/folders/` di URL-nya, contoh folder "Ridwan Mahenra" di struktur `FTIK - DATA DOSEN`). Browser akan terbuka sekali untuk login & izin akses — setelah itu token tersimpan di `token.json`, tidak perlu login ulang.
   Akun yang login harus sudah punya akses lihat ke folder itu (sama seperti folder yang di-share ke Anda).

## Web app (opsi B — dosen login sendiri, tanpa install apa pun)

Dosen login dengan akun Google, pilih folder Drive miliknya (dari folder yang
di-share BAAK fakultas ke dia), klik "Sync", lalu lihat aktivitas + total AK.
Isolasi data antar dosen otomatis terjamin oleh permission Drive API sendiri
(dosen B login dengan akunnya hanya bisa lihat folder yang di-share ke dia).

Setup sekali (beda dari OAuth client CLI di atas — ini tipe **Web application**):

1. Di project Google Cloud Console yang sama, buat OAuth client ID baru tipe
   **Web application**. Authorized redirect URI: `http://localhost:8000/auth/callback`
   (ganti domainnya saat deploy ke server sungguhan).
2. Jalankan:
   ```bash
   pip install -r requirements.txt
   GOOGLE_CLIENT_ID=<client id> GOOGLE_CLIENT_SECRET=<client secret> \
     SESSION_SECRET=<string acak panjang> \
     PYTHONPATH=src uvicorn agentdupak.webapp.main:app --reload
   ```
3. Buka `http://localhost:8000`, login, pilih folder, sync.

Datanya tersimpan di `agentdupak.db` (SQLite, local file, tidak di-commit).

## Struktur

```
src/agentdupak/
  models.py            # dataclass Aktivitas
  pdf_extract.py        # ekstrak teks dari PDF (teks asli, bukan hasil scan)
  drive_common.py        # logic jalan-jalan folder Drive + download, dipakai CLI & web
  drive_sync.py          # versi CLI: pakai credentials.json/token.json di disk
  pipeline.py             # download -> ekstrak -> parse -> Aktivitas (dipakai CLI & web)
  parsers/                # 1 modul per jenis dokumen
  rules/ak_rules.py       # rujukan Lampiran III Permenpan RB 17/2013 & 46/2013
  webapp/
    main.py               # route FastAPI (login, pilih folder, sync, dashboard)
    auth.py               # OAuth login Google (Authlib)
    drive_web.py           # versi web: pakai access token dari sesi browser
    db.py                  # penyimpanan SQLite (dosen + aktivitas)
    templates/              # login.html, browse.html, dashboard.html
scripts/
  demo.py               # jalan dari fixture teks (tanpa Drive) -- CLI
  sync_and_parse.py      # jalan end-to-end dari Drive asli -- CLI
tests/fixtures/          # contoh teks asli (hasil ekstraksi PDF nyata) untuk test parser
```

## Langkah selanjutnya

1. **Konfirmasi nilai AK resmi untuk "bimbingan publikasi karya ilmiah"** (jalur non-skripsi) dan tambahkan ke `rules/ak_rules.py` — begitu ketemu, kategori ini otomatis lepas dari status "perlu review".
2. Parser untuk Lembar Pengesahan/Cover (regex toleran noise OCR, atau LLM lokal untuk kasus yang terlalu berantakan).
3. Lengkapi `rules/ak_rules.py` dengan kategori Penelitian, Pengabdian, Penunjang dari sheet DUPAK OK.
4. Status review manual sebelum AK dianggap final untuk SUBMIT resmi (sekarang langsung dihitung begitu sync, belum ada tahap "dosen konfirmasi" terpisah dari "sistem menghitung").
5. Simpan refresh_token dengan terenkripsi di DB (sekarang plaintext) sebelum dipakai di luar localhost.
6. UI untuk menampilkan & menindaklanjuti aktivitas berstatus `ak_perlu_review` secara terpusat (sekarang cuma ditandai warna kuning di tabel dashboard).
