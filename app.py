import streamlit as st
import pandas as pd
import re

# ======================================================
# CONFIG
# ======================================================
st.set_page_config(
    page_title="Dashboard Monitoring BAPP & Instalasi",
    layout="wide"
)

REFRESH_INTERVAL = 300  # 5 menit

# Auto refresh
st.markdown(
    f"<meta http-equiv='refresh' content='{REFRESH_INTERVAL}'>",
    unsafe_allow_html=True
)

# ======================================================
# HEADER
# ======================================================
st.title("📊 Dashboard Monitoring Instalasi & BAPP")
st.caption("Cukup masukkan link Google Spreadsheet (edit/view)")

# ======================================================
# INPUT LINK SPREADSHEET (NORMAL)
# ======================================================
sheet_url = st.text_input(
    "🔗 Masukkan link Google Spreadsheet",
    placeholder="https://docs.google.com/spreadsheets/d/xxxxx/edit"
)

load_btn = st.button("📥 Load Data")

# ======================================================
# UTIL: EXTRACT ID & BUILD CSV URL
# ======================================================
def convert_to_csv_url(sheet_url: str) -> str:
    match = re.search(r"/spreadsheets/d/([a-zA-Z0-9-_]+)", sheet_url)
    if not match:
        raise ValueError("Link spreadsheet tidak valid")

    sheet_id = match.group(1)
    return f"https://docs.google.com/spreadsheets/d/{sheet_id}/export?format=csv"

# ======================================================
# LOAD DATA
# ======================================================
@st.cache_data(ttl=REFRESH_INTERVAL)
def load_data(csv_url):
    return pd.read_csv(csv_url)

if not sheet_url:
    st.info("Masukkan link Google Spreadsheet untuk memulai.")
    st.stop()

if load_btn:
    try:
        csv_url = convert_to_csv_url(sheet_url)
        df = load_data(csv_url)
        st.success("✅ Data berhasil dimuat dari Google Spreadsheet")
    except Exception as e:
        st.error("❌ Gagal memuat data. Pastikan link valid & akses Viewer.")
        st.stop()
else:
    st.warning("Klik **Load Data** setelah memasukkan link.")
    st.stop()

# ======================================================
# FIELD YANG DIPAKAI (DARI FILE KAMU)
# ======================================================
required_columns = [
    "Trans. ID",
    "Nama",
    "Jenjang",
    "Kabupaten",
    "Propinsi",
    "Status",
    "Instalasi",
    "Selesai",
    "Keterangan",
    "Petugas"
]

missing_cols = [c for c in required_columns if c not in df.columns]
if missing_cols:
    st.error(f"❌ Kolom tidak ditemukan: {', '.join(missing_cols)}")
    st.stop()

df = df[required_columns]

# ======================================================
# STATUS COLOR
# ======================================================
def status_style(val):
    val = str(val).upper()
    if "BAPP" in val or "KURANG" in val:
        return "background-color:#3b82f6;color:white"   # Biru
    elif "PROSES" in val or "INSTALASI" in val:
        return "background-color:#facc15;color:black"   # Kuning
    elif "SELESAI" in val:
        return "background-color:#22c55e;color:white"   # Hijau
    return ""

# ======================================================
# METRICS
# ======================================================
st.divider()
c1, c2, c3 = st.columns(3)

c1.metric(
    "🔵 Kurang BAPP",
    df["Status"].str.contains("BAPP|KURANG", case=False, na=False).sum()
)
c2.metric(
    "🟡 Diproses",
    df["Status"].str.contains("PROSES|INSTALASI", case=False, na=False).sum()
)
c3.metric(
    "🟢 Selesai",
    df["Status"].str.contains("SELESAI", case=False, na=False).sum()
)

# ======================================================
# FILTER
# ======================================================
st.divider()
provinsi = st.multiselect(
    "Filter Provinsi",
    sorted(df["Propinsi"].dropna().unique()),
    default=sorted(df["Propinsi"].dropna().unique())
)

jenjang = st.multiselect(
    "Filter Jenjang",
    sorted(df["Jenjang"].dropna().unique()),
    default=sorted(df["Jenjang"].dropna().unique())
)

filtered_df = df[
    (df["Propinsi"].isin(provinsi)) &
    (df["Jenjang"].isin(jenjang))
]

# ======================================================
# TABLE
# ======================================================
st.divider()
st.subheader("📋 Detail Monitoring")

st.dataframe(
    filtered_df.style.applymap(status_style, subset=["Status"]),
    use_container_width=True
)

# ======================================================
# FOOTER
# ======================================================
st.caption("⏱️ Auto refresh 5 menit | Input link spreadsheet biasa (tanpa CSV)")
