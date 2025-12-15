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
    menu_items={'About': "Dashboard Monitoring Pekerjaan v3.1"}
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
</style>
""", unsafe_allow_html=True)

# ======================================================
# UTILITIES
# ======================================================
def extract_sheet_id(url):
    """Extract Sheet ID dari URL Google Sheets"""
    m = re.search(r"/spreadsheets/d/([a-zA-Z0-9-_]+)", url)
    return m.group(1) if m else None

def get_sheet_names(sheet_id):
    """Ambil SEMUA nama sheet dari Google Spreadsheet"""
    try:
        url = f"https://docs.google.com/spreadsheets/d/{sheet_id}/edit"
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        
        # Cari semua sheet names dalam HTML
        pattern = r'"sheetId":(\d+),"title":"([^"]+)"'
        matches = re.findall(pattern, response.text)
        
        # Return list of sheet names, sorted by sheet ID
        sheet_names = [match[1] for match in matches]
        
        # Fallback: coba pattern lain
        if not sheet_names:
            pattern2 = r'"title":"([^"]+)","index":\d+'
            sheet_names = re.findall(pattern2, response.text)
        
        # Remove duplicates sambil maintain order
        seen = set()
        unique_names = []
        for name in sheet_names:
            if name not in seen and not name.startswith('_'):
                seen.add(name)
                unique_names.append(name)
        
        return unique_names
    except Exception as e:
        st.error(f"Error mengambil nama sheet: {str(e)}")
        return []

def csv_by_name(sheet_id, sheet_name):
    """Generate CSV URL untuk sheet tertentu"""
    encoded_name = quote(sheet_name)
    return f"https://docs.google.com/spreadsheets/d/{sheet_id}/gviz/tq?tqx=out:csv&sheet={encoded_name}"

@st.cache_data(ttl=REFRESH_INTERVAL)
def load_all_sheets(sheet_id):
    """Load semua sheet dari Google Spreadsheet"""
    dfs = []
    sheet_names = get_sheet_names(sheet_id)

    if not sheet_names:
        return None, "❌ Tidak ada sheet yang ditemukan. Pastikan spreadsheet bisa diakses publik."

    progress_bar = st.progress(0)
    status_text = st.empty()
    
    for idx, name in enumerate(sheet_names):
        try:
            status_text.text(f"📥 Memuat sheet: {name}")
            df = pd.read_csv(csv_by_name(sheet_id, name))
            
            if not df.empty:
                df["__sheet"] = name
                dfs.append(df)
                st.success(f"✅ Sheet '{name}' berhasil dimuat ({len(df)} baris)")
            
            progress_bar.progress((idx + 1) / len(sheet_names))
            time.sleep(0.1)  # Prevent rate limiting
            
        except Exception as e:
            st.warning(f"⚠️ Gagal memuat sheet '{name}': {str(e)}")
            continue

    progress_bar.empty()
    status_text.empty()

    if not dfs:
        return None, "❌ Tidak ada sheet yang bisa dibaca. Periksa izin akses spreadsheet."

    combined_df = pd.concat(dfs, ignore_index=True)
    st.success(f"🎉 Total {len(dfs)} sheet berhasil dimuat dengan {len(combined_df)} baris data!")
    
    return combined_df, None

# ======================================================
# STATUS NORMALIZER
# ======================================================
def normalize_status(val):
    """Normalisasi status untuk konsistensi"""
    if pd.isna(val):
        return "Belum Dikerjakan"

    val = str(val).upper()
    val = re.sub(r'[\u00A0\u200B\u200C\u200D\t\n\r]', ' ', val)
    val = re.sub(r'\s+', ' ', val).strip()

    if "DATA BERMASALAH" in val or "BERMASALAH" in val:
        return "Data Bermasalah"
    if "KURANG BAPP" in val or "BAPP" in val:
        return "Kurang BAPP"
    if "PROSES" in val or "INSTALASI" in val or "DIKERJAKAN" in val:
        return "Sedang Diproses"
    if "SELESAI" in val or "DONE" in val or "COMPLETE" in val:
        return "Selesai"
    return "Belum Dikerjakan"

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
        help="Pastikan spreadsheet dapat diakses oleh siapa saja dengan link"
    )
    
    load_btn = st.button("📥 Muat Ulang Semua Sheet", use_container_width=True)
    
    st.markdown("---")
    st.info("💡 **Tips:**\n- Spreadsheet harus diset 'Anyone with the link can view'\n- Refresh otomatis setiap 5 menit")

# ======================================================
# MAIN
# ======================================================
if not sheet_url:
    st.info("👆 Masukkan URL Google Spreadsheet di sidebar")
    st.stop()

sheet_id = extract_sheet_id(sheet_url)
if not sheet_id:
    st.error("❌ URL Spreadsheet tidak valid. Format: https://docs.google.com/spreadsheets/d/[SHEET_ID]/edit")
    st.stop()

# Load data
if load_btn or "df" not in st.session_state:
    with st.spinner("⏳ Memuat data dari semua sheet..."):
        df, err = load_all_sheets(sheet_id)
        if err:
            st.error(err)
            st.stop()
        st.session_state["df"] = df
        st.session_state["last_load"] = datetime.now()

df = st.session_state["df"]

# Show info
if "last_load" in st.session_state:
    col1, col2, col3 = st.columns(3)
    col1.metric("📋 Total Baris Data", len(df))
    col2.metric("📑 Total Sheet", df["__sheet"].nunique())
    col3.metric("🕐 Terakhir Dimuat", st.session_state["last_load"].strftime("%H:%M:%S"))

# ======================================================
# VALIDASI KOLOM
# ======================================================
required_columns = [
    "Trans. ID", "Nama", "Jenjang", "Kabupaten", "Propinsi",
    "NPSN", "Status_Text", "Keterangan", "Petugas"
]

missing = [c for c in required_columns if c not in df.columns]
if missing:
    st.error(f"❌ Kolom tidak ditemukan: {', '.join(missing)}")
    st.info(f"Kolom yang tersedia: {', '.join(df.columns.tolist())}")
    st.stop()

# ======================================================
# PROCESS DATA
# ======================================================
df["Status_Category"] = df["Status_Text"].apply(normalize_status)

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

c1.metric("⏳ BELUM", total_belum)
c2.metric("⚙️ PROSES", total_proses)
c3.metric("📄 KURANG BAPP", total_bapp)
c4.metric("✅ SELESAI", total_selesai)
c5.metric("⚠️ BERMASALAH", total_bermasalah)

# Progress bar
total = len(df)
if total > 0:
    progress_pct = (total_selesai / total) * 100
    st.progress(total_selesai / total)
    st.write(f"**Progress Keseluruhan:** {progress_pct:.1f}% ({total_selesai}/{total})")

# ======================================================
# FILTER
# ======================================================
st.markdown("---")

col_filter1, col_filter2, col_filter3 = st.columns(3)

with col_filter1:
    status_filter = st.selectbox(
        "🎯 Filter Status",
        [
            "Semua Status",
            "Belum Dikerjakan",
            "Sedang Diproses",
            "Kurang BAPP",
            "Selesai",
            "Data Bermasalah"
        ]
    )

with col_filter2:
    sheet_list = ["Semua Sheet"] + sorted(df["__sheet"].unique().tolist())
    sheet_filter = st.selectbox("📑 Filter Sheet", sheet_list)

with col_filter3:
    search_text = st.text_input("🔍 Cari (Nama/NPSN/Kabupaten)", "")

# Apply filters
filtered_df = df.copy()

if status_filter != "Semua Status":
    filtered_df = filtered_df[filtered_df["Status_Category"] == status_filter]

if sheet_filter != "Semua Sheet":
    filtered_df = filtered_df[filtered_df["__sheet"] == sheet_filter]

if search_text:
    mask = (
        filtered_df["Nama"].str.contains(search_text, case=False, na=False) |
        filtered_df["NPSN"].astype(str).str.contains(search_text, case=False, na=False) |
        filtered_df["Kabupaten"].str.contains(search_text, case=False, na=False)
    )
    filtered_df = filtered_df[mask]

st.write(f"**Menampilkan {len(filtered_df)} dari {len(df)} baris**")

# ======================================================
# TABLE
# ======================================================
st.markdown('<div class="section-header"><h3>📋 Data Detail</h3></div>', unsafe_allow_html=True)

# Add sheet column to display
display_columns = ["__sheet"] + required_columns

def style_status(val):
    """Style untuk kolom status"""
    cat = normalize_status(val)
    color = get_status_color(cat)
    return f"background-color:{color};color:white;font-weight:600;padding:5px;border-radius:5px;"

# Display dataframe dengan styling
st.dataframe(
    filtered_df[display_columns].style.applymap(
        style_status, 
        subset=["Status_Text"]
    ),
    use_container_width=True,
    height=500
)

# ======================================================
# DOWNLOAD
# ======================================================
col_dl1, col_dl2 = st.columns(2)

with col_dl1:
    st.download_button(
        "📥 Download CSV (Hasil Filter)",
        filtered_df.to_csv(index=False),
        f"monitoring_filtered_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
        "text/csv",
        use_container_width=True
    )

with col_dl2:
    st.download_button(
        "📥 Download CSV (Semua Data)",
        df.to_csv(index=False),
        f"monitoring_all_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
        "text/csv",
        use_container_width=True
    )

# ======================================================
# BREAKDOWN PER SHEET
# ======================================================
with st.expander("📊 Lihat Breakdown Per Sheet"):
    st.subheader("Status per Sheet")
    
    sheet_summary = df.groupby(["__sheet", "Status_Category"]).size().reset_index(name="Jumlah")
    pivot_summary = sheet_summary.pivot(index="__sheet", columns="Status_Category", values="Jumlah").fillna(0)
    
    st.dataframe(pivot_summary, use_container_width=True)

# ======================================================
# FOOTER
# ======================================================
st.markdown("---")
st.markdown("""
<div class='dashboard-footer'>
    <p>🚀 Dashboard Monitoring v3.1 • Multi Sheet • Auto Refresh • Built with Streamlit</p>
</div>
""", unsafe_allow_html=True)
