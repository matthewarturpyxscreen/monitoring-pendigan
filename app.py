import streamlit as st
st.cache_data.clear()

import pandas as pd
import re
import requests
import time
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

REFRESH_INTERVAL = 300  # 5 menit (AMAN Streamlit Cloud)

# ======================================================
# REALTIME SESSION TRACKER
# ======================================================
if "last_refresh" not in st.session_state:
    st.session_state.last_refresh = time.time()

# ======================================================
# CSS (DESIGN TIDAK DIUBAH)
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
def extract_sheet_id(url):
    m = re.search(r"/spreadsheets/d/([a-zA-Z0-9-_]+)", url)
    return m.group(1) if m else None

def get_all_gids(sheet_id):
    """Ambil semua gid TANPA API"""
    url = f"https://docs.google.com/spreadsheets/d/{sheet_id}"
    html = requests.get(url).text
    gids = set(re.findall(r'gid=([0-9]+)', html))
    return list(gids)

def csv_url(sheet_id, gid):
    return f"https://docs.google.com/spreadsheets/d/{sheet_id}/export?format=csv&gid={gid}"

@st.cache_data(ttl=REFRESH_INTERVAL)
def load_all_sheets(sheet_id):
    dfs = []
    gids = get_all_gids(sheet_id)

    for gid in gids:
        try:
            df = pd.read_csv(csv_url(sheet_id, gid))
            df["__gid"] = gid
            dfs.append(df)
        except:
            continue

    if not dfs:
        return None, "Tidak ada sheet yang bisa dibaca"

    return pd.concat(dfs, ignore_index=True), None

# ======================================================
# STATUS NORMALIZER (ANTI ERROR WARNA)
# ======================================================
def normalize_status(val):
    if pd.isna(val):
        return "Belum Dikerjakan"

    val = str(val).upper()
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
    <p>Realtime Sync Active • Last Update: {datetime.now().strftime('%d %B %Y, %H:%M:%S')}</p>
</div>
""", unsafe_allow_html=True)

# ======================================================
# SIDEBAR
# ======================================================
with st.sidebar:
    sheet_url = st.text_input("🔗 Google Spreadsheet URL")
    load_btn = st.button("📥 Load Semua Sheet")

# ======================================================
# MAIN LOGIC
# ======================================================
if not sheet_url:
    st.info("Masukkan URL Google Spreadsheet")
    st.stop()

sheet_id = extract_sheet_id(sheet_url)
if not sheet_id:
    st.error("URL Spreadsheet tidak valid")
    st.stop()

if load_btn or "df" in st.session_state:
    if load_btn:
        with st.spinner("⏳ Memuat semua sheet..."):
            df, err = load_all_sheets(sheet_id)
            if err:
                st.error(err)
                st.stop()
            st.session_state["df"] = df

df = st.session_state["df"]

# ======================================================
# BACKGROUND REALTIME REFRESH
# ======================================================
now = time.time()
if now - st.session_state.last_refresh > REFRESH_INTERVAL:
    st.session_state.last_refresh = now
    st.cache_data.clear()
    st.experimental_rerun()

# ======================================================
# VALIDASI KOLOM
# ======================================================
required_columns = [
    "Trans. ID", "Nama", "Jenjang", "Kabupaten", "Propinsi",
    "NPSN", "Status_Text", "Keterangan", "Petugas"
]

missing = [c for c in required_columns if c not in df.columns]
if missing:
    st.error(f"Kolom tidak ditemukan di beberapa sheet: {missing}")
    st.stop()

# ======================================================
# PROCESS DATA
# ======================================================
df["Status_Text"] = df["Status_Text"].apply(normalize_status)
df["Status_Category"] = df["Status_Text"]

# ======================================================
# METRICS
# ======================================================
st.markdown('<div class="section-header"><h3>📈 Ringkasan Status (ALL SHEET)</h3></div>', unsafe_allow_html=True)

c1, c2, c3, c4, c5 = st.columns(5)
c1.metric("BELUM", (df.Status_Category=="Belum Dikerjakan").sum())
c2.metric("PROSES", (df.Status_Category=="Sedang Diproses").sum())
c3.metric("KURANG BAPP", (df.Status_Category=="Kurang BAPP").sum())
c4.metric("SELESAI", (df.Status_Category=="Selesai").sum())
c5.metric("BERMASALAH", (df.Status_Category=="Data Bermasalah").sum())

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
    "📥 Download CSV (ALL SHEET)",
    filtered_df.to_csv(index=False),
    "monitoring_all_sheet.csv",
    "text/csv"
)

# ======================================================
# FOOTER
# ======================================================
st.markdown("""
<div class='dashboard-footer'>
    <p>🚀 Dashboard Monitoring v3.0 • Realtime • Multi Sheet</p>
</div>
""", unsafe_allow_html=True)
