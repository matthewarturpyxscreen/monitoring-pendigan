import streamlit as st
import pandas as pd
import re
from datetime import datetime

# ======================================================
# CONFIG
# ======================================================
st.set_page_config(
    page_title="Dashboard Monitoring Pekerjaan",
    layout="wide",
    initial_sidebar_state="expanded",
    menu_items={
        'About': "Dashboard Monitoring Pekerjaan v3.0"
    }
)

REFRESH_INTERVAL = 300  # 5 menit

# ======================================================
# MODERN PROFESSIONAL CSS
# ======================================================
st.markdown("""
<style>
    /* Import Google Fonts */
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');
    
    /* Global Styles */
    * {
        font-family: 'Inter', sans-serif;
    }
    
    /* Hide Streamlit Branding */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
    
    /* Main Container */
    .main {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 2rem;
    }
    
    /* Glass Card Effect */
    .glass-card {
        background: rgba(255, 255, 255, 0.95);
        backdrop-filter: blur(10px);
        border-radius: 16px;
        padding: 2rem;
        box-shadow: 0 8px 32px rgba(0, 0, 0, 0.1);
        border: 1px solid rgba(255, 255, 255, 0.2);
        margin-bottom: 1.5rem;
    }
    
    /* Header Styles */
    .dashboard-header {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        padding: 2rem;
        border-radius: 16px;
        text-align: center;
        box-shadow: 0 8px 32px rgba(102, 126, 234, 0.4);
        margin-bottom: 2rem;
    }
    
    .dashboard-header h1 {
        margin: 0;
        font-size: 2.5rem;
        font-weight: 700;
        text-shadow: 2px 2px 4px rgba(0, 0, 0, 0.2);
    }
    
    .dashboard-header p {
        margin: 0.5rem 0 0 0;
        font-size: 1rem;
        opacity: 0.95;
    }
    
    /* Metric Cards */
    div[data-testid="stMetricValue"] {
        font-size: 2rem;
        font-weight: 700;
        color: #1e293b;
    }
    
    div[data-testid="stMetricLabel"] {
        font-size: 0.875rem;
        font-weight: 600;
        color: #64748b;
        text-transform: uppercase;
        letter-spacing: 0.05em;
    }
    
    /* Buttons */
    .stButton > button {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        border: none;
        border-radius: 8px;
        padding: 0.75rem 2rem;
        font-weight: 600;
        transition: all 0.3s ease;
        box-shadow: 0 4px 16px rgba(102, 126, 234, 0.3);
    }
    
    .stButton > button:hover {
        transform: translateY(-2px);
        box-shadow: 0 6px 20px rgba(102, 126, 234, 0.4);
    }
    
    /* Input Fields */
    .stTextInput > div > div > input {
        border-radius: 8px;
        border: 2px solid #e2e8f0;
        padding: 0.75rem;
        transition: all 0.3s ease;
    }
    
    .stTextInput > div > div > input:focus {
        border-color: #667eea;
        box-shadow: 0 0 0 3px rgba(102, 126, 234, 0.1);
    }
    
    /* Select Boxes */
    .stSelectbox > div > div > div {
        border-radius: 8px;
        border: 2px solid #e2e8f0;
    }
    
    /* Data Table */
    .dataframe {
        border-radius: 8px;
        overflow: hidden;
        box-shadow: 0 4px 16px rgba(0, 0, 0, 0.05);
    }
    
    /* Section Headers */
    .section-header {
        background: white;
        padding: 1.5rem;
        border-radius: 12px;
        box-shadow: 0 2px 8px rgba(0, 0, 0, 0.05);
        margin-bottom: 1.5rem;
        border-left: 4px solid #667eea;
    }
    
    .section-header h3 {
        margin: 0;
        color: #1e293b;
        font-size: 1.5rem;
        font-weight: 700;
    }
    
    /* Info Box */
    .info-box {
        background: linear-gradient(135deg, #f0f9ff 0%, #e0f2fe 100%);
        border-left: 4px solid #3b82f6;
        padding: 1rem;
        border-radius: 8px;
        margin: 1rem 0;
    }
    
    /* Success Box */
    .success-box {
        background: linear-gradient(135deg, #f0fdf4 0%, #dcfce7 100%);
        border-left: 4px solid #10b981;
        padding: 1rem;
        border-radius: 8px;
        margin: 1rem 0;
    }
    
    /* Warning Box */
    .warning-box {
        background: linear-gradient(135deg, #fffbeb 0%, #fef3c7 100%);
        border-left: 4px solid #f59e0b;
        padding: 1rem;
        border-radius: 8px;
        margin: 1rem 0;
    }
    
    /* Sidebar Styling */
    section[data-testid="stSidebar"] {
        background: linear-gradient(180deg, #667eea 0%, #764ba2 100%);
    }
    
    section[data-testid="stSidebar"] .glass-card {
        background: rgba(255, 255, 255, 0.95);
    }
    
    /* Footer */
    .dashboard-footer {
        background: white;
        padding: 1.5rem;
        border-radius: 12px;
        text-align: center;
        color: #64748b;
        margin-top: 2rem;
        box-shadow: 0 2px 8px rgba(0, 0, 0, 0.05);
    }
</style>
""", unsafe_allow_html=True)

# Auto refresh
st.markdown(
    f"""<meta http-equiv="refresh" content="{REFRESH_INTERVAL}">""",
    unsafe_allow_html=True
)

# ======================================================
# UTILITY FUNCTIONS
# ======================================================
def convert_to_csv_url(sheet_id: str, gid: str = "0") -> str:
    """Convert Google Sheets URL to CSV export URL"""
    return f"https://docs.google.com/spreadsheets/d/{sheet_id}/export?format=csv&gid={gid}"

@st.cache_data(ttl=REFRESH_INTERVAL)
def load_data(sheet_id: str, gid: str = "0"):
    """Load data from Google Sheets"""
    try:
        csv_url = convert_to_csv_url(sheet_id, gid)
        df = pd.read_csv(csv_url)
        return df, None
    except Exception as e:
        return None, str(e)

def categorize_status(val):
    """Categorize status into predefined categories"""
    val = str(val).upper()
    if "BAPP" in val or "KURANG" in val:
        return "Kurang BAPP"
    elif "PROSES" in val or "INSTALASI" in val:
        return "Sedang Diproses"
    elif "SELESAI" in val:
        return "Selesai"
    else:
        return "Belum Dikerjakan"

def get_status_color(status):
    """Get color for status"""
    colors = {
        "Belum Dikerjakan": "#94a3b8",
        "Kurang BAPP": "#3b82f6",
        "Sedang Diproses": "#f59e0b",
        "Selesai": "#10b981"
    }
    return colors.get(status, "#94a3b8")

# ======================================================
# HEADER
# ======================================================
st.markdown(f"""
<div class='dashboard-header'>
    <h1>📊 Dashboard Monitoring Pekerjaan</h1>
    <p>Real-time Monitoring & Analytics System • Last Updated: {datetime.now().strftime('%d %B %Y, %H:%M:%S')}</p>
</div>
""", unsafe_allow_html=True)

# ======================================================
# SIDEBAR
# ======================================================
with st.sidebar:
    st.markdown("""
<div class='glass-card'>
    <div style='text-align: center;'>
        <h2 style='margin: 0; font-size: 1.5rem;'>⚙️</h2>
        <h3 style='margin: 0.5rem 0; color: #1e293b;'>Pengaturan</h3>
    </div>
</div>
    """, unsafe_allow_html=True)
    
    sheet_url = st.text_input(
        "🔗 Google Spreadsheet URL",
        placeholder="https://docs.google.com/spreadsheets/d/xxxxx",
        help="Pastikan spreadsheet diatur ke 'Anyone with the link can view'"
    )
    
    # Extract Sheet ID and GID
    sheet_id = None
    default_gid = "0"
    
    if sheet_url:
        match = re.search(r"/spreadsheets/d/([a-zA-Z0-9-_]+)", sheet_url)
        if match:
            sheet_id = match.group(1)
            st.success("✅ Sheet ID terdeteksi")
            
            # Try to extract GID from URL
            gid_match = re.search(r"[#&]gid=([0-9]+)", sheet_url)
            if gid_match:
                default_gid = gid_match.group(1)
                st.info(f"📄 GID terdeteksi: {default_gid}")
    
    gid_input = st.text_input(
        "📄 Sheet GID (opsional)",
        value=default_gid,
        help="0 = sheet pertama. Cek URL sheet untuk GID lain (gid=xxxxx)"
    )
    
    st.markdown("<div style='margin: 1rem 0;'></div>", unsafe_allow_html=True)
    load_btn = st.button("📥 Load Data")
    
    st.markdown("---")
    
    st.markdown("""
<div class='info-box'>
    <h4 style='margin: 0 0 0.5rem 0; color: #1e293b;'>ℹ️ Informasi</h4>
    <ul style='margin: 0; padding-left: 1.2rem; color: #475569;'>
        <li>Dashboard otomatis refresh setiap 5 menit</li>
        <li>Data diambil dari sheet yang dipilih</li>
        <li>Gunakan filter untuk analisis detail</li>
    </ul>
</div>
    """, unsafe_allow_html=True)

# ======================================================
# MAIN LOGIC
# ======================================================
if not sheet_url:
    st.markdown("""
<div class='glass-card' style='text-align: center; padding: 4rem 2rem;'>
    <h2 style='color: #1e293b; margin-bottom: 1rem;'>👈 Mulai dengan memasukkan URL Google Spreadsheet</h2>
    <p style='color: #64748b; font-size: 1.1rem;'>Masukkan link di sidebar untuk memulai monitoring</p>
</div>
    """, unsafe_allow_html=True)
    st.stop()

if not load_btn and 'df' not in st.session_state:
    st.info("👈 Klik tombol **Load Data** di sidebar untuk memulai")
    st.stop()

# Load Data
if load_btn or 'df' in st.session_state:
    if load_btn:
        with st.spinner("⏳ Memuat data dari Google Sheets..."):
            df, error = load_data(sheet_id, gid_input)
            
            if error:
                st.error(f"❌ Gagal memuat data: {error}")
                
                # Helpful error messages
                with st.expander("💡 Panduan Troubleshooting"):
                    st.markdown("""
                    ### Kemungkinan Penyebab Error:
                    
                    **1. Izin Akses Belum Diatur**
                    - Buka Google Sheets Anda
                    - Klik tombol **Share** (pojok kanan atas)
                    - Pilih **"Anyone with the link"**
                    - Set role ke **"Viewer"**
                    - Klik **Done**
                    
                    **2. GID Sheet Salah**
                    - GID `0` = sheet pertama
                    - Untuk sheet lain, lihat URL: `...#gid=123456`
                    - Masukkan angka setelah `gid=` di field GID
                    
                    **3. URL Tidak Valid**
                    - Pastikan URL lengkap dari browser
                    - Format: `https://docs.google.com/spreadsheets/d/...`
                    
                    **4. Sheet Kosong atau Terhapus**
                    - Pastikan sheet memiliki data
                    - Cek apakah sheet dengan GID tersebut masih ada
                    """)
                    
                    st.code(f"""
URL yang digunakan:
{convert_to_csv_url(sheet_id, gid_input)}

Coba buka URL di atas di browser baru.
Jika muncul error atau download gagal, berarti ada masalah izin akses.
                    """)
                
                st.stop()
            
            if df is None or df.empty:
                st.error("❌ Data kosong atau tidak dapat diakses")
                st.info("💡 Pastikan sheet memiliki data dan GID benar")
                st.stop()
            
            st.session_state['df'] = df
            st.success(f"✅ Berhasil memuat {len(df)} baris data")
    
    df = st.session_state['df']

    # ======================================================
    # VALIDATE COLUMNS
    # ======================================================
    required_columns = [
        "Trans. ID", "Nama", "Jenjang", "Kabupaten", "Propinsi",
        "Status", "Instalasi", "Selesai", "Keterangan", "Petugas"
    ]
    
    missing_cols = [c for c in required_columns if c not in df.columns]
    
    if missing_cols:
        st.error(f"❌ Kolom tidak ditemukan: {', '.join(missing_cols)}")
        with st.expander("📋 Lihat kolom yang tersedia"):
            st.write(df.columns.tolist())
        st.stop()

    # ======================================================
    # PROCESS DATA
    # ======================================================
    df['Status_Category'] = df['Status'].apply(categorize_status)

    # ======================================================
    # METRICS OVERVIEW
    # ======================================================
    st.markdown('<div class="section-header"><h3>📈 Ringkasan Status</h3></div>', unsafe_allow_html=True)
    
    col1, col2, col3, col4 = st.columns(4)
    
    total = len(df)
    belum = (df['Status_Category'] == 'Belum Dikerjakan').sum()
    kurang = (df['Status_Category'] == 'Kurang BAPP').sum()
    proses = (df['Status_Category'] == 'Sedang Diproses').sum()
    selesai = (df['Status_Category'] == 'Selesai').sum()
    
    with col1:
        st.metric(
            label="BELUM DIKERJAKAN",
            value=f"{belum:,}",
            delta=f"{belum/total*100:.1f}% dari total"
        )
    
    with col2:
        st.metric(
            label="KURANG BAPP",
            value=f"{kurang:,}",
            delta=f"{kurang/total*100:.1f}% dari total"
        )
    
    with col3:
        st.metric(
            label="SEDANG DIPROSES",
            value=f"{proses:,}",
            delta=f"{proses/total*100:.1f}% dari total"
        )
    
    with col4:
        st.metric(
            label="SELESAI",
            value=f"{selesai:,}",
            delta=f"{selesai/total*100:.1f}% dari total"
        )

    # ======================================================
    # VISUALIZATIONS
    # ======================================================
    st.markdown('<div class="section-header"><h3>📊 Visualisasi Data</h3></div>', unsafe_allow_html=True)
    
    col_chart1, col_chart2 = st.columns(2)
    
    with col_chart1:
        st.markdown("#### Distribusi Status")
        # Status Distribution
        status_counts = df['Status_Category'].value_counts()
        st.bar_chart(status_counts, use_container_width=True, height=300)
    
    with col_chart2:
        st.markdown("#### Top 10 Kabupaten")
        # Top 10 Kabupaten
        top_kabupaten = df['Kabupaten'].value_counts().head(10)
        st.bar_chart(top_kabupaten, use_container_width=True, height=300)

    # ======================================================
    # FILTERS
    # ======================================================
    st.markdown('<div class="section-header"><h3>🔎 Filter & Pencarian</h3></div>', unsafe_allow_html=True)
    
    col_f1, col_f2, col_f3, col_f4 = st.columns(4)
    
    with col_f1:
        provinsi_options = ['Semua'] + sorted(df["Propinsi"].dropna().unique().tolist())
        provinsi_filter = st.selectbox("📍 Provinsi", provinsi_options)
    
    with col_f2:
        jenjang_options = ['Semua'] + sorted(df["Jenjang"].dropna().unique().tolist())
        jenjang_filter = st.selectbox("🎓 Jenjang", jenjang_options)
    
    with col_f3:
        status_options = ['Semua'] + ['Belum Dikerjakan', 'Kurang BAPP', 'Sedang Diproses', 'Selesai']
        status_filter = st.selectbox("📊 Status", status_options)
    
    with col_f4:
        search_term = st.text_input("🔍 Cari Nama/Trans ID", "")

    # Apply filters
    filtered_df = df.copy()
    
    if provinsi_filter != 'Semua':
        filtered_df = filtered_df[filtered_df["Propinsi"] == provinsi_filter]
    
    if jenjang_filter != 'Semua':
        filtered_df = filtered_df[filtered_df["Jenjang"] == jenjang_filter]
    
    if status_filter != 'Semua':
        filtered_df = filtered_df[filtered_df["Status_Category"] == status_filter]
    
    if search_term:
        filtered_df = filtered_df[
            filtered_df["Nama"].str.contains(search_term, case=False, na=False) |
            filtered_df["Trans. ID"].astype(str).str.contains(search_term, case=False, na=False)
        ]

    # ======================================================
    # DATA TABLE
    # ======================================================
    st.markdown(f'<div class="section-header"><h3>📋 Detail Data ({len(filtered_df):,} dari {total:,} records)</h3></div>', unsafe_allow_html=True)
    
    # Add status styling to dataframe
    def status_style(val):
        val = str(val)
        category = categorize_status(val)
        color = get_status_color(category)
        return f"background-color: {color}; color: white; font-weight: 600; padding: 0.25rem 0.5rem; border-radius: 4px;"
    
    display_df = filtered_df[required_columns].copy()
    
    st.dataframe(
        display_df.style.applymap(status_style, subset=["Status"]),
        use_container_width=True,
        height=500
    )

    # ======================================================
    # EXPORT & ACTIONS
    # ======================================================
    st.markdown("---")
    
    col_action1, col_action2, col_action3 = st.columns([2, 1, 1])
    
    with col_action2:
        csv = filtered_df.to_csv(index=False).encode('utf-8')
        st.download_button(
            label="📥 Download CSV",
            data=csv,
            file_name=f"monitoring_data_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
            mime="text/csv",
            use_container_width=True
        )
    
    with col_action3:
        if st.button("🔄 Refresh Data", use_container_width=True):
            st.cache_data.clear()
            st.rerun()

# ======================================================
# FOOTER
# ======================================================
st.markdown("---")
st.markdown("""
<div class='dashboard-footer'>
    <p style='margin: 0; font-weight: 600;'>🚀 Dashboard Monitoring v3.0 • Powered by Streamlit</p>
</div>
""", unsafe_allow_html=True)
