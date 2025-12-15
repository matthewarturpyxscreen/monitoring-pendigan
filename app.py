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
    menu_items={'About': "Dashboard Monitoring v5.0 - Professional Edition"}
)

REFRESH_INTERVAL = 300  # 5 menit

# ======================================================
# AUTO REFRESH
# ======================================================
st.markdown(
    f"""<meta http-equiv="refresh" content="{REFRESH_INTERVAL}">""",
    unsafe_allow_html=True
)

# ======================================================
# PROFESSIONAL CSS DESIGN
# ======================================================
st.markdown("""
<style>
    /* Import Professional Font */
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap');
    
    /* Global Styles */
    * {
        font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
    }
    
    /* Main Container */
    .block-container {
        padding-top: 2rem;
        padding-bottom: 2rem;
        max-width: 1400px;
    }
    
    /* Header Profesional */
    .dashboard-header {
        background: linear-gradient(135deg, #1e293b 0%, #0f172a 100%);
        padding: 2.5rem 3rem;
        border-radius: 12px;
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1), 0 2px 4px -1px rgba(0, 0, 0, 0.06);
        margin-bottom: 2rem;
        border: 1px solid rgba(255, 255, 255, 0.1);
    }
    
    .dashboard-header h1 {
        color: #ffffff;
        font-size: 2rem;
        font-weight: 800;
        margin: 0;
        letter-spacing: -0.5px;
    }
    
    .dashboard-header p {
        color: #cbd5e1;
        font-size: 0.9rem;
        margin: 0.5rem 0 0 0;
        font-weight: 500;
    }
    
    /* Section Headers */
    .section-header {
        background: #ffffff;
        padding: 1.25rem 1.5rem;
        border-radius: 8px;
        margin: 1.5rem 0 1rem 0;
        border-left: 4px solid #0f172a;
        box-shadow: 0 1px 3px 0 rgba(0, 0, 0, 0.1);
    }
    
    .section-header h3 {
        color: #0f172a;
        font-size: 1.1rem;
        font-weight: 700;
        margin: 0;
        letter-spacing: -0.3px;
    }
    
    /* Metric Cards */
    [data-testid="stMetricValue"] {
        font-size: 2rem;
        font-weight: 800;
        color: #0f172a;
    }
    
    [data-testid="stMetricLabel"] {
        font-size: 0.85rem;
        font-weight: 600;
        color: #64748b;
        text-transform: uppercase;
        letter-spacing: 0.5px;
    }
    
    [data-testid="stMetricDelta"] {
        font-size: 0.85rem;
        font-weight: 600;
    }
    
    /* Buttons */
    .stButton > button {
        border-radius: 6px;
        font-weight: 600;
        letter-spacing: 0.3px;
        border: none;
        transition: all 0.2s ease;
        text-transform: uppercase;
        font-size: 0.85rem;
    }
    
    .stButton > button:hover {
        transform: translateY(-1px);
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1);
    }
    
    /* Input Fields */
    .stTextInput > div > div > input {
        border-radius: 6px;
        border: 2px solid #e2e8f0;
        font-weight: 500;
        transition: all 0.2s ease;
    }
    
    .stTextInput > div > div > input:focus {
        border-color: #0f172a;
        box-shadow: 0 0 0 3px rgba(15, 23, 42, 0.1);
    }
    
    /* Select Boxes */
    .stSelectbox > div > div {
        border-radius: 6px;
        border: 2px solid #e2e8f0;
        font-weight: 500;
    }
    
    /* Data Tables */
    .stDataFrame {
        border-radius: 8px;
        overflow: hidden;
        box-shadow: 0 1px 3px 0 rgba(0, 0, 0, 0.1);
    }
    
    /* Expander */
    .streamlit-expanderHeader {
        background-color: #f8fafc;
        border-radius: 6px;
        font-weight: 600;
        color: #0f172a;
        border: 1px solid #e2e8f0;
    }
    
    /* Progress Bar */
    .stProgress > div > div > div > div {
        background-color: #10b981;
        border-radius: 4px;
    }
    
    /* Tabs */
    .stTabs [data-baseweb="tab-list"] {
        gap: 8px;
        background-color: #f8fafc;
        padding: 8px;
        border-radius: 8px;
    }
    
    .stTabs [data-baseweb="tab"] {
        border-radius: 6px;
        font-weight: 600;
        color: #64748b;
        padding: 8px 16px;
    }
    
    .stTabs [aria-selected="true"] {
        background-color: #0f172a;
        color: #ffffff;
    }
    
    /* Sidebar */
    [data-testid="stSidebar"] {
        background-color: #f8fafc;
        border-right: 1px solid #e2e8f0;
    }
    
    [data-testid="stSidebar"] h1 {
        color: #0f172a;
        font-weight: 800;
        font-size: 1.25rem;
    }
    
    /* Info/Warning/Error Boxes */
    .stAlert {
        border-radius: 8px;
        border: none;
        font-weight: 500;
    }
    
    /* Footer */
    .dashboard-footer {
        text-align: center;
        padding: 2rem 1rem;
        margin-top: 3rem;
        border-top: 2px solid #e2e8f0;
    }
    
    .dashboard-footer p {
        color: #64748b;
        font-weight: 600;
        margin: 0.25rem 0;
        font-size: 0.9rem;
    }
    
    /* Download Buttons */
    .stDownloadButton > button {
        background-color: #0f172a;
        color: white;
        border-radius: 6px;
        font-weight: 600;
        border: none;
        padding: 0.5rem 1rem;
    }
    
    .stDownloadButton > button:hover {
        background-color: #1e293b;
        transform: translateY(-1px);
    }
    
    /* Hide Streamlit Branding */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    
    /* Custom Spacing */
    .element-container {
        margin-bottom: 0.5rem;
    }
    
    /* Status Badge Styling */
    .status-badge {
        display: inline-block;
        padding: 4px 12px;
        border-radius: 4px;
        font-weight: 600;
        font-size: 0.85rem;
        text-transform: uppercase;
        letter-spacing: 0.5px;
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
    """Normalisasi status sesuai Apps Script"""
    if pd.isna(val) or val == "":
        return "Belum Dikerjakan"
    
    val = str(val).upper().strip()
    val = re.sub(r'[\u00A0\u200B\u200C\u200D\t\n\r]', ' ', val)
    val = re.sub(r'\s+', ' ', val)
    
    if "BERMASALAH" in val or "MASALAH" in val or "ERROR" in val or "GAGAL" in val:
        return "Data Bermasalah"
    elif "SELESAI" in val or "COMPLETE" in val or "SUKSES" in val:
        return "Selesai"
    elif "KURANG BAPP" in val or "BAPP" in val or "KURANG" in val:
        return "Kurang BAPP"
    elif "PROSES" in val or "PENGERJAAN" in val or "INSTALASI" in val or "DIKERJAKAN" in val:
        return "Sedang Diproses"
    elif "BELUM" in val:
        return "Belum Dikerjakan"
    else:
        return "Sedang Diproses"

def get_status_priority(status):
    """Priority untuk deduplication"""
    priority_map = {
        "Selesai": 1,
        "Sedang Diproses": 2,
        "Kurang BAPP": 3,
        "Data Bermasalah": 4,
        "Belum Dikerjakan": 5
    }
    return priority_map.get(status, 99)

def deduplicate_data(df):
    """Deduplikasi berdasarkan Trans. ID dengan prioritas status"""
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
        "Kurang BAPP": "#3b82f6",
        "Selesai": "#10b981",
        "Data Bermasalah": "#ef4444"
    }
    return colors.get(status, "#94a3b8")

def get_status_emoji(status):
    """Emoji untuk setiap status"""
    emojis = {
        "Belum Dikerjakan": "⏳",
        "Sedang Diproses": "⚙️",
        "Kurang BAPP": "📄",
        "Selesai": "✅",
        "Data Bermasalah": "⚠️"
    }
    return emojis.get(status, "❓")

@st.cache_data(ttl=REFRESH_INTERVAL, show_spinner=False)
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
    deduped_df, dedup_info = deduplicate_data(combined_df)
    
    return deduped_df, load_results, dedup_info

# ======================================================
# HEADER
# ======================================================
st.markdown(f"""
<div class='dashboard-header'>
    <h1>📊 DASHBOARD MONITORING PEKERJAAN</h1>
    <p>MULTI-SHEET GID SUPPORT • SMART DEDUPLICATION • LAST UPDATE: {datetime.now().strftime('%d %B %Y, %H:%M:%S WIB').upper()}</p>
</div>
""", unsafe_allow_html=True)

# ======================================================
# SIDEBAR
# ======================================================
with st.sidebar:
    st.title("⚙️ KONFIGURASI")
    
    st.markdown("### 🔗 URL DATA SOURCE")
    
    if "url_inputs" not in st.session_state:
        st.session_state.url_inputs = ["https://docs.google.com/spreadsheets/d/1eX5CeXR4xzYPPHikbfdm2JUBpL5HQ3LC9cAA0X4m-QQ/edit#gid=0"]
    
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
                if st.button("🗑️", key=f"del_{idx}", help="Hapus URL"):
                    urls_to_remove.append(idx)
    
    for idx in sorted(urls_to_remove, reverse=True):
        st.session_state.url_inputs.pop(idx)
    
    col_add1, col_add2 = st.columns([2, 2])
    with col_add1:
        if st.button("➕ TAMBAH", use_container_width=True):
            st.session_state.url_inputs.append("")
            st.rerun()
    
    with col_add2:
        if st.button("🔄 RESET", use_container_width=True):
            st.session_state.url_inputs = [""]
            st.rerun()
    
    st.caption(f"**TOTAL: {len(st.session_state.url_inputs)} URL**")
    
    st.markdown("---")
    
    col1, col2 = st.columns(2)
    with col1:
        load_btn = st.button("🔄 LOAD DATA", use_container_width=True, type="primary")
    with col2:
        clear_btn = st.button("🗑️ CLEAR CACHE", use_container_width=True)
    
    if clear_btn:
        st.cache_data.clear()
        st.rerun()
    
    st.markdown("---")
    
    with st.expander("📖 PETUNJUK PENGGUNAAN"):
        st.markdown("""
        **CARA MENGGUNAKAN:**
        
        1. **Tambah URL**
           - Klik tombol "➕ TAMBAH"
           - Input URL dengan format GID
        
        2. **Format URL**
           ```
           https://docs.google.com/.../edit#gid=xxx
           ```
        
        3. **Hapus URL**
           - Klik tombol 🗑️ di samping URL
        
        4. **Load Data**
           - Klik "🔄 LOAD DATA"
           - Sistem akan memproses semua sheet
        
        5. **Permission**
           - Share → Anyone with link → Viewer
        """)
    
    with st.expander("🎯 PRIORITAS STATUS"):
        st.markdown("""
        **URUTAN PRIORITAS DEDUPLIKASI:**
        
        1. ✅ SELESAI (Prioritas Tertinggi)
        2. ⚙️ SEDANG DIPROSES
        3. 📄 KURANG BAPP
        4. ⚠️ DATA BERMASALAH
        5. ⏳ BELUM DIKERJAKAN (Prioritas Terendah)
        
        *Sistem otomatis memilih data dengan status terbaik*
        """)

# ======================================================
# MAIN - LOAD DATA
# ======================================================
url_list = [url.strip() for url in st.session_state.url_inputs if url.strip()]

if not url_list:
    st.info("👆 **MASUKKAN MINIMAL 1 URL DI SIDEBAR**")
    st.stop()

with st.expander(f"📋 **URL YANG AKAN DIPROSES ({len(url_list)} SHEET)**"):
    for i, url in enumerate(url_list, 1):
        sheet_id, gid = extract_sheet_id_and_gid(url)
        if sheet_id:
            st.success(f"**{i}.** Sheet ID: `{sheet_id}` | GID: `{gid}`")
        else:
            st.error(f"**{i}.** ❌ URL TIDAK VALID: {url[:50]}...")

if load_btn or "df" not in st.session_state:
    with st.spinner("⏳ MEMUAT DATA DARI SEMUA SHEET..."):
        df, load_results, dedup_info = load_multiple_sheets(url_list)
        
        st.markdown("### 📊 HASIL LOADING")
        result_df = pd.DataFrame(load_results)
        st.dataframe(result_df, use_container_width=True, hide_index=True)
        
        if df is None:
            st.error("❌ SEMUA SHEET GAGAL DIMUAT. PERIKSA URL DAN PERMISSION!")
            st.stop()
        
        if dedup_info:
            st.success(f"✅ DATA BERHASIL DIMUAT!")
            
            col_d1, col_d2, col_d3 = st.columns(3)
            col_d1.metric("📥 DATA AWAL", f"{dedup_info['before']:,}")
            col_d2.metric("🗑️ DUPLIKAT DIHAPUS", f"{dedup_info['removed']:,}")
            col_d3.metric("✅ DATA FINAL", f"{dedup_info['after']:,}")
            
            if dedup_info['removed'] > 0:
                st.info(f"💡 Ditemukan **{dedup_info['duplicates_found']:,} data duplikat**. Sistem otomatis memilih data dengan status terlengkap.")
        
        st.session_state["df"] = df
        st.session_state["load_results"] = load_results
        st.session_state["dedup_info"] = dedup_info
        st.session_state["last_load"] = datetime.now()

df = st.session_state.get("df")
if df is None:
    st.warning("⚠️ **KLIK TOMBOL 'LOAD DATA' DI SIDEBAR UNTUK MEMULAI**")
    st.stop()

dedup_info = st.session_state.get("dedup_info", {})

# ======================================================
# INFO BOXES
# ======================================================
st.markdown("---")
col_info1, col_info2, col_info3, col_info4 = st.columns(4)

col_info1.metric("📋 TOTAL DATA", f"{len(df):,}")
col_info2.metric("📑 SHEET LOADED", len(url_list))
if dedup_info:
    col_info3.metric("🗑️ DUPLIKAT REMOVED", f"{dedup_info.get('removed', 0):,}")
if "last_load" in st.session_state:
    col_info4.metric("🕐 LAST LOAD", st.session_state["last_load"].strftime("%H:%M:%S"))

# ======================================================
# VALIDASI KOLOM
# ======================================================
required_columns = ["Trans. ID", "Nama", "Jenjang", "Kabupaten", "Propinsi", "NPSN"]

if "Status_Text" not in df.columns:
    st.error("❌ **KOLOM 'Status_Text' TIDAK DITEMUKAN!**")
    st.warning("⚠️ Jalankan Apps Script untuk generate kolom Status_Text")
    st.stop()

missing = [c for c in required_columns if c not in df.columns]
if missing:
    st.error(f"❌ **KOLOM TIDAK DITEMUKAN:** {', '.join(missing)}")
    with st.expander("Lihat kolom tersedia"):
        st.write(df.columns.tolist())
    st.stop()

optional_columns = ["Keterangan", "Petugas", "PIC", "Telp", "Alamat"]
display_columns = ["__source"] + required_columns + ["Status_Text"]

for col in optional_columns:
    if col in df.columns:
        display_columns.append(col)

# ======================================================
# PROCESS STATUS
# ======================================================
if "Status_Category" not in df.columns:
    df["Status_Category"] = df["Status_Text"].apply(normalize_status)

with st.expander("🔍 **DEBUG: CEK STATUS TEXT DARI SPREADSHEET**"):
    st.markdown("**SAMPLE 20 DATA PERTAMA:**")
    
    debug_cols = ["__source", "Trans. ID", "Nama", "Status_Text", "Status_Category"]
    debug_df = df[debug_cols].head(20)
    
    st.dataframe(debug_df, use_container_width=True)
    
    st.markdown("---")
    st.markdown("**UNIQUE STATUS TEXT TERDETEKSI:**")
    unique_status = df["Status_Text"].value_counts().reset_index()
    unique_status.columns = ["Status Text", "Jumlah"]
    st.dataframe(unique_status, use_container_width=True)
    
    st.info("💡 Cek apakah 'DATA BERMASALAH' muncul di list. Jika tidak, Apps Script belum dijalankan.")

# ======================================================
# METRICS
# ======================================================
st.markdown("---")
st.markdown('<div class="section-header"><h3>📈 RINGKASAN STATUS</h3></div>', unsafe_allow_html=True)

c1, c2, c3, c4, c5 = st.columns(5)

total_belum = (df.Status_Category == "Belum Dikerjakan").sum()
total_proses = (df.Status_Category == "Sedang Diproses").sum()
total_bapp = (df.Status_Category == "Kurang BAPP").sum()
total_selesai = (df.Status_Category == "Selesai").sum()
total_bermasalah = (df.Status_Category == "Data Bermasalah").sum()

c1.metric("⏳ BELUM", total_belum, 
          delta=f"{(total_belum/len(df)*100):.1f}%" if len(df) > 0 else "0%")
c2.metric("⚙️ PROSES", total_proses,
          delta=f"{(total_proses/len(df)*100):.1f}%" if len(df) > 0 else "0%")
c3.metric("📄 KURANG BAPP", total_bapp,
          delta=f"{(total_bapp/len(df)*100):.1f}%" if len(df) > 0 else "0%")
c4.metric("✅ SELESAI", total_selesai,
          delta=f"{(total_selesai/len(df)*100):.1f}%" if len(df) > 0 else "0%")
c5.metric("⚠️ BERMASALAH", total_bermasalah,
          delta=f"{(total_bermasalah/len(df)*100):.1f}%" if len(df) > 0 else "0%")

total = len(df)
if total > 0:
    progress_pct = (total_selesai / total) * 100
    st.progress(total_selesai / total)
    st.markdown(f"**🎯 PROGRESS KESELURUHAN: {progress_pct:.1f}% ({total_selesai:,} dari {total:,} sekolah)**")

# ======================================================
# FILTER
# ======================================================
st.markdown("---")
st.markdown("### 🔎 FILTER DATA")

col_filter1, col_filter2, col_filter3 = st.columns(3)

with col_filter1:
    status_filter = st.selectbox(
        "📊 STATUS",
        ["Semua Status", "Belum Dikerjakan", "Sedang Diproses", "Kurang BAPP", "Selesai", "Data Bermasalah"]
    )

with col_filter2:
    if "__source" in df.columns:
        source_list = ["Semua Source"] + sorted(df["__source"].unique().tolist())
        source_filter = st.selectbox("📑 SOURCE SHEET", source_list)
    else:
        source_filter = "Semua Source"

with col_filter3:
    search_text = st.text_input("🔍 CARI (Nama/NPSN/Kabupaten)", "")

filtered_df = df.copy()

if status_filter != "Semua Status":
    filtered_df = filtered_df[filtered_df["Status_Category"] == status_filter]

if source_filter != "Semua Source" and "__source" in filtered_df.columns:
    filtered_df = filtered_df[filtered_df["__source"] == source_filter]

if search_text:
    search_cols = ["Nama", "NPSN", "Kabupaten"]
    mask = pd.Series([False] * len(filtered_df))
    for col in search_cols:
        if col in filtered_df.columns:
            mask = mask | filtered_df[col].astype(str).str.contains(search_text, case=False, na=False)
    filtered_df = filtered_df[mask]

st.markdown(f"**MENAMPILKAN {len(filtered_df):,} DARI {len(df):,} BARIS**")

# ======================================================
# TABLE
# ======================================================
st.markdown("---")
st.markdown('<div class="section-header"><h3>📋 DATA DETAIL</h3></div>', unsafe_allow_html=True)

def style_status_cell(val):
    """Style untuk kolom status"""
    cat = normalize_status(val)
    color = get_status_color(cat)
    return f"background-color:{color};color:white;font-weight:700;padding:8px;border-radius:4px;text-align:center;text-transform:uppercase;letter-spacing:0.5px;font-size:0.85rem;"

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
    st.warning("⚠️ **TIDAK ADA DATA YANG SESUAI DENGAN FILTER**")

# ======================================================
# DOWNLOAD
# ======================================================
st.markdown("---")
col_dl1, col_dl2 = st.columns(2)

timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')

with col_dl1:
    st.download_button(
        "📥 DOWNLOAD HASIL FILTER (CSV)",
        filtered_df.to_csv(index=False).encode('utf-8'),
        f"monitoring_filtered_{timestamp}.csv",
        "text/csv",
        use_container_width=True
    )

with col_dl2:
    st.download_button(
        "📥 Download Semua Data (CSV)",
        df.to_csv(index=False).encode('utf-8'),
        f"monitoring_all_{timestamp}.csv",
        "text/csv",
        use_container_width=True
    )

# ======================================================
# ANALYTICS
# ======================================================
st.markdown("---")
with st.expander("📊 **Analytics & Breakdown**"):
    
    tab1, tab2, tab3 = st.tabs(["📈 Per Source", "🔍 Deduplikasi Info", "📋 Summary"])
    
    with tab1:
        if "__source" in df.columns:
            st.subheader("Status per Source Sheet")
            source_summary = df.groupby(["__source", "Status_Category"]).size().reset_index(name="Jumlah")
            pivot_summary = source_summary.pivot(index="__source", columns="Status_Category", values="Jumlah").fillna(0).astype(int)
            pivot_summary["TOTAL"] = pivot_summary.sum(axis=1)
            st.dataframe(pivot_summary, use_container_width=True)
    
    with tab2:
        st.subheader("🔍 Informasi Deduplikasi")
        if dedup_info:
            col1, col2 = st.columns(2)
            with col1:
                st.metric("Data Awal (Sebelum Dedup)", f"{dedup_info['before']:,}")
                st.metric("Data Duplikat Ditemukan", f"{dedup_info['duplicates_found']:,}")
            with col2:
                st.metric("Data Final (Setelah Dedup)", f"{dedup_info['after']:,}")
                st.metric("Data yang Dihapus", f"{dedup_info['removed']:,}")
            
            st.info("💡 Sistem otomatis memilih data dengan status terbaik (prioritas: Selesai → Proses → BAPP → Bermasalah → Belum)")
    
    with tab3:
        st.subheader("📋 Summary Keseluruhan")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("**Status Distribution**")
            for status in ["Selesai", "Sedang Diproses", "Kurang BAPP", "Data Bermasalah", "Belum Dikerjakan"]:
                count = (df["Status_Category"] == status).sum()
                pct = (count/len(df)*100) if len(df) > 0 else 0
                emoji = get_status_emoji(status)
                st.metric(f"{emoji} {status}", f"{count:,}", f"{pct:.1f}%")
        
        with col2:
            st.markdown("**Data Sources**")
            if "__source" in df.columns:
                source_counts = df["__source"].value_counts()
                for source, count in source_counts.items():
                    pct = (count/len(df)*100)
                    st.metric(source, f"{count:,}", f"{pct:.1f}%")

# ======================================================
# FOOTER
# ======================================================
st.markdown("---")
st.markdown("""
<div class='dashboard-footer'>
    <p>🚀 Dashboard Monitoring v5.0 • Multi-Sheet GID • Smart Deduplication</p>
    <p style='font-size:0.8rem; color:#999;'>Powered by Streamlit | Prioritas: Data dengan Status Terlengkap</p>
</div>
""", unsafe_allow_html=True)
