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
    menu_items={'About': "Dashboard Monitoring v5.3 - Manual Refresh Only"}
)

# ======================================================
# CSS
# ======================================================
st.markdown("""
<style>
.dashboard-header {
    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    padding: 2rem;
    border-radius: 10px;
    color: white;
    text-align: center;
    margin-bottom: 2rem;
}
.section-header {
    background: #f8f9fa;
    padding: 1rem;
    border-radius: 8px;
    margin: 1rem 0;
}
.dashboard-footer {
    text-align: center;
    padding: 1rem;
    margin-top: 2rem;
    color: #666;
}
.url-input-box {
    background: #f0f9ff;
    padding: 1rem;
    border-radius: 8px;
    border-left: 4px solid #3b82f6;
    margin: 0.5rem 0;
}
</style>
""", unsafe_allow_html=True)

# ======================================================
# UTILITIES
# ======================================================
def extract_sheet_id_and_gid(url):
    """Extract Sheet ID dan GID dari URL"""
    # Extract sheet ID
    sheet_match = re.search(r"/spreadsheets/d/([a-zA-Z0-9-_]+)", url)
    if not sheet_match:
        return None, None
    
    sheet_id = sheet_match.group(1)
    
    # Extract GID (jika ada)
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
        
        # Tambah identifier
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
    """
    Deduplikasi berdasarkan Trans. ID
    Prioritas: Ambil data yang sudah ada status (bukan Belum Dikerjakan)
    """
    if "Trans. ID" not in df.columns:
        st.warning("⚠️ Kolom 'Trans. ID' tidak ditemukan, skip deduplikasi")
        return df, {}
    
    # Normalize status
    df["Status_Category"] = df["Status_Text"].apply(normalize_status)
    df["__priority"] = df["Status_Category"].apply(get_status_priority)
    
    # Count duplicates before
    before_count = len(df)
    duplicate_count = df.duplicated(subset=["Trans. ID"], keep=False).sum()
    
    # Sort by priority (ascending) - yang prioritas tinggi di atas
    df_sorted = df.sort_values(by=["Trans. ID", "__priority"])
    
    # Keep first (yang prioritas paling tinggi)
    df_dedup = df_sorted.drop_duplicates(subset=["Trans. ID"], keep="first")
    
    # Remove helper column
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
    """Warna untuk setiap status - UPDATED"""
    colors = {
        "Belum Dikerjakan": "#94a3b8",
        "Sedang Diproses": "#f59e0b",
        "Revisi": "#ff00ff",  # Magenta/Pink
        "Kurang BAPP": "#00ffff",  # Cyan
        "Selesai": "#10b981",
        "Data Bermasalah": "#ef4444"
    }
    return colors.get(status, "#94a3b8")

def get_status_emoji(status):
    """Emoji untuk setiap status - UPDATED"""
    emojis = {
        "Belum Dikerjakan": "⏳",
        "Sedang Diproses": "⚙️",
        "Revisi": "🔄",  # Emoji untuk Revisi
        "Kurang BAPP": "📄",
        "Selesai": "✅",
        "Data Bermasalah": "⚠️"
    }
    return emojis.get(status, "❓")

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
    
    # Gabungkan semua data
    combined_df = pd.concat(all_dfs, ignore_index=True)
    
    # Deduplikasi
    deduped_df, dedup_info = deduplicate_data(combined_df)
    
    return deduped_df, load_results, dedup_info

# ======================================================
# INITIALIZE SESSION STATE - PERSISTENT URLs
# ======================================================
# Initialize url_inputs PERTAMA KALI saja
if "url_inputs" not in st.session_state:
    st.session_state.url_inputs = ["https://docs.google.com/spreadsheets/d/1eX5CeXR4xzYPPHikbfdm2JUBpL5HQ3LC9cAA0X4m-QQ/edit#gid=0"]

# ======================================================
# HEADER
# ======================================================
st.markdown(f"""
<div class='dashboard-header'>
    <h1>📊 Dashboard Monitoring Pekerjaan</h1>
    <p>Multi-Sheet GID Support • Smart Deduplication • Manual Refresh • Last Update: {datetime.now().strftime('%d %B %Y, %H:%M:%S WIB')}</p>
</div>
""", unsafe_allow_html=True)

# ======================================================
# SIDEBAR - MULTI URL INPUT
# ======================================================
with st.sidebar:
    st.title("⚙️ Input Data Source")
    
    st.markdown("### 🔗 Input URL Sheet (GID)")
    
    # Display all URL inputs
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
    
    # Remove URLs yang ditandai untuk dihapus
    if urls_to_remove:
        for idx in sorted(urls_to_remove, reverse=True):
            st.session_state.url_inputs.pop(idx)
        st.rerun()
    
    # Button untuk add URL baru
    col_add1, col_add2 = st.columns([2, 2])
    with col_add1:
        if st.button("➕ Tambah URL", use_container_width=True):
            st.session_state.url_inputs.append("")
            st.rerun()
    
    with col_add2:
        if st.button("🔄 Reset Semua", use_container_width=True):
            st.session_state.url_inputs = [""]
            st.rerun()
    
    st.caption(f"Total: {len(st.session_state.url_inputs)} URL")
    
    st.markdown("---")
    
    col1, col2 = st.columns(2)
    with col1:
        load_btn = st.button("🔄 Load Data", use_container_width=True, type="primary")
    with col2:
        clear_btn = st.button("🗑️ Clear Cache", use_container_width=True)
    
    if clear_btn:
        # Clear semua data yang di-load, tapi URL tetap
        if "df" in st.session_state:
            del st.session_state["df"]
        if "load_results" in st.session_state:
            del st.session_state["load_results"]
        if "dedup_info" in st.session_state:
            del st.session_state["dedup_info"]
        if "last_load" in st.session_state:
            del st.session_state["last_load"]
        st.success("✅ Cache cleared! URL masih tersimpan.")
        st.rerun()
    
    st.markdown("---")
    
    # Status last load
    if st.session_state.get("last_load"):
        st.success(f"✅ Last Load: {st.session_state['last_load'].strftime('%H:%M:%S')}")
    
    st.markdown("---")
    
    with st.expander("📖 Cara Pakai"):
        st.markdown("""
        **1. Tambah URL:**
        - Klik "➕ Tambah URL" untuk menambah input baru
        - Setiap URL akan punya kolom sendiri
        
        **2. Ambil URL dengan GID:**
        - Buka Google Sheets
        - Klik tab sheet yang ingin diambil
        - Copy URL dari browser (sudah ada #gid=xxx)
        - Paste di kolom URL
        
        **3. Hapus URL:**
        - Klik 🗑️ di sebelah URL untuk menghapus
        
        **4. Load Data:**
        - Klik tombol "🔄 Load Data" untuk refresh
        - URL akan tetap tersimpan
        - Tidak ada auto refresh
        
        **5. Deduplikasi Otomatis:**
        - Sistem otomatis hapus data duplikat
        - Prioritas: Data yang **sudah ada status**
        - Base on: `Trans. ID`
        
        **6. Permission:**
        - Share → Anyone with link → Viewer
        """)
    
    with st.expander("🎯 Prioritas Status"):
        st.markdown("""
        Jika ada data sama (Trans. ID sama) di beberapa sheet, sistem akan ambil yang:
        
        1. ✅ **Selesai** (prioritas tertinggi)
        2. ⚙️ **Sedang Diproses**
        3. 🔄 **Revisi**
        4. 📄 **Kurang BAPP**
        5. ⚠️ **Data Bermasalah**
        6. ⏳ **Belum Dikerjakan** (prioritas terendah)
        """)
    
    st.info("💡 Refresh manual aja - klik tombol Load Data")

# ======================================================
# MAIN - LOAD DATA
# ======================================================
# Get clean URL list dari session state
url_list = [url.strip() for url in st.session_state.url_inputs if url.strip()]

if not url_list:
    st.info("👆 Masukkan minimal 1 URL di sidebar")
    st.stop()

# Show URLs yang akan diload
with st.expander(f"📋 URL yang tersimpan ({len(url_list)} sheet)"):
    for i, url in enumerate(url_list, 1):
        sheet_id, gid = extract_sheet_id_and_gid(url)
        if sheet_id:
            st.success(f"{i}. Sheet ID: `{sheet_id}` | GID: `{gid}`")
        else:
            st.error(f"{i}. ❌ URL tidak valid: {url[:50]}...")

# MANUAL LOAD ONLY
if load_btn:
    with st.spinner("⏳ Memuat data dari semua sheet..."):
        df, load_results, dedup_info = load_multiple_sheets(url_list)
        
        # Show load results
        st.markdown("### 📊 Hasil Loading")
        result_df = pd.DataFrame(load_results)
        st.dataframe(result_df, use_container_width=True, hide_index=True)
        
        if df is None:
            st.error("❌ Semua sheet gagal dimuat. Periksa URL dan permission!")
            st.stop()
        
        # Show dedup info
        if dedup_info:
            st.success(f"✅ Data berhasil dimuat!")
            
            col_d1, col_d2, col_d3 = st.columns(3)
            col_d1.metric("📥 Data Awal", f"{dedup_info['before']:,}")
            col_d2.metric("🗑️ Duplikat Dihapus", f"{dedup_info['removed']:,}")
            col_d3.metric("✅ Data Final", f"{dedup_info['after']:,}")
            
            if dedup_info['removed'] > 0:
                st.info(f"💡 Ditemukan {dedup_info['duplicates_found']:,} data duplikat. Sistem otomatis pilih yang sudah ada status.")
        
        # Simpan ke session state
        st.session_state["df"] = df
        st.session_state["load_results"] = load_results
        st.session_state["dedup_info"] = dedup_info
        st.session_state["last_load"] = datetime.now()

df = st.session_state.get("df")
if df is None:
    st.warning("⚠️ Klik tombol '🔄 Load Data' di sidebar untuk memuat data")
    st.stop()

dedup_info = st.session_state.get("dedup_info", {})

# ======================================================
# INFO BOXES
# ======================================================
st.markdown("---")
col_info1, col_info2, col_info3, col_info4 = st.columns(4)

col_info1.metric("📋 Total Data", f"{len(df):,}")
col_info2.metric("📑 Sheet Loaded", len(url_list))
if dedup_info:
    col_info3.metric("🗑️ Duplikat Removed", f"{dedup_info.get('removed', 0):,}")
if "last_load" in st.session_state:
    col_info4.metric("🕐 Last Load", st.session_state["last_load"].strftime("%H:%M:%S"))

# ======================================================
# VALIDASI KOLOM
# ======================================================
# Mapping nama kolom (case insensitive)
def find_column(df, possible_names):
    """Cari kolom dengan case-insensitive"""
    df_cols_lower = {col.lower(): col for col in df.columns}
    for name in possible_names:
        if name.lower() in df_cols_lower:
            return df_cols_lower[name.lower()]
    return None

# Cari kolom dengan berbagai variasi nama - DISESUAIKAN DENGAN SPREADSHEET
trans_id_col = find_column(df, ["trans. id", "Trans. ID", "trans id", "transid", "trans_id"])
nama_col = find_column(df, ["nama", "Nama", "name", "sekolah"])
jenjang_col = find_column(df, ["jenjang", "Jenjang", "level", "tingkat"])
kabupaten_col = find_column(df, ["kabupaten", "Kabupaten", "kab", "regency"])
propinsi_col = find_column(df, ["propinsi", "Propinsi", "provinsi", "province", "prov"])
npsn_col = find_column(df, ["npsn", "NPSN"])
status_col = find_column(df, ["Status_Text", "status_text", "status text", "status"])

# Debug: Tampilkan kolom yang ditemukan
st.info(f"🔍 Debug - Kolom ditemukan: trans_id={trans_id_col}, nama={nama_col}, jenjang={jenjang_col}, kabupaten={kabupaten_col}, propinsi={propinsi_col}, npsn={npsn_col}, status={status_col}")

# Rename kolom ke format standar
column_mapping = {}
if trans_id_col: column_mapping[trans_id_col] = "Trans. ID"
if nama_col: column_mapping[nama_col] = "Nama"
if jenjang_col: column_mapping[jenjang_col] = "Jenjang"
if kabupaten_col: column_mapping[kabupaten_col] = "Kabupaten"
if propinsi_col: column_mapping[propinsi_col] = "Propinsi"
if npsn_col: column_mapping[npsn_col] = "NPSN"
if status_col: column_mapping[status_col] = "Status_Text"

df = df.rename(columns=column_mapping)

# Validasi kolom wajib
required_columns = ["Trans. ID", "Nama", "Jenjang", "Kabupaten", "Propinsi", "NPSN"]

if "Status_Text" not in df.columns:
    st.error("❌ Kolom 'Status_Text' tidak ditemukan!")
    st.warning("⚠️ Jalankan Apps Script dulu untuk generate kolom Status_Text")
    with st.expander("🔍 Lihat kolom tersedia"):
        st.write("Kolom di DataFrame:")
        st.write(df.columns.tolist())
    st.stop()

missing = [c for c in required_columns if c not in df.columns]
if missing:
    st.error(f"❌ Kolom tidak ditemukan: {', '.join(missing)}")
    with st.expander("🔍 Lihat kolom tersedia"):
        st.write("Kolom di DataFrame:")
        st.write(df.columns.tolist())
        st.write("\nMapping yang berhasil:")
        st.write(column_mapping)
    st.stop()

# Optional columns - DISESUAIKAN
optional_columns = ["keterangan", "petugas", "pic", "telp", "alamat", "catatan", "resi pengiriman", "serial number"]
display_columns = ["__source", "Trans. ID", "Nama", "Jenjang", "Kabupaten", "Propinsi", "NPSN", "Status_Text"]

# Cari optional columns (case insensitive)
for opt_col in optional_columns:
    found_col = find_column(df, [opt_col, opt_col.title(), opt_col.upper()])
    if found_col and found_col not in display_columns:
        display_columns.append(found_col)

# ======================================================
# PROCESS STATUS
# ======================================================
if "Status_Category" not in df.columns:
    df["Status_Category"] = df["Status_Text"].apply(normalize_status)

# ======================================================
# METRICS - UPDATED dengan Revisi
# ======================================================
st.markdown("---")
st.markdown('<div class="section-header"><h3>📈 Ringkasan Status</h3></div>', unsafe_allow_html=True)

c1, c2, c3, c4, c5, c6 = st.columns(6)

total_belum = (df.Status_Category == "Belum Dikerjakan").sum()
total_proses = (df.Status_Category == "Sedang Diproses").sum()
total_revisi = (df.Status_Category == "Revisi").sum()
total_bapp = (df.Status_Category == "Kurang BAPP").sum()
total_selesai = (df.Status_Category == "Selesai").sum()
total_bermasalah = (df.Status_Category == "Data Bermasalah").sum()

c1.metric("⏳ BELUM", total_belum, 
          delta=f"{(total_belum/len(df)*100):.1f}%" if len(df) > 0 else "0%")
c2.metric("⚙️ PROSES", total_proses,
          delta=f"{(total_proses/len(df)*100):.1f}%" if len(df) > 0 else "0%")
c3.metric("🔄 REVISI", total_revisi,
          delta=f"{(total_revisi/len(df)*100):.1f}%" if len(df) > 0 else "0%")
c4.metric("📄 KURANG BAPP", total_bapp,
          delta=f"{(total_bapp/len(df)*100):.1f}%" if len(df) > 0 else "0%")
c5.metric("✅ SELESAI", total_selesai,
          delta=f"{(total_selesai/len(df)*100):.1f}%" if len(df) > 0 else "0%")
c6.metric("⚠️ BERMASALAH", total_bermasalah,
          delta=f"{(total_bermasalah/len(df)*100):.1f}%" if len(df) > 0 else "0%")

# Progress bar
total = len(df)
if total > 0:
    progress_pct = (total_selesai / total) * 100
    st.progress(total_selesai / total)
    st.markdown(f"**🎯 Progress Keseluruhan:** {progress_pct:.1f}% ({total_selesai:,} dari {total:,} sekolah)")

# ======================================================
# FILTER - UPDATED dengan Revisi
# ======================================================
st.markdown("---")
st.markdown("### 🔎 Filter Data")

col_filter1, col_filter2, col_filter3 = st.columns(3)

with col_filter1:
    status_filter = st.selectbox(
        "📊 Status",
        ["Semua Status", "Belum Dikerjakan", "Sedang Diproses", "Revisi", "Kurang BAPP", "Selesai", "Data Bermasalah"]
    )

with col_filter2:
    if "__source" in df.columns:
        source_list = ["Semua Source"] + sorted(df["__source"].unique().tolist())
        source_filter = st.selectbox("📑 Source Sheet", source_list)
    else:
        source_filter = "Semua Source"

with col_filter3:
    search_text = st.text_input("🔍 Cari (Nama/NPSN/Kabupaten)", "")

# Apply filters
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

st.markdown(f"**Menampilkan {len(filtered_df):,} dari {len(df):,} baris**")

# ======================================================
# TABLE
# ======================================================
st.markdown("---")
st.markdown('<div class="section-header"><h3>📋 Data Detail</h3></div>', unsafe_allow_html=True)

def style_status_cell(val):
    """Style untuk kolom status"""
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
st.markdown("---")
col_dl1, col_dl2 = st.columns(2)

timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')

with col_dl1:
    st.download_button(
        "📥 Download Hasil Filter (CSV)",
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
# ANALYTICS - UPDATED dengan Revisi
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
            
            st.info("💡 Sistem otomatis memilih data dengan status terbaik (prioritas: Selesai → Proses → Revisi → BAPP → Bermasalah → Belum)")
    
    with tab3:
        st.subheader("📋 Summary Keseluruhan")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("**Status Distribution**")
            for status in ["Selesai", "Sedang Diproses", "Revisi", "Kurang BAPP", "Data Bermasalah", "Belum Dikerjakan"]:
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
    <p>🚀 Dashboard Monitoring v5.3 • Multi-Sheet GID • Smart Deduplication • Manual Refresh</p>
    <p style='font-size:0.8rem; color:#999;'>Powered by Streamlit | URL Persistent • Refresh Manual • Updated with Revisi Status</p>
</div>
""", unsafe_allow_html=True)
