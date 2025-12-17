import streamlit as st
import pandas as pd
import re
import requests
import time
from datetime import datetime


# ==============================================================================
# PAGE CONFIGURATION
# ==============================================================================

st.set_page_config(
    page_title="Dashboard Monitoring Pekerjaan",
    layout="wide",
    initial_sidebar_state="expanded",
    menu_items={'About': "Dashboard Monitoring v5.4 - Fixed Column Detection"}
)


# ==============================================================================
# CUSTOM CSS STYLING
# ==============================================================================

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


# ==============================================================================
# UTILITY FUNCTIONS - URL & SHEET HANDLING
# ==============================================================================

def extract_sheet_id_and_gid(url):
    """Extract Sheet ID dan GID dari URL Google Sheets"""
    sheet_match = re.search(r"/spreadsheets/d/([a-zA-Z0-9-_]+)", url)
    if not sheet_match:
        return None, None
    
    sheet_id = sheet_match.group(1)
    gid_match = re.search(r"[#&]gid=(\d+)", url)
    gid = gid_match.group(1) if gid_match else "0"
    
    return sheet_id, gid


def load_sheet_by_gid(sheet_id, gid, sheet_label="Sheet"):
    """Load sheet berdasarkan GID dari Google Sheets"""
    try:
        url = f"https://docs.google.com/spreadsheets/d/{sheet_id}/export?format=csv&gid={gid}"
        df = pd.read_csv(url)
        
        if df.empty:
            raise Exception("Sheet kosong")
        
        # Tambahkan metadata identifier
        df["__source"] = sheet_label
        df["__gid"] = gid
        
        return df, None
    except Exception as e:
        return None, str(e)


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
    
    return combined_df, load_results, None


# ==============================================================================
# UTILITY FUNCTIONS - STATUS NORMALIZATION
# ==============================================================================

def normalize_status(val):
    """Normalisasi status sesuai Apps Script - termasuk handling Revisi"""
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


def get_status_color(status):
    """Warna untuk setiap status kategori"""
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
    """Emoji untuk setiap status kategori"""
    emojis = {
        "Belum Dikerjakan": "⏳",
        "Sedang Diproses": "⚙️",
        "Revisi": "🔄",
        "Kurang BAPP": "📄",
        "Selesai": "✅",
        "Data Bermasalah": "⚠️"
    }
    return emojis.get(status, "❓")


# ==============================================================================
# UTILITY FUNCTIONS - DATA PROCESSING
# ==============================================================================

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


def find_column(df, possible_names):
    """Cari kolom dengan case-insensitive dan strip whitespace"""
    # Buat mapping kolom yang sudah di-clean
    df_cols_cleaned = {}
    for col in df.columns:
        # Clean: lowercase, strip, hapus whitespace berlebih
        cleaned = str(col).lower().strip()
        cleaned = re.sub(r'\s+', ' ', cleaned)
        df_cols_cleaned[cleaned] = col
    
    # Cari dari possible_names
    for name in possible_names:
        cleaned_name = str(name).lower().strip()
        cleaned_name = re.sub(r'\s+', ' ', cleaned_name)
        if cleaned_name in df_cols_cleaned:
            return df_cols_cleaned[cleaned_name]
    
    return None


# ==============================================================================
# SESSION STATE INITIALIZATION
# ==============================================================================

if "url_inputs" not in st.session_state:
    st.session_state.url_inputs = [
        "https://docs.google.com/spreadsheets/d/1eX5CeXR4xzYPPHikbfdm2JUBpL5HQ3LC9cAA0X4m-QQ/edit#gid=0"
    ]


# ==============================================================================
# HEADER SECTION
# ==============================================================================

st.markdown(f"""
<div class='dashboard-header'>
    <h1>📊 Dashboard Monitoring Pekerjaan</h1>
    <p>Multi-Sheet GID Support • Smart Deduplication • Manual Refresh • v5.4 Fixed</p>
</div>
""", unsafe_allow_html=True)


# ==============================================================================
# SIDEBAR - DATA SOURCE INPUT
# ==============================================================================

with st.sidebar:
    st.title("⚙️ Input Data Source")
    st.markdown("### 🔗 Input URL Sheet (GID)")
    
    # URL Input Fields with Delete Button
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
    
    # Process URL removal
    if urls_to_remove:
        for idx in sorted(urls_to_remove, reverse=True):
            st.session_state.url_inputs.pop(idx)
        st.rerun()
    
    # Add & Reset Buttons
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
    
    # Load & Clear Cache Buttons
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
    
    # Last Load Timestamp
    if st.session_state.get("last_load"):
        st.success(f"✅ Last Load: {st.session_state['last_load'].strftime('%H:%M:%S')}")
    
    st.markdown("---")
    
    # Help Section
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


# ==============================================================================
# MAIN CONTENT - DATA LOADING
# ==============================================================================

url_list = [url.strip() for url in st.session_state.url_inputs if url.strip()]

if not url_list:
    st.info("👆 Masukkan minimal 1 URL di sidebar")
    st.stop()

# Display saved URLs
with st.expander(f"📋 URL yang tersimpan ({len(url_list)} sheet)"):
    for i, url in enumerate(url_list, 1):
        sheet_id, gid = extract_sheet_id_and_gid(url)
        if sheet_id:
            st.success(f"{i}. Sheet ID: `{sheet_id}` | GID: `{gid}`")
        else:
            st.error(f"{i}. ❌ URL tidak valid")

# Load Data Process
if load_btn:
    with st.spinner("⏳ Memuat data..."):
        df, load_results, _ = load_multiple_sheets(url_list)
        
        st.markdown("### 📊 Hasil Loading")
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


# ==============================================================================
# COLUMN DETECTION & MAPPING
# ==============================================================================

st.markdown("---")
st.markdown("### 🔧 Deteksi & Mapping Kolom")

# Find columns with various name variations
trans_id_col = find_column(df, ["trans. id", "trans id", "transid", "trans_id", "id transaksi", "id"])
nama_col = find_column(df, ["nama", "name", "sekolah", "nama sekolah"])
jenjang_col = find_column(df, ["jenjang", "level", "tingkat", "jenjang pendidikan"])
kabupaten_col = find_column(df, ["kabupaten", "kab", "regency", "kab/kota", "kabupaten/kota"])
propinsi_col = find_column(df, ["propinsi", "provinsi", "province", "prov"])
npsn_col = find_column(df, ["npsn"])
status_col = find_column(df, ["status_text", "status text", "status", "status pengerjaan", "keterangan"])

# Show detection results
with st.expander("🔍 Hasil Deteksi Kolom (Klik untuk lihat detail)"):
    col1, col2 = st.columns(2)
    
    with col1:
        st.write("**Kolom yang ditemukan:**")
        st.write(f"- Trans ID: `{trans_id_col if trans_id_col else '❌ TIDAK DITEMUKAN'}`")
        st.write(f"- Nama: `{nama_col if nama_col else '❌ TIDAK DITEMUKAN'}`")
        st.write(f"- Jenjang: `{jenjang_col if jenjang_col else '❌ TIDAK DITEMUKAN'}`")
        st.write(f"- Kabupaten: `{kabupaten_col if kabupaten_col else '❌ TIDAK DITEMUKAN'}`")
        st.write(f"- Propinsi: `{propinsi_col if propinsi_col else '❌ TIDAK DITEMUKAN'}`")
        st.write(f"- NPSN: `{npsn_col if npsn_col else '❌ TIDAK DITEMUKAN'}`")
        st.write(f"- Status: `{status_col if status_col else '❌ TIDAK DITEMUKAN'}`")
    
    with col2:
        st.write("**Semua kolom di spreadsheet:**")
        st.dataframe(
            pd.DataFrame({"Nama Kolom": df.columns.tolist()}),
            use_container_width=True,
            height=300
        )

# Rename columns
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

# Validate required columns
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

# Deduplicate data after rename
df, dedup_info = deduplicate_data(df)

if dedup_info:
    col_d1, col_d2, col_d3 = st.columns(3)
    col_d1.metric("📥 Data Awal", f"{dedup_info['before']:,}")
    col_d2.metric("🗑️ Duplikat Removed", f"{dedup_info['removed']:,}")
    col_d3.metric("✅ Data Final", f"{dedup_info['after']:,}")

st.session_state["df"] = df
st.session_state["dedup_info"] = dedup_info


# ==============================================================================
# METRICS - STATUS SUMMARY
# ==============================================================================

st.markdown("---")
st.markdown('<div class="section-header"><h3>📈 Ringkasan Status</h3></div>', unsafe_allow_html=True)

c1, c2, c3, c4, c5, c6 = st.columns(6)

total_belum = (df.Status_Category == "Belum Dikerjakan").sum()
total_proses = (df.Status_Category == "Sedang Diproses").sum()
total_revisi = (df.Status_Category == "Revisi").sum()
total_bapp = (df.Status_Category == "Kurang BAPP").sum()
total_selesai = (df.Status_Category == "Selesai").sum()
total_bermasalah = (df.Status_Category == "Data Bermasalah").sum()

c1.metric(
    "⏳ NOT CHECKED / BELUM DICEK",
    total_belum,
    f"{(total_belum/len(df)*100):.1f}%"
)
c2.metric(
    "⚙️ PROSES / ALREADY FOLLOWED UP TO THE CORDINATOR",
    total_proses,
    f"{(total_proses/len(df)*100):.1f}%"
)
c3.metric(
    "🔄 ON CHECK / SUDAH DICEK",
    total_revisi,
    f"{(total_revisi/len(df)*100):.1f}%"
)
c4.metric(
    "📄 KURANG BAPP / BAPP DATA LACK",
    total_bapp,
    f"{(total_bapp/len(df)*100):.1f}%"
)
c5.metric(
    "✅ SELESAI / DONE",
    total_selesai,
    f"{(total_selesai/len(df)*100):.1f}%"
)
c6.metric(
    "⚠️ CONSTRAINED DATA / BERMASALAH",
    total_bermasalah,
    f"{(total_bermasalah/len(df)*100):.1f}%"
)

if len(df) > 0:
    progress_pct = (total_selesai / len(df)) * 100
    st.progress(total_selesai / len(df))
    st.markdown(f"**🎯 Progress: {progress_pct:.1f}% ({total_selesai:,}/{len(df):,})**")


# ==============================================================================
# FILTER CONTROLS
# ==============================================================================

st.markdown("---")
st.markdown("### 🔎 Filter Data")

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
    search_text = st.text_input("🔍 Cari", "")

# Apply filters
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

st.markdown(f"**Menampilkan {len(filtered_df):,} dari {len(df):,} baris**")


# ==============================================================================
# DATA TABLE DISPLAY
# ==============================================================================

st.markdown("---")
st.markdown('<div class="section-header"><h3>📋 Data Detail</h3></div>', unsafe_allow_html=True)

display_columns = ["__source", "Trans. ID", "Nama", "Jenjang", "Kabupaten", "Propinsi", "NPSN", "Status_Text"]

def style_status_cell(val):
    """Apply styling to status cells"""
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
    st.warning("⚠️ Tidak ada data")


# ==============================================================================
# DOWNLOAD BUTTONS
# ==============================================================================

st.markdown("---")
col_dl1, col_dl2 = st.columns(2)

timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')

with col_dl1:
    st.download_button(
        "📥 Download Filter (CSV)",
        filtered_df.to_csv(index=False).encode('utf-8'),
        f"filtered_{timestamp}.csv",
        "text/csv",
        use_container_width=True
    )

with col_dl2:
    st.download_button(
        "📥 Download All (CSV)",
        df.to_csv(index=False).encode('utf-8'),
        f"all_{timestamp}.csv",
        "text/csv",
        use_container_width=True
    )


# ==============================================================================
# FOOTER
# ==============================================================================

st.markdown("---")
st.markdown("""
<div class='dashboard-footer'>
    <p>🚀 Dashboard v5.4 • Fixed Column Detection • Smart Deduplication</p>
</div>
""", unsafe_allow_html=True)
