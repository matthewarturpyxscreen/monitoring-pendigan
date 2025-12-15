import streamlit as st
import pandas as pd

# ======================================================
# CONFIG
# ======================================================
st.set_page_config(
    page_title="Dashboard Monitoring BAPP & Instalasi",
    layout="wide"
)

REFRESH_INTERVAL = 300  # detik (5 menit)

# Auto refresh halaman
st.markdown(
    f"<meta http-equiv='refresh' content='{REFRESH_INTERVAL}'>",
    unsafe_allow_html=True
)

# ======================================================
# HEADER
# ======================================================
st.title("📊 Dashboard Monitoring Instalasi & BAPP")
st.caption("Monitoring realtime dari Google Spreadsheet (CSV)")

# ======================================================
# INPUT LINK SPREADSHEET
# ======================================================
csv_url = st.text_input(
    "🔗 Masukkan link Google Spreadsheet (CSV)",
    placeholder="https://docs.google.com/spreadsheets/d/e/xxxx/pub?output=csv"
)

load_btn = st.button("📥 Load Data")

# ======================================================
# LOAD DATA
# ======================================================
@st.cache_data(ttl=REFRESH_INTERVAL)
def load_data(url):
    return pd.read_csv(url)

if not csv_url:
    st.info("Masukkan link CSV Google Spreadsheet untuk mulai.")
    st.stop()

if load_btn:
    try:
        df = load_data(csv_url)
        st.success("✅ Data berhasil dimuat")
    except Exception:
        st.error("❌ Gagal membaca data. Pastikan link CSV & akses Viewer.")
        st.stop()
else:
    st.warning("Klik **Load Data** setelah memasukkan link CSV.")
    st.stop()

# ======================================================
# SELECT FIELD YANG DIPAKAI
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
# STATUS COLOR MAPPING
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
col1, col2, col3 = st.columns(3)

col1.metric(
    "🔵 Kurang BAPP",
    df["Status"].str.contains("BAPP|KURANG", case=False, na=False).sum()
)

col2.metric(
    "🟡 Sedang Diproses",
    df["Status"].str.contains("PROSES|INSTALASI", case=False, na=False).sum()
)

col3.metric(
    "🟢 Selesai",
    df["Status"].str.contains("SELESAI", case=False, na=False).sum()
)

# ======================================================
# FILTER
# ======================================================
st.divider()
st.subheader("🔎 Filter Data")

col_f1, col_f2 = st.columns(2)

with col_f1:
    provinsi_filter = st.multiselect(
        "Provinsi",
        options=sorted(df["Propinsi"].dropna().unique()),
        default=sorted(df["Propinsi"].dropna().unique())
    )

with col_f2:
    jenjang_filter = st.multiselect(
        "Jenjang",
        options=sorted(df["Jenjang"].dropna().unique()),
        default=sorted(df["Jenjang"].dropna().unique())
    )

filtered_df = df[
    (df["Propinsi"].isin(provinsi_filter)) &
    (df["Jenjang"].isin(jenjang_filter))
]

# ======================================================
# TABLE
# ======================================================
st.divider()
st.subheader("📋 Detail Monitoring")

styled_df = filtered_df.style.applymap(
    status_style,
    subset=["Status"]
)

st.dataframe(styled_df, use_container_width=True)

# ======================================================
# FOOTER
# ======================================================
st.caption("⏱️ Auto refresh setiap 5 menit | Streamlit Dashboard")
