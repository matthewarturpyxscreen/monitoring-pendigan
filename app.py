import streamlit as st
st.cache_data.clear()

import pandas as pd
import re
from datetime import datetime

# ======================================================
# CONFIG
# ======================================================
st.set_page_config(
    page_title="Dashboard Monitoring Pekerjaan",
    layout="wide",
    initial_sidebar_state="expanded",
    menu_items={'About': "Dashboard Monitoring Pekerjaan v3.0"}
)

REFRESH_INTERVAL = 300

# ======================================================
# CSS (TIDAK DIUBAH)
# ======================================================
st.markdown("""
<style>
/* CSS KAMU — TIDAK DIUBAH */
</style>
""", unsafe_allow_html=True)

st.markdown(
    f"""<meta http-equiv="refresh" content="{REFRESH_INTERVAL}">""",
    unsafe_allow_html=True
)

# ======================================================
# UTILITIES
# ======================================================
def convert_to_csv_url(sheet_id: str, gid: str = "0") -> str:
    return f"https://docs.google.com/spreadsheets/d/{sheet_id}/export?format=csv&gid={gid}"

@st.cache_data(ttl=REFRESH_INTERVAL)
def load_data(sheet_id: str, gid: str = "0"):
    try:
        return pd.read_csv(convert_to_csv_url(sheet_id, gid)), None
    except Exception as e:
        return None, str(e)

# ======================================================
# STATUS NORMALIZER (ANTI GOOGLE SHEETS BUG)
# ======================================================
def normalize_status(val):
    if pd.isna(val):
        return "Belum Dikerjakan"

    val = str(val).upper()

    # hapus karakter siluman
    val = re.sub(r'[\u00A0\u200B\u200C\u200D\t\n\r]', ' ', val)
    val = re.sub(r'\s+', ' ', val).strip()

    if "DATA BERMASALAH" in val:
        return "Data Bermasalah"
    elif "KURANG BAPP" in val:
        return "Kurang BAPP"
    elif "PROSES" in val or "INSTALASI" in val:
        return "Sedang Diproses"
    elif "SELESAI" in val:
        return "Selesai"
    else:
        return "Belum Dikerjakan"

def get_status_color(status):
    return {
        "Belum Dikerjakan": "#94a3b8",
        "Sedang Diproses": "#f59e0b",
        "Kurang BAPP": "#3b82f6",
        "Selesai": "#10b981",
        "Data Bermasalah": "#ef4444"
    }.get(status, "#94a3b8")

# ======================================================
# HEADER
# ======================================================
st.markdown(f"""
<div class='dashboard-header'>
    <h1>📊 Dashboard Monitoring Pekerjaan</h1>
    <p>Last Updated: {datetime.now().strftime('%d %B %Y, %H:%M:%S')}</p>
</div>
""", unsafe_allow_html=True)

# ======================================================
# SIDEBAR
# ======================================================
with st.sidebar:
    sheet_url = st.text_input("🔗 Google Spreadsheet URL")
    sheet_id, gid = None, "0"

    if sheet_url:
        m = re.search(r"/spreadsheets/d/([a-zA-Z0-9-_]+)", sheet_url)
        if m:
            sheet_id = m.group(1)

        g = re.search(r"[#&]gid=([0-9]+)", sheet_url)
        if g:
            gid = g.group(1)

    load_btn = st.button("📥 Load Data")

# ======================================================
# MAIN
# ======================================================
if not sheet_id:
    st.info("Masukkan URL Google Spreadsheet")
    st.stop()

if load_btn or "df" in st.session_state:
    if load_btn:
        df, err = load_data(sheet_id, gid)
        if err:
            st.error(err)
            st.stop()
        st.session_state["df"] = df

df = st.session_state["df"]

# ======================================================
# VALIDASI KOLOM
# ======================================================
required_columns = [
    "Trans. ID", "Nama", "Jenjang", "Kabupaten", "Propinsi",
    "NPSN", "Status_Text", "Keterangan", "Petugas"
]

missing = [c for c in required_columns if c not in df.columns]
if missing:
    st.error(f"Kolom hilang: {missing}")
    st.stop()

# ======================================================
# PROCESS DATA (FIX UTAMA)
# ======================================================
df["Status_Text"] = df["Status_Text"].apply(normalize_status)
df["Status_Category"] = df["Status_Text"]

# ======================================================
# METRICS
# ======================================================
st.markdown('<div class="section-header"><h3>📈 Ringkasan Status</h3></div>', unsafe_allow_html=True)

c1, c2, c3, c4, c5 = st.columns(5)

c1.metric("BELUM", (df.Status_Category == "Belum Dikerjakan").sum())
c2.metric("PROSES", (df.Status_Category == "Sedang Diproses").sum())
c3.metric("KURANG BAPP", (df.Status_Category == "Kurang BAPP").sum())
c4.metric("SELESAI", (df.Status_Category == "Selesai").sum())
c5.metric("BERMASALAH", (df.Status_Category == "Data Bermasalah").sum())

# ======================================================
# FILTER
# ======================================================
status_filter = st.selectbox(
    "Status",
    [
        "Semua",
        "Belum Dikerjakan",
        "Sedang Diproses",
        "Kurang BAPP",
        "Selesai",
        "Data Bermasalah"
    ]
)

filtered_df = df.copy()
if status_filter != "Semua":
    filtered_df = filtered_df[filtered_df["Status_Category"] == status_filter]

# ======================================================
# TABLE
# ======================================================
def style_status(val):
    return f"background-color:{get_status_color(val)};color:white;font-weight:600"

st.dataframe(
    filtered_df[required_columns]
    .style
    .applymap(style_status, subset=["Status_Text"]),
    use_container_width=True,
    height=550
)

# ======================================================
# DOWNLOAD
# ======================================================
st.download_button(
    "📥 Download CSV",
    filtered_df.to_csv(index=False),
    "monitoring.csv",
    "text/csv"
)

# ======================================================
# FOOTER
# ======================================================
st.markdown("""
<div class='dashboard-footer'>
    <p>🚀 Dashboard Monitoring v3.0</p>
</div>
""", unsafe_allow_html=True)
