
import streamlit as st
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import matplotlib.pyplot as plt

st.set_page_config(page_title="Dashboard Kontak", page_icon="📞", layout="wide")

# ---------- Helpers ----------

ID_MONTHS = {
    "Jan": "Jan", "Feb": "Feb", "Mar": "Mar", "Apr": "Apr",
    "Mei": "May", "Jun": "Jun", "Jul": "Jul", "Agu": "Aug",
    "Ags": "Aug", "Agust": "Aug", "Sep": "Sep", "Okt": "Oct",
    "Nov": "Nov", "Des": "Dec"
}

def id_to_en_months(s: str) -> str:
    if not isinstance(s, str):
        return s
    out = s
    for id_m, en_m in ID_MONTHS.items():
        out = out.replace(f"-{id_m}-", f"-{en_m}-").replace(f" {id_m} ", f" {en_m} ")
    return out

@st.cache_data
def load_data(file) -> pd.DataFrame:
    if file is None:
        return pd.DataFrame()
    try:
        df = pd.read_excel(file)
    except Exception:
        df = pd.read_csv(file)
    # Standardize column names
    df.columns = [c.strip() for c in df.columns]
    # Rename common columns if needed
    col_map_candidates = {
        "Nama": ["Nama", "name"],
        "Nomor HP": ["Nomor HP", "No HP", "Phone", "Nomor"],
        "Email": ["Email", "email"],
        "Perusahaan": ["Perusahaan", "Company"],
        "Asal File": ["Asal File", "Source"],
        "Link WhatsApp": ["Link WhatsApp", "WA Link", "Whatsapp Link"],
        "Status Follow-Up": ["Status Follow-Up", "Status", "Follow Up Status"],
        "Keterangan": ["Keterangan", "Notes"],
        "Last Contact": ["Last Contact", "LastContact", "Terakhir Kontak"],
    }
    rename = {}
    for std, aliases in col_map_candidates.items():
        for a in aliases:
            if a in df.columns:
                rename[a] = std
                break
    df = df.rename(columns=rename)

    # Parse last contact date
    if "Last Contact" in df.columns:
        # try replace Indonesian month names to English
        df["Last Contact (raw)"] = df["Last Contact"]
        df["Last Contact"] = (
            pd.to_datetime(df["Last Contact"].astype(str).apply(id_to_en_months),
                           dayfirst=True, errors="coerce")
        )
    else:
        df["Last Contact"] = pd.NaT

    # Clean phone, generate wa link if missing
    def clean_phone(x):
        s = str(x).strip().replace(" ", "").replace("-", "").replace("+", "")
        s = s.replace(".","")
        if s.startswith("0"):
            s = "62" + s[1:]
        if not s.startswith("62"):
            if s.isdigit():
                s = "62" + s
        return s

    if "Nomor HP" in df.columns:
        df["Nomor HP (clean)"] = df["Nomor HP"].apply(clean_phone)
    else:
        df["Nomor HP (clean)"] = ""

    if "Link WhatsApp" not in df.columns or df["Link WhatsApp"].isna().all():
        df["Link WhatsApp"] = "https://wa.me/" + df["Nomor HP (clean)"].astype(str)
    else:
        # ensure wa link exists
        df["Link WhatsApp"] = df["Link WhatsApp"].fillna("https://wa.me/" + df["Nomor HP (clean)"].astype(str))

    # Days since last contact
    today = pd.Timestamp(datetime.now().date())
    df["Days Since Last Contact"] = (today - df["Last Contact"]).dt.days

    # SLA based on days since last contact
    def sla_label(d):
        if pd.isna(d):
            return "No Date"
        try:
            d = int(d)
        except:
            return "No Date"
        if d >= 20: return "⚠️ 20+ days (Red)"
        if d >= 7: return "🟡 7+ days (Yellow)"
        return "✅ <7 days (Green)"
    df["SLA Status"] = df["Days Since Last Contact"].apply(sla_label)

    return df

def kpi_card(label, value, help_txt=None):
    with st.container(border=True):
        st.markdown(f"**{label}**")
        st.markdown(f"<h2 style='margin-top:0'>{value}</h2>", unsafe_allow_html=True)
        if help_txt:
            st.caption(help_txt)

# ---------- UI ----------

st.title("📞 Dashboard Kontak")
st.caption("Upload file Excel/CSV kontak kamu. App ini akan otomatis bikin ringkasan, grafik, dan tabel yang bisa difilter.")

uploaded = st.sidebar.file_uploader("Upload Excel atau CSV", type=["xlsx","xls","csv"])

df = load_data(uploaded)

if df.empty:
    st.info("Belum ada file yang diupload. Gunakan tombol di sidebar untuk upload. Template tersedia di README.")
    st.stop()

# Sidebar filters
with st.sidebar:
    st.header("Filter")
    # Status filter
    status_col = "Status Follow-Up" if "Status Follow-Up" in df.columns else None
    statuses = sorted(df[status_col].dropna().unique()) if status_col else []
    picked_status = st.multiselect("Status Follow-Up", statuses, default=[])

    # Keterangan text filter
    ket_val = st.text_input("Cari di Keterangan (opsional)", value="")

    # Date range
    min_d = pd.to_datetime(df["Last Contact"], errors="coerce").min()
    max_d = pd.to_datetime(df["Last Contact"], errors="coerce").max()
    if pd.notna(min_d) and pd.notna(max_d):
        start_d, end_d = st.date_input("Rentang Tanggal Last Contact",
                                       [min_d.date(), max_d.date()])
    else:
        start_d, end_d = None, None

    # Search Name/Phone
    q = st.text_input("Search Nama/HP/Email", value="")

# Apply filters
filtered = df.copy()
if status_col and picked_status:
    filtered = filtered[filtered[status_col].isin(picked_status)]
if ket_val:
    filtered = filtered[filtered.get("Keterangan","").astype(str).str.contains(ket_val, case=False, na=False)]
if start_d and end_d:
    mask = (filtered["Last Contact"] >= pd.Timestamp(start_d)) & (filtered["Last Contact"] <= pd.Timestamp(end_d))
    filtered = filtered[mask]
if q:
    ql = q.lower()
    cols_search = ["Nama", "Nomor HP", "Nomor HP (clean)", "Email"]
    cols_present = [c for c in cols_search if c in filtered.columns]
    if cols_present:
        mask = False
        for c in cols_present:
            mask = mask | filtered[c].astype(str).str.lower().str.contains(ql, na=False)
        filtered = filtered[mask]

# ---------- KPIs ----------
c1, c2, c3, c4 = st.columns(4)
total_contacts = len(filtered)
done_count = len(filtered[filtered[status_col] == "Done Contact"]) if status_col else "-"
pending_count = len(filtered[filtered[status_col].isin(["Belum dikontak","Belum dihubungi","Pending"])]) if status_col else "-"
last_contact_date = pd.to_datetime(filtered["Last Contact"], errors="coerce").max()

with c1: kpi_card("Total Kontak (filtered)", total_contacts)
with c2: kpi_card("Sudah Follow-up", done_count)
with c3: kpi_card("Belum Follow-up (Pending)", pending_count)
with c4: kpi_card("Last Contact Terakhir", last_contact_date.date().isoformat() if pd.notna(last_contact_date) else "-")

st.markdown("---")

# ---------- Charts ----------
left, right = st.columns((1,1))

with left:
    if status_col:
        st.subheader("Distribusi Status Follow-Up")
        counts = filtered[status_col].value_counts()
        fig, ax = plt.subplots()
        counts.plot(kind="bar", ax=ax)
        ax.set_xlabel("Status")
        ax.set_ylabel("Jumlah")
        st.pyplot(fig)
    else:
        st.info("Kolom 'Status Follow-Up' tidak ditemukan.")

with right:
    st.subheader("Aktivitas per Tanggal (Last Contact)")
    df_dates = filtered.dropna(subset=["Last Contact"]).copy()
    if not df_dates.empty:
        df_dates["Date"] = df_dates["Last Contact"].dt.date
        series = df_dates.groupby("Date").size().sort_index()
        fig2, ax2 = plt.subplots()
        series.plot(kind="line", marker="o", ax=ax2)
        ax2.set_xlabel("Tanggal")
        ax2.set_ylabel("Jumlah Kontak")
        st.pyplot(fig2)
    else:
        st.info("Belum ada tanggal pada 'Last Contact'.")

st.markdown("---")

st.subheader("Daftar Kontak (Terfilter)")
display_cols = [c for c in ["Nama","Nomor HP","Nomor HP (clean)","Email","Perusahaan","Status Follow-Up","Keterangan","Last Contact","Days Since Last Contact","SLA Status","Link WhatsApp"] if c in filtered.columns]
st.dataframe(filtered[display_cols], use_container_width=True)

# Download filtered
csv = filtered[display_cols].to_csv(index=False).encode("utf-8")
st.download_button("⬇️ Download CSV (filtered)", csv, file_name="contacts_filtered.csv", mime="text/csv")

st.caption("Tip: Klik kolom 'Link WhatsApp' untuk membuka chat. Pastikan nomornya sudah dalam format 62xxxxx.")
