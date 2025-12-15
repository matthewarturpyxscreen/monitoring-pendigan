import streamlit as st
import pandas as pd
import re
import requests
from bs4 import BeautifulSoup

# ======================================================
# CONFIG
# ======================================================
st.set_page_config(
    page_title="Dashboard Monitoring Pekerjaan",
    layout="wide",
    initial_sidebar_state="expanded"
)

REFRESH_INTERVAL = 300  # 5 menit

# Custom CSS untuk design modern
st.markdown("""
    <style>
    /* Main container */
    .main {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 2rem;
    }
    
    /* Title styling */
    h1 {
        color: white !important;
        text-shadow: 2px 2px 4px rgba(0,0,0,0.2);
        font-weight: 700 !important;
    }
    
    h2, h3 {
        color: white !important;
    }
    
    /* Dataframe styling */
    .stDataFrame {
        background: white;
        border-radius: 12px;
        padding: 1rem;
        box-shadow: 0 4px 6px rgba(0,0,0,0.1);
    }
    
    /* Button styling */
    .stButton>button {
        background: linear-gradient(90deg, #667eea 0%, #764ba2 100%);
        color: white;
        border: none;
        border-radius: 8px;
        padding: 0.5rem 2rem;
        font-weight: 600;
        transition: all 0.3s;
    }
    
    .stButton>button:hover {
        transform: scale(1.05);
        box-shadow: 0 4px 12px rgba(0,0,0,0.2);
    }
    
    /* Metric styling */
    [data-testid="stMetricValue"] {
        font-size: 2rem !important;
        font-weight: 700 !important;
    }
    
    /* Sidebar */
    [data-testid="stSidebar"] {
        background: linear-gradient(180deg, #667eea 0%, #764ba2 100%);
    }
    
    [data-testid="stSidebar"] label {
        color: white !important;
        font-weight: 500 !important;
    }
    
    [data-testid="stSidebar"] .stTextInput input {
        background: white;
        border-radius: 8px;
    }
    
    /* Info boxes */
    .stAlert {
        border-radius: 8px;
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
st.markdown("### *Real-time Monitoring System*")

# ======================================================
# UTILITY FUNCTIONS
# ======================================================
def extract_sheet_id(url):
    """Extract sheet ID from Google Spreadsheet URL"""
    match = re.search(r"/spreadsheets/d/([a-zA-Z0-9-_]+)", url)
    return match.group(1) if match else None

def get_sheet_names_and_gids(sheet_id):
    """
    Scrape sheet names and GIDs from Google Spreadsheet
    Returns: list of tuples [(sheet_name, gid), ...]
    """
    try:
        url = f"https://docs.google.com/spreadsheets/d/{sheet_id}/edit"
        response = requests.get(url, timeout=10)
        
        if response.status_code != 200:
            return []
        
        # Parse GIDs dan nama sheet dari HTML
        html = response.text
        
        # Method 1: Cari di JavaScript data
        gid_pattern = r'"gid":"(\d+)"'
        name_pattern = r'"name":"([^"]+)"'
        
        gids = re.findall(gid_pattern, html)
        names = re.findall(name_pattern, html)
        
        # Filter dan combine
        sheets = []
        seen_gids = set()
        
        for gid, name in zip(gids, names):
            if gid not in seen_gids and not name.startswith('_'):
                sheets.append((name, gid))
                seen_gids.add(gid)
        
        return sheets[:20]  # Limit 20 sheets
        
    except Exception as e:
        st.error(f"Error fetching sheet list: {str(e)}")
        return []

def convert_to_csv_url(sheet_id, gid="0"):
    """Convert to CSV export URL"""
    return f"https://docs.google.com/spreadsheets/d/{sheet_id}/export?format=csv&gid={gid}"

@st.cache_data(ttl=REFRESH_INTERVAL)
def load_sheet(sheet_id, gid, sheet_name):
    """Load data from a specific sheet"""
    csv_url = convert_to_csv_url(sheet_id, gid)
    df = pd.read_csv(csv_url)
    df['_source_sheet'] = sheet_name
    return df

# ======================================================
# SIDEBAR - INPUT & SETTINGS
# ======================================================
with st.sidebar:
    st.markdown("## ⚙️ Pengaturan")
    st.markdown("---")
    
    st.markdown("### 🔗 Link Google Spreadsheet")
    sheet_url = st.text_input(
        "Masukkan link spreadsheet",
        placeholder="https://docs.google.com/spreadsheets/d/xxxxx/edit",
        help="Link utama spreadsheet (bukan link sheet tertentu)",
        label_visibility="collapsed"
    )
    
    sheet_id = extract_sheet_id(sheet_url) if sheet_url else None
    
    # Auto-detect sheets jika ada sheet_id
    available_sheets = []
    if sheet_id:
        with st.spinner("🔍 Mencari daftar sheet..."):
            available_sheets = get_sheet_names_and_gids(sheet_id)
        
        if available_sheets:
            st.success(f"✅ Ditemukan {len(available_sheets)} sheet")
            
            st.markdown("---")
            st.markdown("### 📑 Pilih Sheet yang Ingin Diload")
            
            # Multiselect untuk pilih sheets
            selected_sheet_names = st.multiselect(
                "Pilih sheet",
                options=[name for name, gid in available_sheets],
                default=[name for name, gid in available_sheets][:3],  # Default 3 pertama
                help="Pilih satu atau lebih sheet untuk dimuat",
                label_visibility="collapsed"
            )
            
            # Get GIDs untuk selected sheets
            selected_sheets = [
                (name, gid) for name, gid in available_sheets 
                if name in selected_sheet_names
            ]
        else:
            st.warning("⚠️ Tidak dapat mendeteksi sheet otomatis")
            st.markdown("---")
            st.markdown("### 📝 Input Manual")
            st.caption("Masukkan GID sheet secara manual")
            
            manual_gids = st.text_area(
                "GID (satu per baris)",
                placeholder="0\n123456\n789012",
                help="Buka tab sheet, lihat gid= di URL"
            )
            
            if manual_gids:
                gid_list = [g.strip() for g in manual_gids.split('\n') if g.strip()]
                selected_sheets = [(f"Sheet-{g}", g) for g in gid_list]
            else:
                selected_sheets = []
    else:
        selected_sheets = []
    
    st.markdown("---")
    load_btn = st.button("📥 Load Data", use_container_width=True, disabled=not selected_sheets)
    
    if selected_sheets:
        st.caption(f"📊 {len(selected_sheets)} sheet akan dimuat")
    
    st.markdown("---")
    st.caption("⏱️ Auto refresh: 5 menit")
    st.caption("💡 **Tips:**")
    st.caption("1. Paste link spreadsheet")
    st.caption("2. Pilih sheet yang diinginkan")
    st.caption("3. Klik Load Data")

# ======================================================
# MAIN LOGIC
# ======================================================
if not sheet_url:
    st.info("👈 Silakan masukkan link Google Spreadsheet di sidebar")
    st.stop()

if not selected_sheets:
    st.warning("👈 Pilih minimal 1 sheet di sidebar")
    st.stop()

if not load_btn and 'df_combined' not in st.session_state:
    st.warning("👈 Klik **Load Data** di sidebar untuk memulai")
    st.stop()

if load_btn or 'df_combined' in st.session_state:
    if load_btn:
        all_dfs = []
        errors = []
        
        # Progress container
        progress_bar = st.progress(0)
        status_text = st.empty()
        
        for idx, (sheet_name, gid) in enumerate(selected_sheets):
            try:
                status_text.text(f"⏳ Loading: {sheet_name}...")
                df = load_sheet(sheet_id, gid, sheet_name)
                all_dfs.append(df)
                status_text.text(f"✅ {sheet_name} berhasil dimuat ({len(df)} baris)")
            except Exception as e:
                errors.append(f"❌ {sheet_name}: {str(e)}")
                status_text.text(f"❌ {sheet_name} gagal")
            
            progress_bar.progress((idx + 1) / len(selected_sheets))
        
        progress_bar.empty()
        status_text.empty()
        
        if errors:
            with st.expander("⚠️ Beberapa sheet gagal dimuat"):
                for error in errors:
                    st.caption(error)
        
        if all_dfs:
            df_combined = pd.concat(all_dfs, ignore_index=True)
            st.session_state['df_combined'] = df_combined
            st.success(f"✅ **{len(all_dfs)} sheet berhasil dimuat** • Total {len(df_combined):,} baris")
        else:
            st.error("❌ Tidak ada data yang berhasil dimuat")
            st.caption("Pastikan spreadsheet diatur ke 'Anyone with the link can view'")
            st.stop()
    
    df = st.session_state['df_combined']
    
    # ======================================================
    # FIELD VALIDATION
    # ======================================================
    required_columns = [
        "Trans. ID", "Nama", "Jenjang", "Kabupaten", 
        "Propinsi", "Status", "Instalasi", "Selesai", 
        "Keterangan", "Petugas"
    ]
    
    # Cek kolom yang hilang
    missing_cols = [c for c in required_columns if c not in df.columns]
    
    if missing_cols:
        st.error(f"❌ Kolom tidak ditemukan: {', '.join(missing_cols)}")
        with st.expander("🔍 Lihat kolom yang tersedia"):
            st.write(df.columns.tolist())
        st.stop()
    
    # ======================================================
    # STATUS CALCULATION
    # ======================================================
    def categorize_status(val):
        val = str(val).upper()
        if "BAPP" in val or "KURANG" in val:
            return "Kurang BAPP"
        elif "PROSES" in val or "INSTALASI" in val:
            return "Sedang Diproses"
        elif "SELESAI" in val:
            return "Selesai"
        else:
            return "Belum Dikerjakan"
    
    df['Status_Category'] = df['Status'].apply(categorize_status)
    
    # ======================================================
    # METRICS CARDS
    # ======================================================
    st.markdown("## 📈 Ringkasan Status")
    
    col1, col2, col3, col4 = st.columns(4)
    
    total = len(df)
    
    with col1:
        belum = (df['Status_Category'] == 'Belum Dikerjakan').sum()
        pct = f"{belum/total*100:.1f}%" if total > 0 else "0%"
        st.metric(
            label="⚪ Belum Dikerjakan",
            value=f"{belum:,}",
            delta=pct
        )
    
    with col2:
        kurang = (df['Status_Category'] == 'Kurang BAPP').sum()
        pct = f"{kurang/total*100:.1f}%" if total > 0 else "0%"
        st.metric(
            label="🔵 Kurang BAPP",
            value=f"{kurang:,}",
            delta=pct
        )
    
    with col3:
        proses = (df['Status_Category'] == 'Sedang Diproses').sum()
        pct = f"{proses/total*100:.1f}%" if total > 0 else "0%"
        st.metric(
            label="🟡 Sedang Diproses",
            value=f"{proses:,}",
            delta=pct
        )
    
    with col4:
        selesai = (df['Status_Category'] == 'Selesai').sum()
        pct = f"{selesai/total*100:.1f}%" if total > 0 else "0%"
        st.metric(
            label="🟢 Selesai",
            value=f"{selesai:,}",
            delta=pct
        )
    
    # ======================================================
    # FILTER SECTION
    # ======================================================
    st.markdown("---")
    st.markdown("## 🔎 Filter Data")
    
    col_f1, col_f2, col_f3, col_f4 = st.columns(4)
    
    with col_f1:
        if '_source_sheet' in df.columns:
            sheet_options = sorted(df["_source_sheet"].dropna().unique())
            sheet_filter = st.multiselect(
                "📑 Sheet",
                sheet_options,
                default=sheet_options
            )
        else:
            sheet_filter = None
    
    with col_f2:
        provinsi_options = sorted(df["Propinsi"].dropna().unique())
        provinsi_filter = st.multiselect(
            "📍 Provinsi",
            provinsi_options,
            default=provinsi_options
        )
    
    with col_f3:
        jenjang_options = sorted(df["Jenjang"].dropna().unique())
        jenjang_filter = st.multiselect(
            "🎓 Jenjang",
            jenjang_options,
            default=jenjang_options
        )
    
    with col_f4:
        status_options = ['Belum Dikerjakan', 'Kurang BAPP', 'Sedang Diproses', 'Selesai']
        status_filter = st.multiselect(
            "📊 Status",
            status_options,
            default=status_options
        )
    
    # Apply filters
    filtered_df = df[
        (df["Propinsi"].isin(provinsi_filter)) &
        (df["Jenjang"].isin(jenjang_filter)) &
        (df["Status_Category"].isin(status_filter))
    ]
    
    if sheet_filter and '_source_sheet' in df.columns:
        filtered_df = filtered_df[filtered_df["_source_sheet"].isin(sheet_filter)]
    
    # ======================================================
    # DATA TABLE
    # ======================================================
    st.markdown("---")
    
    col_header1, col_header2 = st.columns([3, 1])
    
    with col_header1:
        st.markdown(f"## 📋 Detail Monitoring ({len(filtered_df):,} data)")
    
    with col_header2:
        csv = filtered_df.to_csv(index=False).encode('utf-8')
        st.download_button(
            label="📥 Download CSV",
            data=csv,
            file_name="monitoring_data.csv",
            mime="text/csv",
            use_container_width=True
        )
    
    # Status styling
    def status_style(val):
        val = str(val).upper()
        if "BAPP" in val or "KURANG" in val:
            return "background-color:#3b82f6;color:white;font-weight:600;padding:8px;border-radius:4px"
        elif "PROSES" in val or "INSTALASI" in val:
            return "background-color:#facc15;color:black;font-weight:600;padding:8px;border-radius:4px"
        elif "SELESAI" in val:
            return "background-color:#22c55e;color:white;font-weight:600;padding:8px;border-radius:4px"
        else:
            return "background-color:#e5e7eb;color:black;font-weight:600;padding:8px;border-radius:4px"
    
    # Display columns
    display_cols = required_columns.copy()
    if '_source_sheet' in filtered_df.columns:
        display_cols.insert(0, '_source_sheet')
    
    st.dataframe(
        filtered_df[display_cols].style.applymap(status_style, subset=["Status"]),
        use_container_width=True,
        height=500
    )
    
    # ======================================================
    # FOOTER
    # ======================================================
    st.markdown("---")
    st.caption("🚀 Powered by Streamlit | 📊 Dashboard Monitoring v2.0 | Made with ❤️")
