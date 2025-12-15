import streamlit as st
st.cache_data.clear()

import pandas as pd
import re
import requests
import time
from datetime import datetime
from urllib.parse import quote

# ======================================================
# CONFIG
# ======================================================
st.set_page_config(
    page_title="Dashboard Monitoring Pekerjaan",
    layout="wide",
    initial_sidebar_state="expanded",
    menu_items={'About': "Dashboard Monitoring Pekerjaan v4.0"}
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
.sheet-badge {
    display: inline-block;
    padding: 0.25rem 0.75rem;
    background: #e0e7ff;
    color: #4338ca;
    border-radius: 12px;
    font-size: 0.875rem;
    font-weight: 600;
    margin: 0.25rem;
}
</style>
""", unsafe_allow_html=True)

# ======================================================
# UTILITIES
# ======================================================
def extract_sheet_id(url):
    """Extract Sheet ID dari URL Google Sheets"""
    m = re.search(r"/spreadsheets/d/([a-zA-Z0-9-_]+)", url)
    return m.group(1) if m else None

def get_all_sheet_names_from_tabs(sheet_id):
    """Ambil semua nama sheet dari tabs di bagian bawah spreadsheet"""
    try:
        url = f"https://docs.google.com/spreadsheets/d/{sheet_id}/edit"
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
        response = requests.get(url, headers=headers, timeout=15)
        
        if response.status_code != 200:
            return []
        
        html = response.text
        
        # Pattern untuk menangkap nama sheet dari struktur JSON Google Sheets
        # Format: "sheetId":xxx,"title":"NAMA_SHEET"
        pattern = r'"sheetId":\d+,"title":"([^"]+)"'
        matches = re.findall(pattern, html)
        
        if not matches:
            # Coba pattern alternatif
            pattern2 = r'"title":"([^"]+?)","index":\d+'
            matches = re.findall(pattern2, html)
        
        # Filter dan deduplikasi
        seen = set()
        sheet_names = []
        for name in matches:
            # Skip sheet yang kemungkinan sistem atau hidden
            if name.startswith('_') or name.startswith('Copy of'):
                continue
            # Decode unicode jika perlu
            if name not in seen:
                seen.add(name)
                sheet_names.append(name)
        
        return sheet_names
        
    except Exception as e:
        st.error(f"Error parsing sheet names: {str(e)}")
        return []

def load_sheet_by_name(sheet_id, sheet_name):
    """Load satu sheet berdasarkan nama"""
    try:
        encoded_name = quote(sheet_name)
        url = f"https://docs.google.com/spreadsheets/d/{sheet_id}/gviz/tq?tqx=out:csv&sheet={encoded_name}"
        df = pd.read_csv(url)
        return df
    except Exception as e:
        raise Exception(f"Gagal load sheet '{sheet_name}': {str(e)}")

@st.cache_data(ttl=REFRESH_INTERVAL, show_spinner=False)
def load_all_sheets(sheet_id):
    """Load semua sheet dari Google Spreadsheet"""
    
    # Cek akses
    try:
        test_url = f"https://docs.google.com/spreadsheets/d/{sheet_id}/export?format=csv"
        test_response = requests.head(test_url, timeout=5, allow_redirects=True)
        if test_response.status_code != 200:
            return None, "❌ Spreadsheet tidak bisa diakses.\n\n**Solusi:**\n1. Buka spreadsheet\n2. Klik **Share** → **Anyone with the link** → **Viewer**\n3. Copy URL dan paste ulang"
    except:
        return None, "❌ Tidak bisa koneksi ke Google Sheets. Cek koneksi internet Anda."
    
    # Ambil nama-nama sheet
    sheet_names = get_all_sheet_names_from_tabs(sheet_id)
    
    if not sheet_names:
        return None, "❌ Tidak ada sheet yang terdeteksi.\n\n**Kemungkinan:**\n1. Spreadsheet kosong\n2. Nama sheet mengandung karakter khusus\n3. Permission belum diset dengan benar"
    
    # Load setiap sheet
    dfs = []
    failed_sheets = []
    
    for idx, sheet_name in enumerate(sheet_names):
        try:
            df = load_sheet_by_name(sheet_id, sheet_name)
            
            if df.empty:
                failed_sheets.append(f"{sheet_name} (kosong)")
                continue
            
            # Tambahkan kolom identifier sheet
            df["__sheet_name"] = sheet_name
            dfs.append(df)
            
        except Exception as e:
            failed_sheets.append(f"{sheet_name} ({str(e)[:30]}...)")
            continue
    
    if not dfs:
        error_msg = "❌ Semua sheet gagal dimuat."
        if failed_sheets:
            error_msg += f"\n\n**Sheet yang gagal:**\n" + "\n".join([f"- {s}" for s in failed_sheets])
        return None, error_msg
    
    # Gabungkan semua dataframe
    combined_df = pd.concat(dfs, ignore_index=True)
    
    return combined_df, {
        "total_sheets": len(sheet_names),
        "loaded_sheets": len(dfs),
        "failed_sheets": failed_sheets,
        "total_rows": len(combined_df)
    }

# ======================================================
# STATUS NORMALIZER - DISESUAIKAN DENGAN APPS SCRIPT
# ======================================================
def normalize_status(val):
    """Normalisasi status sesuai output Apps Script"""
    if pd.isna(val) or val == "":
        return "Belum Dikerjakan"
    
    val = str(val).upper().strip()
    
    # Normalize whitespace dan special chars
    val = re.sub(r'[\u00A0\u200B\u200C\u200D\t\n\r]', ' ', val)
    val = re.sub(r'\s+', ' ', val)
    
    # Mapping sesuai Apps Script
    if "SELESAI" in val or "COMPLETE" in val or "DONE" in val:
        return "Selesai"
    elif "KURANG BAPP" in val or "BAPP" in val:
        return "Kurang BAPP"
    elif "BERMASALAH" in val or "MASALAH" in val or "ERROR" in val:
        return "Data Bermasalah"
    elif "PROSES" in val or "PENGERJAAN" in val or "DIKERJAKAN" in val:
        return "Sedang Diproses"
    elif "BELUM" in val:
        return "Belum Dikerjakan"
    else:
        return "Sedang Diproses"  # Default untuk status lainnya

def get_status_color(status):
    """Warna untuk setiap status"""
    colors = {
        "Belum Dikerjakan": "#94a3b8",      # Abu-abu
        "Sedang Diproses": "#f59e0b",       # Orange/Kuning
        "Kurang BAPP": "#3b82f6",           # Biru
        "Selesai": "#10b981",               # Hijau
        "Data Bermasalah": "#ef4444"        # Merah
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

# ======================================================
# HEADER
# ======================================================
st.markdown(f"""
<div class='dashboard-header'>
    <h1>📊 Dashboard Monitoring Pekerjaan</h1>
    <p>Realtime Sync Active • Last Update: {datetime.now().strftime('%d %B %Y, %H:%M:%S WIB')}</p>
</div>
""", unsafe_allow_html=True)

# ======================================================
# SIDEBAR
# ======================================================
with st.sidebar:
    st.title("⚙️ Pengaturan")
    
    sheet_url = st.text_input(
        "🔗 Google Spreadsheet URL",
        value="https://docs.google.com/spreadsheets/d/1eX5CeXR4xzYPPHikbfdm2JUBpL5HQ3LC9cAA0X4m-QQ/edit?usp=sharing",
        help="Paste URL lengkap dari spreadsheet Anda"
    )
    
    col1, col2 = st.columns(2)
    with col1:
        load_btn = st.button("🔄 Refresh", use_container_width=True, type="primary")
    with col2:
        clear_btn = st.button("🗑️ Clear Cache", use_container_width=True)
    
    if clear_btn:
        st.cache_data.clear()
        st.rerun()
    
    st.markdown("---")
    
    with st.expander("🔧 Setup Apps Script"):
        st.markdown("""
        **Script sudah terpasang?** ✅
        
        Pastikan script sudah dijalankan minimal 1x:
        1. Buka **Extensions** → **Apps Script**
        2. Paste script Anda
        3. Klik **Run** (▶️)
        4. Approve permissions
        5. Kolom **Status_Text** akan muncul
        
        Script akan update status berdasarkan warna NPSN.
        """)
    
    with st.expander("📖 Setting Permission"):
        st.markdown("""
        **Langkah-langkah:**
        1. Buka spreadsheet Anda
        2. Klik **Share** (pojok kanan atas)
        3. **General access** → **Anyone with the link**
        4. Role: **Viewer**
        5. Copy link & paste di atas
        """)
    
    st.info("💡 Auto refresh tiap 5 menit")

# ======================================================
# MAIN
# ======================================================
if not sheet_url:
    st.info("👆 Masukkan URL Google Spreadsheet di sidebar")
    st.stop()

sheet_id = extract_sheet_id(sheet_url)
if not sheet_id:
    st.error("❌ URL tidak valid!\n\nFormat: `https://docs.google.com/spreadsheets/d/[SHEET_ID]/edit`")
    st.stop()

# Load data
if load_btn or "df" not in st.session_state:
    with st.spinner("⏳ Memuat data dari spreadsheet..."):
        df, result = load_all_sheets(sheet_id)
        
        if df is None:
            st.error(result)
            st.stop()
        
        st.session_state["df"] = df
        st.session_state["load_info"] = result
        st.session_state["last_load"] = datetime.now()
        
        # Success message
        info = result
        st.success(f"✅ Berhasil memuat {info['loaded_sheets']}/{info['total_sheets']} sheet dengan {info['total_rows']} baris data!")
        
        if info['failed_sheets']:
            with st.expander("⚠️ Sheet yang gagal dimuat"):
                for failed in info['failed_sheets']:
                    st.warning(failed)

df = st.session_state["df"]
load_info = st.session_state.get("load_info", {})

# Info boxes
col_info1, col_info2, col_info3, col_info4 = st.columns(4)
col_info1.metric("📋 Total Baris", len(df))
col_info2.metric("📑 Sheet Dimuat", load_info.get('loaded_sheets', 0))
col_info3.metric("📂 Total Sheet", load_info.get('total_sheets', 0))
if "last_load" in st.session_state:
    col_info4.metric("🕐 Terakhir Update", st.session_state["last_load"].strftime("%H:%M:%S"))

# ======================================================
# VALIDASI KOLOM
# ======================================================
st.markdown("---")

# Cek kolom yang tersedia
available_cols = df.columns.tolist()

st.info(f"**Kolom terdeteksi:** {', '.join(available_cols[:10])}..." if len(available_cols) > 10 else f"**Kolom terdeteksi:** {', '.join(available_cols)}")

# Kolom wajib
required_columns = ["Trans. ID", "Nama", "Jenjang", "Kabupaten", "Propinsi", "NPSN"]

# Cek Status_Text
if "Status_Text" not in df.columns:
    st.error("❌ **Kolom 'Status_Text' tidak ditemukan!**")
    st.warning("⚠️ **Solusi:**\n1. Jalankan Apps Script yang sudah Anda buat\n2. Script akan membuat kolom 'Status_Text' otomatis\n3. Refresh dashboard ini")
    st.stop()

# Optional columns (kalau ada)
optional_columns = ["Keterangan", "Petugas", "PIC", "Telp", "Alamat"]
display_columns = ["__sheet_name"] + required_columns + ["Status_Text"]

for col in optional_columns:
    if col in df.columns:
        display_columns.append(col)

missing = [c for c in required_columns if c not in df.columns]
if missing:
    st.error(f"❌ Kolom wajib tidak ditemukan: {', '.join(missing)}")
    with st.expander("📋 Lihat semua kolom"):
        st.write(available_cols)
    st.stop()

# ======================================================
# PROCESS DATA
# ======================================================
df["Status_Category"] = df["Status_Text"].apply(normalize_status)

# Debug: lihat sample status
with st.expander("🔍 Debug: Sample Status dari Spreadsheet"):
    sample_df = df[["__sheet_name", "NPSN", "Status_Text", "Status_Category"]].head(10)
    st.dataframe(sample_df, use_container_width=True)

# ======================================================
# METRICS
# ======================================================
st.markdown('<div class="section-header"><h3>📈 Ringkasan Status (Semua Sheet)</h3></div>', unsafe_allow_html=True)

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

# Progress bar
total = len(df)
if total > 0:
    progress_pct = (total_selesai / total) * 100
    st.progress(total_selesai / total)
    st.markdown(f"**🎯 Progress Keseluruhan:** {progress_pct:.1f}% ({total_selesai:,} dari {total:,} sekolah)")

# ======================================================
# FILTER
# ======================================================
st.markdown("---")
st.markdown("### 🔎 Filter Data")

col_filter1, col_filter2, col_filter3 = st.columns(3)

with col_filter1:
    status_filter = st.selectbox(
        "📊 Status",
        ["Semua Status", "Belum Dikerjakan", "Sedang Diproses", "Kurang BAPP", "Selesai", "Data Bermasalah"]
    )

with col_filter2:
    sheet_list = ["Semua Sheet"] + sorted(df["__sheet_name"].unique().tolist())
    sheet_filter = st.selectbox("📑 Sheet", sheet_list)

with col_filter3:
    search_text = st.text_input("🔍 Cari (Nama/NPSN/Kabupaten)", "")

# Apply filters
filtered_df = df.copy()

if status_filter != "Semua Status":
    filtered_df = filtered_df[filtered_df["Status_Category"] == status_filter]

if sheet_filter != "Semua Sheet":
    filtered_df = filtered_df[filtered_df["__sheet_name"] == sheet_filter]

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
st.markdown('<div class="section-header"><h3>📋 Data Detail</h3></div>', unsafe_allow_html=True)

def style_status_cell(val):
    """Style untuk kolom status"""
    cat = normalize_status(val)
    color = get_status_color(cat)
    return f"background-color:{color};color:white;font-weight:600;padding:8px;border-radius:5px;text-align:center;"

# Display dengan styling
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
# BREAKDOWN PER SHEET
# ======================================================
st.markdown("---")
with st.expander("📊 **Lihat Breakdown Detail per Sheet**"):
    
    # Summary table
    sheet_summary = df.groupby(["__sheet_name", "Status_Category"]).size().reset_index(name="Jumlah")
    pivot_summary = sheet_summary.pivot(index="__sheet_name", columns="Status_Category", values="Jumlah").fillna(0).astype(int)
    
    # Add total column
    pivot_summary["TOTAL"] = pivot_summary.sum(axis=1)
    
    st.dataframe(pivot_summary, use_container_width=True)
    
    # Charts per sheet
    st.markdown("#### 📈 Visualisasi per Sheet")
    
    selected_sheet_viz = st.selectbox(
        "Pilih sheet untuk visualisasi:",
        df["__sheet_name"].unique().tolist()
    )
    
    sheet_data = df[df["__sheet_name"] == selected_sheet_viz]
    status_counts = sheet_data["Status_Category"].value_counts()
    
    col_v1, col_v2 = st.columns(2)
    
    with col_v1:
        st.markdown(f"**Status di: {selected_sheet_viz}**")
        for status, count in status_counts.items():
            emoji = get_status_emoji(status)
            pct = (count/len(sheet_data)*100)
            st.metric(f"{emoji} {status}", f"{count}", f"{pct:.1f}%")
    
    with col_v2:
        st.markdown("**Progress Chart**")
        for status in ["Belum Dikerjakan", "Sedang Diproses", "Kurang BAPP", "Selesai", "Data Bermasalah"]:
            if status in status_counts:
                count = status_counts[status]
                pct = count/len(sheet_data)
                color = get_status_color(status)
                st.markdown(f"**{status}**")
                st.progress(pct)
                st.caption(f"{count} sekolah ({pct*100:.1f}%)")

# ======================================================
# FOOTER
# ======================================================
st.markdown("---")
st.markdown("""
<div class='dashboard-footer'>
    <p>🚀 Dashboard Monitoring v4.0 • Multi Sheet • Apps Script Integration • Auto Refresh</p>
    <p style='font-size:0.8rem; color:#999;'>Powered by Streamlit | Data from Google Sheets</p>
</div>
""", unsafe_allow_html=True)
