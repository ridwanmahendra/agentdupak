# agentdupak

Prototipe parser + rules engine untuk mengubah dokumen SK/Berita Acara dosen
(dari Drive, dikelola BAAK fakultas) menjadi aktivitas DUPAK terstruktur dan
angka kredit (AK) otomatis — tanpa mengisi Excel manual.

## Status saat ini

Baru mencakup 2 jenis dokumen yang sudah diverifikasi dari data nyata:

| Jenis dokumen | Parser | Butuh LLM? |
|---|---|---|
| SK Penugasan Mengajar ("JA ... Genap/Ganjil") | `parsers/sk_mengajar.py` | Tidak — teks terstruktur rapi |
| Berita Acara Penguji (non-skripsi) | `parsers/sk_penguji.py` | Tidak — teks terstruktur rapi |
| Lembar Pengesahan / Cover (hasil scan, ber-watermark) | belum dibuat | Ya — OCR-nya noisy |
| SK Bimbingan (metadata ada di nama file) | belum dibuat | Tidak — cukup parse nama file |

## Menjalankan

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

## Struktur

```
src/agentdupak/
  models.py           # dataclass Aktivitas
  pdf_extract.py       # ekstrak teks dari PDF (teks asli, bukan hasil scan)
  drive_sync.py        # scan folder Drive + download PDF via Google Drive API
  parsers/              # 1 modul per jenis dokumen
  rules/ak_rules.py     # rujukan Lampiran III Permenpan RB 17/2013 & 46/2013
scripts/
  demo.py              # jalan dari fixture teks (tanpa Drive)
  sync_and_parse.py     # jalan end-to-end dari Drive asli
tests/fixtures/         # contoh teks asli (hasil ekstraksi PDF nyata) untuk test parser
```

## Langkah selanjutnya

1. Parser untuk SK Bimbingan (dari nama file) dan Lembar Pengesahan/Cover (lewat LLM lokal, karena hasil scan/OCR noisy).
2. Pemetaan folder → parser di `sync_and_parse.py` baru mencakup "SK Mengajar" dan "SK Penguji" — tambah entri baru begitu parser lain siap.
3. Lengkapi `rules/ak_rules.py` dengan kategori Penelitian, Pengabdian, Penunjang dari sheet DUPAK OK.
4. Layer penyimpanan (DB) + status review sebelum AK dianggap final.
