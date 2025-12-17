import streamlit as st
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
    menu_items={'About': "Dashboard Monitoring v5.4 - Fixed Column Detection"}
)

# ======================================================
# CSS - MODERN UI
# ======================================================
st.markdown("""
<style>
    /* Import Google Fonts */
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');
    
    /* Global Styles */
    * {
        font-family: 'Inter', sans-serif;
    }
    
    /* Main Container */
    .main {
        background: linear-gradient(135deg, #f5f7fa 0%, #c3cfe2 100%);
    }
    
    /* Dashboard Header */
    .dashboard-header {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 2.5rem;
        border-radius: 16px;
        color: white;
        text-align: center;
        margin-bottom: 2rem;
        box-shadow: 0 10px 30px rgba(102, 126, 234, 0.3);
    }
    
    .dashboard-header h1 {
        font-size: 2.5rem;
        font-weight: 700;
        margin-bottom: 0.5rem;
        text-shadow: 2px 2px 4px rgba(0,0,0,0.2);
    }
    
    .dashboard-header p {
        font-size: 1.1rem;
        opacity: 0.95;
        font-weight: 500;
    }
    
    /* Section Headers */
    .section-header {
        background: white;
        padding: 1.5rem;
        border-radius: 12px;
        margin: 1.5rem 0;
        box-shadow: 0 2px 8px rgba(0,0,0,0.08);
        border-left: 5px solid #667eea;
    }
    
    .section-header h3 {
        color: #2d3748;
        font-weight: 700;
        margin: 0;
        font-size: 1.5rem;
    }
    
    /* Metrics Cards */
    .stMetric {
        background: white;
        padding: 1.5rem;
        border-radius: 12px;
        box-shadow: 0 2px 12px rgba(0,0,0,0.08);
        transition: transform 0.2s, box-shadow 0.2s;
    }
    
    .stMetric:hover {
        transform: translateY(-4px);
        box-shadow: 0 4px 20px rgba(0,0,0,0.12);
    }
    
    .stMetric label {
        font-size: 0.85rem !important;
        font-weight: 600 !important;
        color: #4a5568 !important;
        text-transform: uppercase;
        letter-spacing: 0.5px;
    }
    
    .stMetric [data-testid="stMetricValue"] {
        font-size: 2rem !important;
        font-weight: 700 !important;
        color: #2d3748 !important;
    }
    
    .stMetric [data-testid="stMetricDelta"] {
        font-size: 1rem !important;
        font-weight: 600 !important;
    }
    
    /* Buttons */
    .stButton button {
        border-radius: 10px;
        font-weight: 600;
        padding: 0.6rem 1.2rem;
        transition: all 0.3s;
        border: none;
        box-shadow: 0 2px 6px rgba(0,0,0,0.1);
    }
    
    .stButton button:hover {
        transform: translateY(-2px);
        box-shadow: 0 4px 12px rgba(0,0,0,0.15);
    }
    
    .stButton button[kind="primary"] {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    }
    
    /* Input Fields */
    .stTextInput input {
        border-radius: 10px;
        border: 2px solid #e2e8f0;
        padding: 0.8rem;
        transition: border-color 0.3s;
    }
    
    .stTextInput input:focus {
        border-color: #667eea;
        box-shadow: 0 0 0 3px rgba(102, 126, 234, 0.1);
    }
    
    .stSelectbox select {
        border-radius: 10px;
        border: 2px solid #e2e8f0;
        padding: 0.8rem;
    }
    
    /* Expander */
    .streamlit-expanderHeader {
        background: white;
        border-radius: 10px;
        padding: 1rem;
        font-weight: 600;
        box-shadow: 0 2px 6px rgba(0,0,0,0.05);
    }
    
    /* Dataframe */
    .stDataFrame {
        border-radius: 12px;
        overflow: hidden;
        box-shadow: 0 4px 16px rgba(0,0,0,0.08);
    }
    
    /* Sidebar */
    [data-testid="stSidebar"] {
        background: linear-gradient(180deg, #f8f9fa 0%, #e9ecef 100%);
        padding: 2rem 1rem;
    }
    
    [data-testid="stSidebar"] .element-container {
        padding: 0.5rem 0;
    }
    
    /* Progress Bar */
    .stProgress > div > div > div {
        background: linear-gradient(90deg, #667eea 0%, #764ba2 100%) !important;
        border-radius: 10px !important;
        height: 24px !important;
    }
    
    .stProgress > div > div {
        background-color: #e2e8f0 !important;
        border-radius: 10px !important;
        height: 24px !important;
    }
    
    /* Info/Success/Warning Boxes */
    .stAlert {
        border-radius: 12px;
        border-left-width: 5px;
        padding: 1rem 1.5rem;
        box-shadow: 0 2px 8px rgba(0,0,0,0.08);
    }
    
    /* Download Buttons Container */
    .download-section {
        background: white;
        padding: 2rem;
        border-radius: 12px;
        box-shadow: 0 2px 12px rgba(0,0,0,0.08);
        margin-top: 2rem;
    }
    
    /* Footer */
    .dashboard-footer {
        text-align: center;
        padding: 2rem;
        margin-top: 3rem;
        color: #718096;
        font-weight: 500;
        background: white;
        border-radius: 12px;
        box-shadow: 0 2px 8px rgba(0,0,0,0.05);
    }
    
    /* Filter Section */
    .filter-container {
        background: white;
        padding: 2rem;
        border-radius: 12px;
        box-shadow: 0 2px 12px rgba(0,0,0,0.08);
        margin: 1.5rem 0;
    }
    
    /* Stats Badge */
    .stats-badge {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        padding: 1rem 2rem;
        border-radius: 10px;
        text-align: center;
        font-weight: 700;
        font-size: 1.2rem;
        box-shadow: 0 4px 12px rgba(102, 126, 234, 0.3);
        margin: 1rem 0;
    }
    
    /* URL Input Box */
    .url-input-section {
        background: #f0f9ff;
        padding: 1.5rem;
        border-radius: 12px;
        border-left: 5px solid #3b82f6;
        margin: 1rem 0;
        box-shadow: 0 2px 8px rgba(59, 130, 246, 0.1);
    }
    
    /* Column Detection Box */
    .detection-box {
        background: white;
        padding: 1.5rem;
        border-radius: 12px;
        box-shadow: 0 2px 8px rgba(0,0,0,0.06);
        margin: 1rem 0;
    }
    
    .detection-success {
        color: #10b981;
        font-weight: 600;
    }
    
    .detection-error {
        color: #ef4444;
        font-weight: 600;
    }
    
    /* Deduplication Stats */
    .dedup-stats {
        background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%);
        padding: 1.5rem;
        border-radius: 12px;
        color: white;
        margin: 1.5rem 0;
        box-shadow: 0 4px 12px rgba(240, 147, 251, 0.3);
    }
</style>
""", unsafe_allow_html=True)

# ======================================================
# UTILITIES
# ======================================================
def extract_sheet_id_and_gid(url):
    """Extract Sheet ID dan GID dari URL"""
    sheet_match = re.search(r"/spreadsheets/d/([a-zA-Z0-9-_]+)", url)
    if not sheet_match:
        return None, None
    
    sheet_id = sheet_match.group(1)
    gid_match = re.search(r"[#&]gid=(\d+)", url)
    gid = gid_match.group(1) if gid_match else "0"
    
    return sheet_id, gid

def load_sheet_by_gid(sheet_id, gid, sheet_label="Sheet"):
    """Load sheet berdasarkan GID"""
    try:
        url = f"https://docs.google.com/spreadsheets/d/{sheet_id}/export?format=csv&gid={gid}"
        df = pd.read_csv(url)
        
        if df.empty:
            raise Exception("Sheet kosong")
        
        df["__source"] = sheet_label
        df["__gid"] = gid
        
        return df, None
    except Exception as e:
        return None, str(e)

def normalize_status(val):
    """Normalisasi status sesuai Apps Script - UPDATED dengan Revisi"""
    if pd.isna(val) or val == "":
        return "Belum Dikerjakan"
    
    val = str(val).upper().strip()
    val = re.sub(r'[\u00A0\u200B\u200C\u200D\t\n\r]', ' ', val)
    val = re.sub(r'\s+', ' ', val)
    
    if "SELESAI" in val or "COMPLETE" in val:
        return "Selesai"
    elif "REVISI" in val or "DIREVISI" in val or "DI REVISI" in val:
        return "Revisi"
    elif "KURANG BAPP" in val or "BAPP" in val:
        return "Kurang BAPP"
    elif "BERMASALAH" in val or "MASALAH" in val or "ERROR" in val:
        return "Data Bermasalah"
    elif "PROSES" in val or "PENGERJAAN" in val or "INSTALASI" in val:
        return "Sedang Diproses"
    elif "BELUM" in val:
        return "Belum Dikerjakan"
    else:
        return "Sedang Diproses"

def get_status_priority(status):
    """Priority untuk deduplication - semakin kecil semakin prioritas"""
    priority_map = {
        "Selesai": 1,
        "Sedang Diproses": 2,
        "Revisi": 3,
        "Kurang BAPP": 4,
        "Data Bermasalah": 5,
        "Belum Dikerjakan": 6
    }
    return priority_map.get(status, 99)

def deduplicate_data(df):
    """Deduplikasi berdasarkan Trans. ID"""
    if "Trans. ID" not in df.columns:
        st.warning("⚠️ Kolom 'Trans. ID' tidak ditemukan, skip deduplikasi")
        return df, {}
    
    df["Status_Category"] = df["Status_Text"].apply(normalize_status)
    df["__priority"] = df["Status_Category"].apply(get_status_priority)
    
    before_count = len(df)
    duplicate_count = df.duplicated(subset=["Trans. ID"], keep=False).sum()
    
    df_sorted = df.sort_values(by=["Trans. ID", "__priority"])
    df_dedup = df_sorted.drop_duplicates(subset=["Trans. ID"], keep="first")
    df_dedup = df_dedup.drop(columns=["__priority"])
    
    after_count = len(df_dedup)
    removed_count = before_count - after_count
    
    dedup_info = {
        "before": before_count,
        "after": after_count,
        "removed": removed_count,
        "duplicates_found": duplicate_count
    }
    
    return df_dedup, dedup_info

def get_status_color(status):
    """Warna untuk setiap status"""
    colors = {
        "Belum Dikerjakan": "#94a3b8",
        "Sedang Diproses": "#f59e0b",
        "Revisi": "#ff00ff",
        "Kurang BAPP": "#00ffff",
        "Selesai": "#10b981",
        "Data Bermasalah": "#ef4444"
    }
    return colors.get(status, "#94a3b8")

def get_status_emoji(status):
    """Emoji untuk setiap status"""
    emojis = {
        "Belum Dikerjakan": "⏳",
        "Sedang Diproses": "⚙️",
        "Revisi": "🔄",
        "Kurang BAPP": "📄",
        "Selesai": "✅",
        "Data Bermasalah": "⚠️"
    }
    return emojis.get(status, "❓")

def find_column(df, possible_names):
    """Cari kolom dengan case-insensitive dan strip whitespace"""
    df_cols_cleaned = {}
    for col in df.columns:
        cleaned = str(col).lower().strip()
        cleaned = re.sub(r'\s+', ' ', cleaned)
        df_cols_cleaned[cleaned] = col
    
    for name in possible_names:
        cleaned_name = str(name).lower().strip()
        cleaned_name = re.sub(r'\s+', ' ', cleaned_name)
        if cleaned_name in df_cols_cleaned:
            return df_cols_cleaned[cleaned_name]
    
    return None

def load_multiple_sheets(url_list):
    """Load multiple sheets dari list URL"""
    all_dfs = []
    load_results = []
    
    for idx, url in enumerate(url_list):
        if not url.strip():
            continue
        
        sheet_id, gid = extract_sheet_id_and_gid(url.strip())
        
        if not sheet_id:
            load_results.append({
                "url": url[:50] + "...",
                "status": "❌ URL tidak valid",
                "rows": 0
            })
            continue
        
        sheet_label = f"Sheet-{idx+1} (GID:{gid})"
        df, error = load_sheet_by_gid(sheet_id, gid, sheet_label)
        
        if error:
            load_results.append({
                "url": url[:50] + "...",
                "status": f"❌ Error: {error}",
                "rows": 0
            })
        else:
            all_dfs.append(df)
            load_results.append({
                "url": url[:50] + "...",
                "status": "✅ Berhasil",
                "rows": len(df)
            })
    
    if not all_dfs:
        return None, load_results, None
    
    combined_df = pd.concat(all_dfs, ignore_index=True)
    return combined_df, load_results, None

# ======================================================
# INITIALIZE SESSION STATE
# ======================================================
if "url_inputs" not in st.session_state:
    st.session_state.url_inputs = ["https://docs.google.com/spreadsheets/d/1eX5CeXR4xzYPPHikbfdm2JUBpL5HQ3LC9cAA0X4m-QQ/edit#gid=0"]

# ======================================================
# HEADER
# ======================================================
st.markdown("""
<div class='dashboard-header'>
    <h1>📊 Dashboard Monitoring Pekerjaan</h1>
    <p>Multi-Sheet GID Support • Smart Deduplication • Manual Refresh • v5.4 Fixed</p>
</div>
""", unsafe_allow_html=True)

# ======================================================
# SIDEBAR
# ======================================================
with st.sidebar:
    st.markdown("### ⚙️ Input Data Source")
    st.markdown("---")
    
    st.markdown("#### 🔗 Input URL Sheet (GID)")
    
    urls_to_remove = []
    for idx, url in enumerate(st.session_state.url_inputs):
        col1, col2 = st.columns([4, 1])
        with col1:
            new_url = st.text_input(
                f"URL #{idx+1}",
                value=url,
                key=f"url_{idx}",
                label_visibility="collapsed"
            )
            st.session_state.url_inputs[idx] = new_url
        with col2:
            if len(st.session_state.url_inputs) > 1:
                if st.button("🗑️", key=f"del_{idx}", help="Hapus URL ini"):
                    urls_to_remove.append(idx)
    
    if urls_to_remove:
        for idx in sorted(urls_to_remove, reverse=True):
            st.session_state.url_inputs.pop(idx)
        st.rerun()
    
    st.markdown("---")
    
    col_add1, col_add2 = st.columns([2, 2])
    with col_add1:
        if st.button("➕ Tambah URL", use_container_width=True):
            st.session_state.url_inputs.append("")
            st.rerun()
    
    with col_add2:
        if st.button("🔄 Reset Semua", use_container_width=True):
            st.session_state.url_inputs = [""]
            st.rerun()
    
    st.info(f"📊 Total: {len(st.session_state.url_inputs)} URL")
    st.markdown("---")
    
    col1, col2 = st.columns(2)
    with col1:
        load_btn = st.button("🔄 Load Data", use_container_width=True, type="primary")
    with col2:
        clear_btn = st.button("🗑️ Clear Cache", use_container_width=True)
    
    if clear_btn:
        for key in ["df", "load_results", "dedup_info", "last_load"]:
            if key in st.session_state:
                del st.session_state[key]
        st.success("✅ Cache cleared!")
        st.rerun()
    
    st.markdown("---")
    
    if st.session_state.get("last_load"):
        st.success(f"✅ Last Load: {st.session_state['last_load'].strftime('%H:%M:%S')}")
    
    st.markdown("---")
    
    with st.expander("📖 Cara Pakai"):
        st.markdown("""
        **1. Tambah URL:**
        - Klik "➕ Tambah URL"
        
        **2. Copy URL dengan GID:**
        - Buka Google Sheets
        - Klik tab sheet yang diinginkan
        - Copy URL (sudah ada #gid=xxx)
        
        **3. Permission:**
        - Share → Anyone with link → Viewer
        
        **4. Load Data:**
        - Klik "🔄 Load Data"
        """)

# ======================================================
# MAIN - LOAD DATA
# ======================================================
url_list = [url.strip() for url in st.session_state.url_inputs if url.strip()]

if not url_list:
    st.info("👆 Masukkan minimal 1 URL di sidebar")
    st.stop()

with st.expander(f"📋 URL yang tersimpan ({len(url_list)} sheet)"):
    for i, url in enumerate(url_list, 1):
        sheet_id, gid = extract_sheet_id_and_gid(url)
        if sheet_id:
            st.success(f"{i}. Sheet ID: `{sheet_id}` | GID: `{gid}`")
        else:
            st.error(f"{i}. ❌ URL tidak valid")

if load_btn:
    with st.spinner("⏳ Memuat data..."):
        df, load_results, _ = load_multiple_sheets(url_list)
        
        st.markdown('<div class="section-header"><h3>📊 Hasil Loading</h3></div>', unsafe_allow_html=True)
        result_df = pd.DataFrame(load_results)
        st.dataframe(result_df, use_container_width=True, hide_index=True)
        
        if df is None:
            st.error("❌ Semua sheet gagal dimuat!")
            st.stop()
        
        st.session_state["df_raw"] = df.copy()
        st.session_state["load_results"] = load_results
        st.session_state["last_load"] = datetime.now()
        st.success(f"✅ Data berhasil dimuat: {len(df):,} baris")

df = st.session_state.get("df_raw")
if df is None:
    st.warning("⚠️ Klik tombol '🔄 Load Data' di sidebar")
    st.stop()

# ======================================================
# COLUMN MAPPING & VALIDATION
# ======================================================
st.markdown('<div class="section-header"><h3>🔧 Deteksi & Mapping Kolom</h3></div>', unsafe_allow_html=True)

trans_id_col = find_column(df, ["trans. id", "trans id", "transid", "trans_id", "id transaksi", "id"])
nama_col = find_column(df, ["nama", "name", "sekolah", "nama sekolah"])
jenjang_col = find_column(df, ["jenjang", "level", "tingkat", "jenjang pendidikan"])
kabupaten_col = find_column(df, ["kabupaten", "kab", "regency", "kab/kota", "kabupaten/kota"])
propinsi_col = find_column(df, ["propinsi", "provinsi", "province", "prov"])
npsn_col = find_column(df, ["npsn"])
status_col = find_column(df, ["status_text", "status text", "status", "status pengerjaan", "keterangan"])

with st.expander("🔍 Hasil Deteksi Kolom (Klik untuk lihat detail)"):
    col1, col2 = st.columns(2)
    with col1:
        st.markdown("#### **Kolom yang ditemukan:**")
        st.markdown(f"**Trans ID:** `{trans_id_col if trans_id_col else '❌ TIDAK DITEMUKAN'}`")
        st.markdown(f"**Nama:** `{nama_col if nama_col else '❌ TIDAK DITEMUKAN'}`")
        st.markdown(f"**Jenjang:** `{jenjang_col if jenjang_col else '❌ TIDAK DITEMUKAN'}`")
        st.markdown(f"**Kabupaten:** `{kabupaten_col if kabupaten_col else '❌ TIDAK DITEMUKAN'}`")
        st.markdown(f"**Propinsi:** `{propinsi_col if propinsi_col else '❌ TIDAK DITEMUKAN'}`")
        st.markdown(f"**NPSN:** `{npsn_col if npsn_col else '❌ TIDAK DITEMUKAN'}`")
        st.markdown(f"**Status:** `{status_col if status_col else '❌ TIDAK DITEMUKAN'}`")
    
    with col2:
        st.markdown("#### **Semua kolom di spreadsheet:**")
        st.dataframe(pd.DataFrame({"Nama Kolom": df.columns.tolist()}), use_container_width=True, height=300)

column_mapping = {}
if trans_id_col: column_mapping[trans_id_col] = "Trans. ID"
if nama_col: column_mapping[nama_col] = "Nama"
if jenjang_col: column_mapping[jenjang_col] = "Jenjang"
if kabupaten_col: column_mapping[kabupaten_col] = "Kabupaten"
if propinsi_col: column_mapping[propinsi_col] = "Propinsi"
if npsn_col: column_mapping[npsn_col] = "NPSN"
if status_col: column_mapping[status_col] = "Status_Text"

if column_mapping:
    df = df.rename(columns=column_mapping)
    st.success(f"✅ {len(column_mapping)} kolom berhasil di-rename")
else:
    st.error("❌ Tidak ada kolom yang berhasil di-detect!")
    st.stop()

required_columns = ["Trans. ID", "Nama", "Jenjang", "Kabupaten", "Propinsi", "NPSN", "Status_Text"]
missing = [c for c in required_columns if c not in df.columns]

if missing:
    st.error(f"❌ Kolom wajib tidak ditemukan: **{', '.join(missing)}**")
    st.warning("⚠️ Periksa nama kolom di spreadsheet atau tambahkan kolom yang hilang")
    
    with st.expander("💡 Solusi"):
        st.markdown("""
        **Kolom yang dibutuhkan:**
        1. Trans. ID (ID Transaksi)
        2. Nama (Nama Sekolah)
        3. Jenjang
        4. Kabupaten
        5. Propinsi
        6. NPSN
        7. Status_Text (Kolom status pengerjaan)
        
        **Jika kolom Status_Text tidak ada:**
        - Buat kolom baru bernama "Status_Text" atau "Status"
        - Atau jalankan Apps Script untuk auto-generate
        """)
    st.stop()

df, dedup_info = deduplicate_data(df)

if dedup_info:
    st.markdown("#### 📊 Deduplication Summary")
    col_d1, col_d2, col_d3 = st.columns(3)
    col_d1.metric("📥 Data Awal", f"{dedup_info['before']:,}")
    col_d2.metric("🗑️ Duplikat Dihapus", f"{dedup_info['removed']:,}")
    col_d3.metric("✅ Data Final", f"{dedup_info['after']:,}")

st.session_state["df"] = df
st.session_state["dedup_info"] = dedup_info

# ======================================================
# METRICS
# ======================================================
st.markdown('<div class="section-header"><h3>📈 Ringkasan Status</h3></div>', unsafe_allow_html=True)

total_belum = (df.Status_Category == "Belum Dikerjakan").sum()
total_proses = (df.Status_Category == "Sedang Diproses").sum()
total_revisi = (df.Status_Category == "Revisi").sum()
total_bapp = (df.Status_Category == "Kurang BAPP").sum()
total_selesai = (df.Status_Category == "Selesai").sum()
total_bermasalah = (df.Status_Category == "Data Bermasalah").sum()

col1, col2, col3 = st.columns(3)
with col1:
    st.metric(
        "⏳ BELUM DICEK",
        total_belum,
        f"{(total_belum/len(df)*100):.1f}%",
        help="NOT CHECKED / BELUM DIKERJAKAN"
    )
    st.caption("🇬🇧 NOT CHECKED")
    
    st.metric(
        "⚙️ PROSES",
        total_proses,
        f"{(total_proses/len(df)*100):.1f}%",
        help="ALREADY FOLLOWED UP TO THE COORDINATOR"
    )
    st.caption("🇬🇧 ALREADY FOLLOWED UP")

with col2:
    st.metric(
        "🔄 SUDAH DICEK",
        total_revisi,
        f"{(total_revisi/len(df)*100):.1f}%",
        help="ON CHECK / REVISI"
    )
    st.caption("🇬🇧 ON CHECK / REVISION")
    
    st.metric(
        "📄 KURANG BAPP",
        total_bapp,
        f"{(total_bapp/len(df)*100):.1f}%",
        help="BAPP DATA LACK"
    )
    st.caption("🇬🇧 BAPP DATA LACK")

with col3:
    st.metric(
        "✅ SELESAI",
        total_selesai,
        f"{(total_selesai/len(df)*100):.1f}%",
        help="DONE / COMPLETED"
    )
    st.caption("🇬🇧 DONE / COMPLETED")
    
    st.metric(
        "⚠️ BERMASALAH",
        total_bermasalah,
        f"{(total_bermasalah/len(df)*100):.1f}%",
        help="CONSTRAINED DATA"
    )
    st.caption("🇬🇧 CONSTRAINED DATA")

st.markdown("---")

if len(df) > 0:
    progress_pct = (total_selesai / len(df)) * 100
    
    st.markdown("#### 🎯 Progress Keseluruhan / Overall Progress")
    st.progress(total_selesai / len(df))
    
    st.markdown(f"""
    <div class='stats-badge'>
        📊 Progress: {progress_pct:.1f}% ({total_selesai:,}/{len(df):,}) - 
        {total_selesai:,} Selesai dari {len(df):,} Total Data
    </div>
    """, unsafe_allow_html=True)

# ======================================================
# FILTER
# ======================================================
st.markdown('<div class="section-header"><h3>🔎 Filter Data</h3></div>', unsafe_allow_html=True)

col_f1, col_f2, col_f3 = st.columns(3)

with col_f1:
    status_filter = st.selectbox(
        "📊 Status",
        ["Semua Status", "Belum Dikerjakan", "Sedang Diproses", "Revisi", "Kurang BAPP", "Selesai", "Data Bermasalah"]
    )

with col_f2:
    if "__source" in df.columns:
        source_list = ["Semua Source"] + sorted(df["__source"].unique().tolist())
        source_filter = st.selectbox("📑 Source", source_list)
    else:
        source_filter = "Semua Source"

with col_f3:
    search_text = st.text_input("🔍 Cari Nama/NPSN/Kabupaten", "")

filtered_df = df.copy()

if status_filter != "Semua Status":
    filtered_df = filtered_df[filtered_df["Status_Category"] == status_filter]

if source_filter != "Semua Source":
    filtered_df = filtered_df[filtered_df["__source"] == source_filter]

if search_text:
    mask = pd.Series([False] * len(filtered_df))
    for col in ["Nama", "NPSN", "Kabupaten"]:
        if col in filtered_df.columns:
            mask = mask | filtered_df[col].astype(str).str.contains(search_text, case=False, na=False)
    filtered_df = filtered_df[mask]

st.markdown(f"""
<div class='stats-badge' style='background: linear-gradient(135deg, #3b82f6 0%, #8b5cf6 100%);'>
    📊 Menampilkan {len(filtered_df):,} dari {len(df):,} baris
</div>
""", unsafe_allow_html=True)

# ======================================================
# TABLE
# ======================================================
st.markdown('<div class="section-header"><h3>📋 Data Detail</h3></div>', unsafe_allow_html=True)

display_columns = ["__source", "Trans. ID", "Nama", "Jenjang", "Kabupaten", "Propinsi", "NPSN", "Status_Text"]

def style_status_cell(val):
    cat = normalize_status(val)
    color = get_status_color(cat)
    return f"background-color:{color};color:white;font-weight:600;padding:8px;border-radius:5px;text-align:center;"

if not filtered_df.empty:
    st.dataframe(
        filtered_df[display_columns].style.applymap(
            style_status_cell,
            subset=["Status_Text"]
        ),
        use_container_width=True,
        height=500
    )
else:
    st.warning("⚠️ Tidak ada data yang sesuai dengan filter")

# ======================================================
# DOWNLOAD
# ======================================================
st.markdown('<div class="section-header"><h3>📥 Download Data</h3></div>', unsafe_allow_html=True)

timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')

col_dl1, col_dl2, col_dl3 = st.columns([2, 2, 2])

with col_dl1:
    st.download_button(
        "📥 Download Data Terfilter",
        filtered_df.to_csv(index=False).encode('utf-8'),
        f"filtered_{timestamp}.csv",
        "text/csv",
        use_container_width=True
    )

with col_dl2:
    st.download_button(
        "📥 Download Semua Data",
        df.to_csv(index=False).encode('utf-8'),
        f"all_{timestamp}.csv",
        "text/csv",
        use_container_width=True
    )

with col_dl3:
    if not filtered_df.empty:
        excel_buffer = pd.ExcelWriter(f"data_{timestamp}.xlsx", engine='xlsxwriter')
        filtered_df.to_excel(excel_buffer, index=False, sheet_name='Data')
        excel_buffer.close()

# ======================================================
# FOOTER
# ======================================================
st.markdown("""
<div class='dashboard-footer'>
    <h4>🚀 Dashboard Monitoring v5.4</h4>
    <p>Fixed Column Detection • Smart Deduplication • Multi-Sheet Support</p>
    <p style='font-size: 0.9rem; margin-top: 1rem;'>Developed with ❤️ using Streamlit</p>
</div>
""", unsafe_allow_html=True)
