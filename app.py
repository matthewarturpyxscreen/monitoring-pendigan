import streamlit as st
import pandas as pd
import re
import plotly.express as px
import plotly.graph_objects as go
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
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');
    
    /* Global Styles */
    * {
        font-family: 'Inter', sans-serif;
    }
    
    /* Main Background */
    .main {
        background: #f8fafc;
        padding: 1.5rem;
    }
    
    /* Remove default padding */
    .block-container {
        padding-top: 2rem;
        padding-bottom: 2rem;
    }
    
    /* Header Styling */
    .dashboard-header {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 2rem 2.5rem;
        border-radius: 16px;
        color: white;
        margin-bottom: 2rem;
        box-shadow: 0 10px 30px rgba(102, 126, 234, 0.3);
    }
    
    .dashboard-title {
        font-size: 2.5rem;
        font-weight: 700;
        margin: 0;
        letter-spacing: -0.5px;
    }
    
    .dashboard-subtitle {
        font-size: 1rem;
        opacity: 0.95;
        margin-top: 0.5rem;
        font-weight: 400;
    }
    
    /* Metric Cards */
    [data-testid="stMetricValue"] {
        font-size: 2.5rem !important;
        font-weight: 700 !important;
        color: #1e293b;
    }
    
    [data-testid="stMetricLabel"] {
        font-size: 0.875rem !important;
        font-weight: 600 !important;
        color: #64748b;
        text-transform: uppercase;
        letter-spacing: 0.5px;
    }
    
    [data-testid="stMetricDelta"] {
        font-size: 0.875rem !important;
        font-weight: 500 !important;
    }
    
    /* Card Container */
    .metric-container {
        background: white;
        padding: 1.5rem;
        border-radius: 12px;
        box-shadow: 0 1px 3px rgba(0,0,0,0.1);
        border: 1px solid #e2e8f0;
        transition: all 0.3s ease;
    }
    
    .metric-container:hover {
        box-shadow: 0 8px 16px rgba(0,0,0,0.1);
        transform: translateY(-2px);
    }
    
    /* Section Headers */
    .section-header {
        font-size: 1.5rem;
        font-weight: 700;
        color: #1e293b;
        margin: 2rem 0 1rem 0;
        padding-bottom: 0.5rem;
        border-bottom: 3px solid #667eea;
        display: inline-block;
    }
    
    /* Sidebar Styling */
    [data-testid="stSidebar"] {
        background: white;
        border-right: 1px solid #e2e8f0;
    }
    
    [data-testid="stSidebar"] .sidebar-content {
        padding: 1.5rem;
    }
    
    /* Input Fields */
    .stTextInput > div > div > input,
    .stTextArea > div > div > textarea {
        border-radius: 8px;
        border: 1.5px solid #e2e8f0;
        padding: 0.75rem;
        font-size: 0.95rem;
        transition: all 0.2s;
    }
    
    .stTextInput > div > div > input:focus,
    .stTextArea > div > div > textarea:focus {
        border-color: #667eea;
        box-shadow: 0 0 0 3px rgba(102, 126, 234, 0.1);
    }
    
    /* Buttons */
    .stButton > button {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        border: none;
        border-radius: 8px;
        padding: 0.75rem 1.5rem;
        font-weight: 600;
        font-size: 0.95rem;
        transition: all 0.3s;
        width: 100%;
        box-shadow: 0 4px 12px rgba(102, 126, 234, 0.3);
    }
    
    .stButton > button:hover {
        transform: translateY(-2px);
        box-shadow: 0 6px 20px rgba(102, 126, 234, 0.4);
    }
    
    /* Download Button */
    .stDownloadButton > button {
        background: white;
        color: #667eea;
        border: 2px solid #667eea;
        border-radius: 8px;
        padding: 0.75rem 1.5rem;
        font-weight: 600;
        transition: all 0.3s;
    }
    
    .stDownloadButton > button:hover {
        background: #667eea;
        color: white;
    }
    
    /* Multiselect */
    .stMultiSelect > div > div {
        border-radius: 8px;
        border: 1.5px solid #e2e8f0;
    }
    
    /* DataFrame Styling */
    .stDataFrame {
        border-radius: 12px;
        overflow: hidden;
        box-shadow: 0 1px 3px rgba(0,0,0,0.1);
        border: 1px solid #e2e8f0;
    }
    
    /* Info/Warning/Error Boxes */
    .stAlert {
        border-radius: 8px;
        border-left: 4px solid;
        padding: 1rem 1.25rem;
    }
    
    /* Divider */
    hr {
        margin: 2rem 0;
        border: none;
        border-top: 1px solid #e2e8f0;
    }
    
    /* Status Badge */
    .status-badge {
        padding: 0.25rem 0.75rem;
        border-radius: 6px;
        font-weight: 600;
        font-size: 0.85rem;
        display: inline-block;
    }
    
    /* Hide Streamlit Branding */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    
    /* Sidebar Logo */
    .sidebar-logo {
        text-align: center;
        padding: 1rem 0 2rem 0;
        border-bottom: 1px solid #e2e8f0;
        margin-bottom: 2rem;
    }
    
    /* Caption Styling */
    .caption-text {
        color: #64748b;
        font-size: 0.875rem;
        margin-top: 0.5rem;
    }
    </style>
""", unsafe_allow_html=True)

# Auto refresh
st.markdown(
    f"<meta http-equiv='refresh' content='{REFRESH_INTERVAL}'>",
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
    <div class="dashboard-header">
        <h1 class="dashboard-title">📊 Dashboard Monitoring Pekerjaan</h1>
        <p class="dashboard-subtitle">Real-time Monitoring & Analytics System • Last Updated: {datetime.now().strftime('%d %B %Y, %H:%M:%S')}</p>
    </div>
""", unsafe_allow_html=True)

# ======================================================
# SIDEBAR
# ======================================================
with st.sidebar:
    st.markdown("""
        <div class="sidebar-logo">
            <h2 style="margin: 0; color: #667eea;">⚙️</h2>
            <h3 style="margin: 0.5rem 0 0 0; color: #1e293b;">Pengaturan</h3>
        </div>
    """, unsafe_allow_html=True)
    
    sheet_url = st.text_input(
        "🔗 Google Spreadsheet URL",
        placeholder="https://docs.google.com/spreadsheets/d/xxxxx",
        help="Pastikan spreadsheet diatur ke 'Anyone with the link can view'"
    )
    
    # Extract Sheet ID
    sheet_id = None
    if sheet_url:
        match = re.search(r"/spreadsheets/d/([a-zA-Z0-9-_]+)", sheet_url)
        if match:
            sheet_id = match.group(1)
            st.success("✅ Sheet ID terdeteksi")
    
    st.markdown("<br>", unsafe_allow_html=True)
    
    load_btn = st.button("📥 Load Data")
    
    st.markdown("---")
    
    st.markdown("""
        <div style="padding: 1rem; background: #f1f5f9; border-radius: 8px; margin-top: 2rem;">
            <p style="margin: 0; font-size: 0.85rem; color: #475569;">
                <strong>ℹ️ Informasi</strong><br>
                • Dashboard otomatis refresh setiap 5 menit<br>
                • Data diambil dari sheet pertama<br>
                • Gunakan filter untuk analisis detail
            </p>
        </div>
    """, unsafe_allow_html=True)

# ======================================================
# MAIN LOGIC
# ======================================================
if not sheet_url:
    st.markdown("""
        <div style="text-align: center; padding: 4rem 2rem;">
            <h2 style="color: #64748b;">👈 Mulai dengan memasukkan URL Google Spreadsheet</h2>
            <p style="color: #94a3b8; margin-top: 1rem;">Masukkan link di sidebar untuk memulai monitoring</p>
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
            df, error = load_data(sheet_id)
            
            if error:
                st.error(f"❌ Gagal memuat data: {error}")
                st.stop()
            
            if df is None or df.empty:
                st.error("❌ Data kosong atau tidak dapat diakses")
                st.stop()
            
            st.session_state['df'] = df
            st.success(f"✅ Berhasil memuat {len(df)} baris data")
    
    df = st.session_state['df']
    
    # ======================================================
    # VALIDATE COLUMNS
    # ======================================================
    required_columns = [
        "Trans. ID", "Nama", "Jenjang", "Kabupaten", 
        "Propinsi", "Status", "Instalasi", "Selesai", 
        "Keterangan", "Petugas"
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
    st.markdown('<p class="section-header">📈 Ringkasan Status</p>', unsafe_allow_html=True)
    
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
    st.markdown('<p class="section-header">📊 Visualisasi Data</p>', unsafe_allow_html=True)
    
    col_chart1, col_chart2 = st.columns(2)
    
    with col_chart1:
        # Status Distribution Pie Chart
        status_counts = df['Status_Category'].value_counts()
        fig_pie = go.Figure(data=[go.Pie(
            labels=status_counts.index,
            values=status_counts.values,
            hole=0.4,
            marker=dict(colors=[get_status_color(s) for s in status_counts.index]),
            textinfo='label+percent',
            textfont=dict(size=12, color='white', family='Inter')
        )])
        fig_pie.update_layout(
            title="Distribusi Status",
            height=350,
            margin=dict(l=20, r=20, t=40, b=20),
            paper_bgcolor='white',
            font=dict(family='Inter')
        )
        st.plotly_chart(fig_pie, use_container_width=True)
    
    with col_chart2:
        # Top 10 Kabupaten
        top_kabupaten = df['Kabupaten'].value_counts().head(10)
        fig_bar = go.Figure(data=[go.Bar(
            x=top_kabupaten.values,
            y=top_kabupaten.index,
            orientation='h',
            marker=dict(color='#667eea')
        )])
        fig_bar.update_layout(
            title="Top 10 Kabupaten",
            height=350,
            margin=dict(l=20, r=20, t=40, b=20),
            xaxis_title="Jumlah",
            yaxis_title="",
            paper_bgcolor='white',
            font=dict(family='Inter')
        )
        st.plotly_chart(fig_bar, use_container_width=True)
    
    # ======================================================
    # FILTERS
    # ======================================================
    st.markdown('<p class="section-header">🔎 Filter & Pencarian</p>', unsafe_allow_html=True)
    
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
    st.markdown(f'<p class="section-header">📋 Detail Data ({len(filtered_df):,} dari {total:,} records)</p>', unsafe_allow_html=True)
    
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
        <div style="text-align: center; color: #94a3b8; padding: 1rem;">
            <p style="margin: 0;">🚀 Dashboard Monitoring v3.0 • Powered by Streamlit</p>
        </div>
    """, unsafe_allow_html=True)
