import streamlit as st
import pandas as pd
import re
import requests
from io import StringIO

# ======================================================
# CONFIG
# ======================================================
st.set_page_config(
    page_title="Dashboard Monitoring Pekerjaan",
    layout="wide",
    initial_sidebar_state="expanded"
)

REFRESH_INTERVAL = 300  # 5 menit

# Custom CSS untuk desain modern
st.markdown("""
<style>
    /* Main background */
    .main {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    }
    
    /* Content container */
    .block-container {
        padding: 2rem 3rem;
        background: white;
        border-radius: 20px;
        margin: 2rem auto;
        box-shadow: 0 20px 60px rgba(0,0,0,0.3);
    }
    
    /* Header styling */
    h1 {
        color: #1e293b;
        font-weight: 800;
        font-size: 2.5rem !important;
        margin-bottom: 0.5rem !important;
        text-align: center;
    }
    
    h2 {
        color: #334155;
        font-weight: 700;
        font-size: 1.5rem !important;
        margin-top: 2rem !important;
    }
    
    h3 {
        color: #475569;
        font-weight: 600;
    }
    
    /* Metric cards */
    [data-testid="stMetricValue"] {
        font-size: 2rem;
        font-weight: 700;
    }
    
    [data-testid="metric-container"] {
        background: linear-gradient(135deg, #f8fafc 0%, #e2e8f0 100%);
        padding: 1.5rem;
        border-radius: 15px;
        box-shadow: 0 4px 6px rgba(0,0,0,0.1);
        border-left: 5px solid;
        transition: transform 0.2s;
    }
    
    [data-testid="metric-container"]:hover {
        transform: translateY(-5px);
        box-shadow: 0 8px 12px rgba(0,0,0,0.15);
    }
    
    /* Status badges in table */
    .stDataFrame {
        border-radius: 10px;
        overflow: hidden;
        box-shadow: 0 4px 6px rgba(0,0,0,0.1);
    }
    
    /* Buttons */
    .stButton > button {
        width: 100%;
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        border: none;
        padding: 0.75rem 2rem;
        font-weight: 600;
        border-radius: 10px;
        box-shadow: 0 4px 6px rgba(0,0,0,0.1);
        transition: all 0.3s;
    }
    
    .stButton > button:hover {
        transform: translateY(-2px);
        box-shadow: 0 6px 12px rgba(0,0,0,0.2);
    }
    
    /* Input fields */
    .stTextInput > div > div > input {
        border-radius: 10px;
        border: 2px solid #e2e8f0;
        padding: 0.75rem;
        font-size: 1rem;
    }
    
    .stTextInput > div > div > input:focus {
        border-color: #667eea;
        box-shadow: 0 0 0 3px rgba(102,126,234,0.1);
    }
    
    /* Selectbox */
    .stMultiSelect > div > div {
        border-radius: 10px;
    }
    
    /* Divider */
    hr {
        margin: 2rem 0;
        border: none;
        height: 2px;
        background: linear-gradient(90deg, transparent, #e2e8f0, transparent);
    }
    
    /* Info/Warning/Error boxes */
    .stAlert {
        border-radius: 10px;
        border: none;
        padding: 1rem 1.5rem;
    }
    
    /* Sidebar */
    [data-testid="stSidebar"] {
        background: linear-gradient(180deg, #1e293b 0%, #334155 100%);
    }
    
    [data-testid="stSidebar"] h1, 
    [data-testid="stSidebar"] h2, 
    [data-testid="stSidebar"] h3,
    [data-testid="stSidebar"] label,
    [data-testid="stSidebar"] p {
        color: white !important;
    }
</style>
""", unsafe_allow_html=True)

# Auto refresh
st.markdown(
    f"<meta http-equiv='refresh' content='{REFRESH_INTERVAL}'>",
    unsafe_allow_html=True
)

# ======================================================
# HEADER
# ======================================================
st.title("📊 Dashboard Monitoring Pekerjaan")
st.markdown("""
<div style='text-align: center; margin-bottom: 2rem;'>
    <p style='color: #64748b; font-size: 1.1rem;'>
        Monitoring real-time progress pekerjaan dari Google Spreadsheet
    </p>
</div>
""", unsafe_allow_html=True)

# ======================================================
# SIDEBAR - INPUT & CONFIG
# ======================================================
with st.sidebar:
    st.markdown("### ⚙️ Konfigurasi")
    
    sheet_url = st.text_input(
        "🔗 Link Google Spreadsheet",
        placeholder="https://docs.google.com/spreadsheets/d/xxxxx/edit",
        help="Pastikan spreadsheet sudah di-share dengan akses 'Anyone with the link can view'"
    )
    
    # Extract sheet ID
    sheet_id = None
    if sheet_url:
        match = re.search(r"/spreadsheets/d/([a-zA-Z0-9-_]+)", sheet_url)
        if match:
            sheet_id = match.group(1)
    
    # Sheet selector
    gid = None
    if sheet_id:
        st.markdown("---")
        st.markdown("### 📑 Pilih Sheet")
        
        # Input manual GID
        gid_input = st.text_input(
            "GID Sheet (opsional)",
            placeholder="0",
            help="Kosongkan untuk sheet pertama (default), atau masukkan GID sheet tertentu"
        )
        
        if gid_input:
            try:
                gid = int(gid_input)
            except:
                st.warning("GID harus berupa angka")
        
        st.info("💡 **Cara mendapatkan GID:**\n1. Buka sheet yang diinginkan\n2. Lihat URL: `...#gid=123456789`\n3. Angka setelah `gid=` adalah GID-nya")
    
    st.markdown("---")
    load_btn = st.button("📥 Load Data", use_container_width=True)
    
    st.markdown("---")
    st.markdown("### 📌 Informasi")
    st.caption(f"🔄 Auto refresh: {REFRESH_INTERVAL//60} menit")
    st.caption("📊 Dashboard versi 2.0")

# ======================================================
# UTIL: LOAD DATA FROM SHEET
# ======================================================
@st.cache_data(ttl=REFRESH_INTERVAL)
def load_data_from_sheet(sheet_id, gid=None):
    """Load data dari Google Sheets dengan support multiple sheets"""
    if gid is not None:
        csv_url = f"https://docs.google.com/spreadsheets/d/{sheet_id}/export?format=csv&gid={gid}"
    else:
        csv_url = f"https://docs.google.com/spreadsheets/d/{sheet_id}/export?format=csv"
    
    response = requests.get(csv_url)
    response.raise_for_status()
    
    csv_data = StringIO(response.text)
    return pd.read_csv(csv_data)

# ======================================================
# LOAD DATA
# ======================================================
if not sheet_url:
    st.info("👈 Silakan masukkan link Google Spreadsheet di sidebar")
    st.stop()

if not sheet_id:
    st.error("❌ Link Google Spreadsheet tidak valid")
    st.stop()

if load_btn:
    with st.spinner("🔄 Memuat data..."):
        try:
            df = load_data_from_sheet(sheet_id, gid)
            st.success("✅ Data berhasil dimuat!")
            st.session_state['df'] = df
            st.session_state['loaded'] = True
        except Exception as e:
            st.error(f"❌ Gagal memuat data: {str(e)}")
            st.info("**Troubleshooting:**\n- Pastikan spreadsheet sudah di-share dengan akses publik\n- Periksa kembali GID sheet jika menggunakan sheet tertentu\n- Coba refresh halaman")
            st.stop()

if 'loaded' not in st.session_state:
    st.warning("⚠️ Klik **Load Data** di sidebar untuk memulai")
    st.stop()

df = st.session_state['df']

# ======================================================
# VALIDASI KOLOM
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
    st.info(f"Kolom yang tersedia: {', '.join(df.columns.tolist())}")
    st.stop()

df = df[required_columns].copy()

# ======================================================
# STATUS PROCESSING
# ======================================================
def get_status_category(val):
    """Kategorisasi status"""
    val = str(val).upper()
    
    if "BAPP" in val or "KURANG" in val:
        return "Kurang BAPP"
    elif "PROSES" in val or "INSTALASI" in val:
        return "Sedang Diproses"
    elif "SELESAI" in val:
        return "Selesai"
    else:
        return "Belum Dikerjakan"

df['Status_Category'] = df['Status'].apply(get_status_category)

def status_style(val):
    """Style untuk status di tabel"""
    val = str(val).upper()
    
    if "BAPP" in val or "KURANG" in val:
        return "background: linear-gradient(135deg, #3b82f6, #2563eb); color: white; padding: 8px 12px; border-radius: 8px; font-weight: 600; text-align: center;"
    elif "PROSES" in val or "INSTALASI" in val:
        return "background: linear-gradient(135deg, #fbbf24, #f59e0b); color: black; padding: 8px 12px; border-radius: 8px; font-weight: 600; text-align: center;"
    elif "SELESAI" in val:
        return "background: linear-gradient(135deg, #22c55e, #16a34a); color: white; padding: 8px 12px; border-radius: 8px; font-weight: 600; text-align: center;"
    else:
        return "background: linear-gradient(135deg, #e5e7eb, #d1d5db); color: black; padding: 8px 12px; border-radius: 8px; font-weight: 600; text-align: center;"

# ======================================================
# METRICS DASHBOARD
# ======================================================
st.markdown("### 📈 Ringkasan Status")

col1, col2, col3, col4 = st.columns(4)

total = len(df)
belum = (df['Status_Category'] == 'Belum Dikerjakan').sum()
kurang_bapp = (df['Status_Category'] == 'Kurang BAPP').sum()
proses = (df['Status_Category'] == 'Sedang Diproses').sum()
selesai = (df['Status_Category'] == 'Selesai').sum()

with col1:
    st.markdown("""
    <div style='border-left-color: #9ca3af;'>
    """, unsafe_allow_html=True)
    st.metric(
        label="⚪ Belum Dikerjakan",
        value=belum,
        delta=f"{(belum/total*100):.1f}%" if total > 0 else "0%"
    )
    st.markdown("</div>", unsafe_allow_html=True)

with col2:
    st.markdown("""
    <div style='border-left-color: #3b82f6;'>
    """, unsafe_allow_html=True)
    st.metric(
        label="🔵 Kurang BAPP",
        value=kurang_bapp,
        delta=f"{(kurang_bapp/total*100):.1f}%" if total > 0 else "0%"
    )
    st.markdown("</div>", unsafe_allow_html=True)

with col3:
    st.markdown("""
    <div style='border-left-color: #fbbf24;'>
    """, unsafe_allow_html=True)
    st.metric(
        label="🟡 Sedang Diproses",
        value=proses,
        delta=f"{(proses/total*100):.1f}%" if total > 0 else "0%"
    )
    st.markdown("</div>", unsafe_allow_html=True)

with col4:
    st.markdown("""
    <div style='border-left-color: #22c55e;'>
    """, unsafe_allow_html=True)
    st.metric(
        label="🟢 Selesai",
        value=selesai,
        delta=f"{(selesai/total*100):.1f}%" if total > 0 else "0%"
    )
    st.markdown("</div>", unsafe_allow_html=True)

# Progress bar keseluruhan
st.markdown("---")
progress_pct = (selesai / total * 100) if total > 0 else 0
st.markdown(f"### 🎯 Progress Keseluruhan: {progress_pct:.1f}%")
st.progress(progress_pct / 100)

# ======================================================
# FILTER
# ======================================================
st.markdown("---")
st.markdown("### 🔎 Filter Data")

col_f1, col_f2, col_f3 = st.columns(3)

with col_f1:
    provinsi_options = sorted(df["Propinsi"].dropna().unique())
    provinsi_filter = st.multiselect(
        "📍 Provinsi",
        provinsi_options,
        default=provinsi_options
    )

with col_f2:
    jenjang_options = sorted(df["Jenjang"].dropna().unique())
    jenjang_filter = st.multiselect(
        "🎓 Jenjang",
        jenjang_options,
        default=jenjang_options
    )

with col_f3:
    status_options = ["Semua", "Belum Dikerjakan", "Kurang BAPP", "Sedang Diproses", "Selesai"]
    status_filter = st.selectbox(
        "🏷️ Status",
        status_options
    )

# Apply filters
filtered_df = df[
    (df["Propinsi"].isin(provinsi_filter)) &
    (df["Jenjang"].isin(jenjang_filter))
]

if status_filter != "Semua":
    filtered_df = filtered_df[filtered_df['Status_Category'] == status_filter]

# ======================================================
# SEARCH
# ======================================================
search_term = st.text_input("🔍 Cari berdasarkan Nama, Trans. ID, atau Kabupaten", "")
if search_term:
    filtered_df = filtered_df[
        filtered_df['Nama'].str.contains(search_term, case=False, na=False) |
        filtered_df['Trans. ID'].astype(str).str.contains(search_term, case=False, na=False) |
        filtered_df['Kabupaten'].str.contains(search_term, case=False, na=False)
    ]

# ======================================================
# TABLE
# ======================================================
st.markdown("---")
st.markdown(f"### 📋 Detail Monitoring ({len(filtered_df)} data)")

if len(filtered_df) > 0:
    # Display styled dataframe
    display_df = filtered_df.drop(columns=['Status_Category'])
    
    st.dataframe(
        display_df.style.applymap(status_style, subset=["Status"]),
        use_container_width=True,
        height=500
    )
    
    # Download button
    csv = filtered_df.to_csv(index=False).encode('utf-8')
    st.download_button(
        label="📥 Download Data (CSV)",
        data=csv,
        file_name="monitoring_data.csv",
        mime="text/csv",
        use_container_width=True
    )
else:
    st.warning("⚠️ Tidak ada data yang sesuai dengan filter")

# ======================================================
# FOOTER
# ======================================================
st.markdown("---")
st.markdown("""
<div style='text-align: center; color: #64748b; padding: 2rem 0;'>
    <p style='margin: 0;'>⏱️ Auto refresh setiap 5 menit</p>
    <p style='margin: 0.5rem 0 0 0;'>Dashboard Monitoring Pekerjaan v2.0 | Built with Streamlit</p>
</div>
""", unsafe_allow_html=True)
