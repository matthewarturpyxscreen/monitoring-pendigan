import streamlit as st
import pandas as pd
import requests
from io import BytesIO

# =====================================
# CONFIG DASHBOARD (MULTI LINK)
# =====================================
DASHBOARDS = {
    "📊 Batch 1 - Papua": {
        "sheet_url": "PASTE_GOOGLE_SHEET_URL_1",
        "sheet_name": "INSTALASI IFP 2025 BATCH 1"
    },
    "📊 Batch 2 - Jawa Timur": {
        "sheet_url": "PASTE_GOOGLE_SHEET_URL_2",
        "sheet_name": "Sheet1"
    },
    "📊 Batch 3 - Nasional": {
        "sheet_url": "PASTE_GOOGLE_SHEET_URL_3",
        "sheet_name": "Sheet1"
    }
}

st.set_page_config(
    page_title="Monitoring Instalasi IFP",
    layout="wide"
)

# =====================================
# UTIL FUNCTIONS
# =====================================
def load_gsheet(url, sheet_name):
    export_url = url.replace("/edit", "/export") + f"?format=xlsx&sheet={sheet_name}"
    r = requests.get(export_url)
    return pd.read_excel(BytesIO(r.content))

def normalize_status(val):
    if pd.isna(val):
        return "Belum Dikerjakan"
    val = str(val).upper()
    return "Selesai" if "SELESAI" in val else "Belum Dikerjakan"

def status_color(status):
    return "🟩 Selesai" if status == "Selesai" else "⬜ Belum Dikerjakan"

# =====================================
# SIDEBAR
# =====================================
st.sidebar.title("📌 Pilih Dashboard")

dashboard_name = st.sidebar.selectbox(
    "Dashboard",
    list(DASHBOARDS.keys())
)

status_filter = st.sidebar.selectbox(
    "Filter Status",
    ["Semua Status", "Belum Dikerjakan", "Selesai"]
)

# =====================================
# LOAD DATA
# =====================================
cfg = DASHBOARDS[dashboard_name]
df = load_gsheet(cfg["sheet_url"], cfg["sheet_name"])

# Normalisasi kolom
df.columns = [c.strip() for c in df.columns]

df["Status_Category"] = df["Status_Text"].apply(normalize_status)

# =====================================
# FILTER
# =====================================
if status_filter != "Semua Status":
    df = df[df["Status_Category"] == status_filter]

# =====================================
# METRICS
# =====================================
total = len(df)
selesai = (df.Status_Category == "Selesai").sum()
belum = total - selesai

st.title(dashboard_name)

col1, col2, col3 = st.columns(3)

with col1:
    st.metric("📋 Total Data", total)

with col2:
    st.metric("⬜ Belum Dikerjakan", belum)

with col3:
    st.metric("🟩 Selesai", selesai)

# =====================================
# PROGRESS
# =====================================
if total > 0:
    st.progress(selesai / total)
    st.caption(f"Progress: {selesai}/{total} ({(selesai/total)*100:.1f}%)")

# =====================================
# TABLE
# =====================================
display_cols = [
    "NPSN", "Provinsi", "Kabupaten", "Nama",
    "Teknisi", "Status_Category"
]

display_cols = [c for c in display_cols if c in df.columns]

df_display = df[display_cols].copy()
df_display["Status"] = df_display["Status_Category"].apply(status_color)

st.dataframe(
    df_display.drop(columns=["Status_Category"]),
    use_container_width=True
)

# =====================================
# DOWNLOAD
# =====================================
st.download_button(
    "⬇️ Download Excel",
    data=df.to_excel(index=False),
    file_name=f"{dashboard_name}.xlsx"
)
