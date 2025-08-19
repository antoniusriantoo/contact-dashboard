
# 📞 Dashboard Kontak – Streamlit

## Cara Pakai (Lokal)
1. **Install Python 3.10+** (cek: `python --version`).
2. (Opsional) Buat virtual env:
   ```bash
   python -m venv .venv
   # Windows
   .venv\Scripts\activate
   # macOS/Linux
   source .venv/bin/activate
   ```
3. Install dependency:
   ```bash
   pip install -r requirements.txt
   ```
4. Jalankan:
   ```bash
   streamlit run app.py
   ```
5. Buka link yang muncul (biasanya `http://localhost:8501`).

## Format Kolom yang Didukung
- **Nama** (wajib agar enak dilihat)
- **Nomor HP** (akan dibersihkan jadi `62...` otomatis)
- **Email** (opsional)
- **Perusahaan** (opsional)
- **Link WhatsApp** (opsional; kalau kosong akan dibuat `https://wa.me/62...`)
- **Status Follow-Up** (disarankan, contoh: `Done Contact`, `Belum dikontak`, `Pending`)
- **Keterangan** (opsional)
- **Last Contact** (tanggal; app ini bisa baca format `19-Agu-25`, `15-Aug-2025`, dll.)

> Kalau nama kolom kamu agak beda, app akan mencoba mengenali alias umum (mis. `No HP`, `Status`, `Notes`, dll.).

## Fitur
- KPI ringkas (total, done, pending, last contact terbaru)
- Grafik distribusi status & tren kontak per tanggal
- Filter by status, keterangan, rentang tanggal, dan search nama/HP/email
- Kolom **Days Since Last Contact** + **SLA Status** (🟡 7+ hari, ⚠️ 20+ hari)
- Download CSV hasil filter

## Deploy Gratis (Streamlit Cloud)
1. Push folder ini ke GitHub.
2. Buka **share.streamlit.io** dan hubungkan repo kamu.
3. Pilih `app.py` sebagai file utama.
