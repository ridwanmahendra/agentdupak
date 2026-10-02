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
PYTHONPATH=src python3 scripts/demo.py     # lihat hasil parsing + AK
PYTHONPATH=src python3 -m pytest tests/ -v  # jalankan test
```

## Struktur

```
src/agentdupak/
  models.py          # dataclass Aktivitas
  parsers/            # 1 modul per jenis dokumen
  rules/ak_rules.py   # rujukan Lampiran III Permenpan RB 17/2013 & 46/2013
tests/fixtures/       # contoh teks asli (hasil ekstraksi PDF nyata) untuk test parser
```

## Langkah selanjutnya

1. Parser untuk SK Bimbingan (dari nama file) dan Lembar Pengesahan/Cover (lewat LLM lokal).
2. Koneksi ke Google Drive API untuk otomatis scan folder `FTIK - DATA DOSEN/<nama dosen>/...`.
3. Lengkapi `rules/ak_rules.py` dengan kategori Penelitian, Pengabdian, Penunjang dari sheet DUPAK OK.
4. Layer penyimpanan (DB) + status review sebelum AK dianggap final.
